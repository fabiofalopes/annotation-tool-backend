from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """Base chat message structure from the original data"""
    user_id: str
    turn_id: str
    turn_text: str
    reply_to_turn: Optional[str] = None

class DisentangledTurn(ChatMessage):
    """Turn with disentanglement annotation data"""
    thread_id: Optional[str] = None
    annotator_id: Optional[str] = None  # Who performed the disentanglement
    annotation_timestamp: Optional[datetime] = None
    annotation_notes: Optional[str] = None  # Optional notes about thread assignment

class DisentanglementChatRoom(BaseModel):
    """Chat room container for disentanglement annotation"""
    room_id: str
    turns: list[DisentangledTurn] 