from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import List
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.message import MessageCreate
from app.services.ai import AIService


class ConversationService:
    @staticmethod
    def create_conversation(
        db: Session,
        user: User,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """创建新对话"""
        db_conversation = Conversation(
            user_id=user.id,
            title=conversation_data.title
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    
    @staticmethod
    def get_user_conversations(
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 20
    ) -> List[Conversation]:
        """获取用户的对话列表"""
        conversations = db.query(
            Conversation,
            func.count(Message.id).label("message_count")
        ).outerjoin(
            Message
        ).filter(
            Conversation.user_id == user.id
        ).group_by(
            Conversation.id
        ).order_by(
            Conversation.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        # 添加消息计数到对话对象
        result = []
        for conv, msg_count in conversations:
            conv.message_count = msg_count
            result.append(conv)
        
        return result
    
    @staticmethod
    def get_conversation(
        db: Session,
        user: User,
        conversation_id: int
    ) -> Conversation:
        """获取特定对话"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在"
            )
        
        return conversation
    
    @staticmethod
    def update_conversation(
        db: Session,
        user: User,
        conversation_id: int,
        conversation_data: ConversationUpdate
    ) -> Conversation:
        """更新对话标题"""
        conversation = ConversationService.get_conversation(db, user, conversation_id)
        
        conversation.title = conversation_data.title
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def delete_conversation(
        db: Session,
        user: User,
        conversation_id: int
    ) -> None:
        """删除对话"""
        conversation = ConversationService.get_conversation(db, user, conversation_id)
        
        db.delete(conversation)
        db.commit()
    
    @staticmethod
    async def send_message(
        db: Session,
        user: User,
        conversation_id: int,
        message_data: MessageCreate
    ) -> tuple[Message, Message]:
        """发送消息并获取AI回复"""
        # 验证对话所有权
        conversation = ConversationService.get_conversation(db, user, conversation_id)
        
        # 创建用户消息
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message_data.content
        )
        db.add(user_message)
        
        # 获取对话历史
        history = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        
        # 调用AI服务获取回复
        ai_response = await AIService.get_ai_response(
            message_data.content,
            history
        )
        
        # 创建AI回复消息
        ai_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        db.add(ai_message)
        
        # 更新对话的更新时间
        conversation.updated_at = func.now()
        
        # 如果是第一条消息，使用用户输入作为对话标题
        if len(history) == 0 and conversation.title == "新对话":
            # 截取前50个字符作为标题
            conversation.title = message_data.content[:50] + ("..." if len(message_data.content) > 50 else "")
        
        db.commit()
        db.refresh(user_message)
        db.refresh(ai_message)
        
        return user_message, ai_message
    
    @staticmethod
    def get_conversation_messages(
        db: Session,
        user: User,
        conversation_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """获取对话中的消息"""
        # 验证对话所有权
        conversation = ConversationService.get_conversation(db, user, conversation_id)
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at
        ).offset(skip).limit(limit).all()
        
        return messages 