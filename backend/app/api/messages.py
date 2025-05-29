from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import json
import asyncio
from app.database import get_db
from app.models.user import User
from app.models.message import Message, MessageRole
from app.schemas.message import MessageCreate, MessageResponse
from app.utils.dependencies import get_current_user
from app.services.conversation import ConversationService
from app.services.ai import AIService

router = APIRouter(prefix="/api/conversations/{conversation_id}/messages", tags=["消息交互"])


@router.get("", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=500, description="返回的记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取对话中的消息列表
    
    按时间顺序排列，支持分页
    """
    messages = ConversationService.get_conversation_messages(
        db, current_user, conversation_id, skip, limit
    )
    return messages


@router.post("", response_model=List[MessageResponse], status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息并获取AI回复
    
    - **content**: 消息内容
    
    返回用户消息和AI回复消息
    """
    user_message, ai_message = await ConversationService.send_message(
        db, current_user, conversation_id, message_data
    )
    return [user_message, ai_message]


@router.post("/stream", status_code=status.HTTP_200_OK)
async def send_message_stream(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息并获取AI流式回复
    
    - **content**: 消息内容
    
    返回服务器发送事件(SSE)流
    """
    try:
        # 验证对话所有权
        conversation = ConversationService.get_conversation(db, current_user, conversation_id)
        
        # 创建用户消息
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message_data.content
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # 获取对话历史（在用户消息保存之前）
        history = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        async def generate_stream():
            try:
                # 首先发送用户消息
                yield f"data: {json.dumps({'type': 'user_message', 'message': {'id': user_message.id, 'content': user_message.content, 'role': 'user'}}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # 强制刷新
                
                # 发送AI回复开始标记
                yield f"data: {json.dumps({'type': 'ai_start'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)  # 强制刷新
                
                # 收集AI回复内容
                ai_content = ""
                try:
                    async for chunk in AIService.get_ai_response_stream(message_data.content, history):
                        if chunk:  # 确保chunk不为空
                            ai_content += chunk
                            yield f"data: {json.dumps({'type': 'ai_chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0)  # 强制刷新，确保立即发送
                except Exception as ai_error:
                    error_msg = f"AI服务错误: {str(ai_error)}"
                    ai_content = error_msg
                    yield f"data: {json.dumps({'type': 'ai_chunk', 'content': error_msg}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0)  # 强制刷新
                
                # 保存AI回复消息
                try:
                    ai_message = Message(
                        conversation_id=conversation_id,
                        role=MessageRole.ASSISTANT,
                        content=ai_content or "抱歉，AI服务暂时不可用。"
                    )
                    db.add(ai_message)
                    
                    # 更新对话时间和标题
                    conversation.updated_at = func.now()
                    if len(history) == 1 and conversation.title == "新对话":  # history包含了刚添加的用户消息
                        conversation.title = message_data.content[:50] + ("..." if len(message_data.content) > 50 else "")
                    
                    db.commit()
                    db.refresh(ai_message)
                    
                    # 发送AI回复完成标记
                    yield f"data: {json.dumps({'type': 'ai_complete', 'message': {'id': ai_message.id, 'content': ai_content, 'role': 'assistant'}}, ensure_ascii=False)}\n\n"
                    
                except Exception as db_error:
                    yield f"data: {json.dumps({'type': 'error', 'message': f'数据库错误: {str(db_error)}'}, ensure_ascii=False)}\n\n"
                
                # 发送结束标记
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
            except Exception as stream_error:
                yield f"data: {json.dumps({'type': 'error', 'message': f'流式处理错误: {str(stream_error)}'}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
                "Content-Type": "text/event-stream; charset=utf-8",
            }
        )
        
    except Exception as e:
        # 如果在设置阶段出错，返回错误响应
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': f'服务器错误: {str(e)}'}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
                "Content-Type": "text/event-stream; charset=utf-8",
            }
        ) 