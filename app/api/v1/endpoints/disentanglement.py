from fastapi import APIRouter, HTTPException
from typing import Optional, Literal
import csv
from datetime import datetime

from app.models.disentanglement import DisentangledTurn, DisentanglementChatRoom
from app.services.disentanglement import DisentanglementService

router = APIRouter()
service = DisentanglementService()

@router.post("/chatroom/import")
async def import_chatroom_for_disentanglement(file_path: str):
    """Import chat data for disentanglement annotation"""
    try:
        return await service.import_chatroom(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/chatroom/{room_id}", response_model=DisentanglementChatRoom)
async def get_disentanglement_chatroom(room_id: str):
    """Get a chat room with its disentanglement annotations"""
    return await service.get_chatroom(room_id)

@router.put("/chatroom/{room_id}/turns/{turn_id}/annotate")
async def annotate_turn(
    room_id: str,
    turn_id: str,
    annotation_data: dict,
    annotator_id: str,
    notes: Optional[str] = None
):
    """Annotate a turn with thread information"""
    return await service.annotate_turn(
        room_id, turn_id, 
        thread_id=annotation_data.get("thread_id"),
        annotator_id=annotator_id,
        annotation_notes=notes
    )

@router.get("/chatroom/{room_id}/threads")
async def get_thread_summary(room_id: str):
    """Get a summary of thread assignments in a chat room"""
    return await service.get_thread_summary(room_id)

@router.post("/chatroom/import/{format}")
async def import_chatroom(
    file_path: str,
    format: Literal["csv", "json"] = "csv"
):
    """Import chat data from CSV or JSON"""
    try:
        return await service.import_chatroom(file_path, format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/chatroom/{room_id}/export/{format}")
async def export_chatroom(
    room_id: str,
    format: Literal["csv", "json"] = "csv",
    output_path: Optional[str] = None
):
    """Export chat room data to CSV or JSON"""
    try:
        path = await service.export_chatroom(room_id, format, output_path)
        return {"message": f"Successfully exported to {path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/chatrooms")
async def list_chatrooms():
    """Get a list of all available chat rooms"""
    return await service.list_chatrooms()

@router.delete("/chatroom/{room_id}")
async def delete_chatroom(room_id: str):
    """Delete a chat room and its data"""
    return await service.delete_chatroom(room_id) 