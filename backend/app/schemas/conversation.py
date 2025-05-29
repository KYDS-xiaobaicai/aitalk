from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from app.schemas.message import MessageResponse


class ConversationBase(BaseModel):
    title: str = Field(default="新对话", max_length=200)


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str = Field(..., max_length=200)


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = [] 