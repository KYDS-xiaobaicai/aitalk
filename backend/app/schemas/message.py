from pydantic import BaseModel, Field
from datetime import datetime
from app.models.message import MessageRole


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    role: MessageRole
    created_at: datetime
    
    class Config:
        from_attributes = True 