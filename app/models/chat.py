from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    user_id: str
    turn_id: str
    turn_text: str
    reply_to_turn: Optional[str] = None

class AnnotatedMessage(Message):
    thread_id: Optional[str] = None
    modified_by: Optional[str] = None
    modified_at: Optional[datetime] = None
    details: Optional[str] = None

class ChatRoom(BaseModel):
    room_id: str
    messages: list[AnnotatedMessage] 