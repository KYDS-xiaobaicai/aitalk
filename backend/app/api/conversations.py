from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse
from app.utils.dependencies import get_current_user
from app.services.conversation import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["对话管理"])


@router.get("", response_model=List[ConversationResponse])
def get_conversations(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的对话列表
    
    支持分页，按更新时间倒序排列
    """
    conversations = ConversationService.get_user_conversations(
        db, current_user, skip, limit
    )
    return conversations


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新对话
    
    - **title**: 对话标题（可选，默认为"新对话"）
    """
    conversation = ConversationService.create_conversation(
        db, current_user, conversation_data
    )
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取特定对话的详情
    """
    conversation = ConversationService.get_conversation(
        db, current_user, conversation_id
    )
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新对话标题
    
    - **title**: 新的对话标题
    """
    conversation = ConversationService.update_conversation(
        db, current_user, conversation_id, conversation_data
    )
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除对话
    
    删除对话会同时删除对话中的所有消息
    """
    ConversationService.delete_conversation(
        db, current_user, conversation_id
    )
    return None 