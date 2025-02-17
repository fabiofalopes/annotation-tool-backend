import json
import os
import csv
from pathlib import Path
from fastapi import HTTPException
from datetime import datetime
from typing import Optional, Literal

from app.models.disentanglement import DisentangledTurn, DisentanglementChatRoom

class DisentanglementService:
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = Path("data/chatrooms")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing rooms from disk
        self.disentanglement_rooms: dict[str, DisentanglementChatRoom] = self._load_rooms()

    def _load_rooms(self) -> dict[str, DisentanglementChatRoom]:
        """Load all chat rooms from disk"""
        rooms = {}
        for file in self.data_dir.glob("*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                room = DisentanglementChatRoom.parse_obj(data)
                rooms[room.room_id] = room
        return rooms

    def _save_room(self, room: DisentanglementChatRoom):
        """Save a chat room to disk"""
        file_path = self.data_dir / f"{room.room_id}.json"
        with open(file_path, 'w') as f:
            json.dump(room.dict(), f, default=str)

    async def import_chatroom(self, file_path: str, format: Literal["csv", "json"] = "csv"):
        """Import chat data from CSV or JSON, preserving existing thread annotations"""
        turns = []
        
        if format == "csv":
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames
                
                # Look for thread column with various possible names
                thread_column = None
                thread_column_variants = ['thread_id', 'thread', 'thread_num', 'thread_number']
                for variant in thread_column_variants:
                    if variant in headers:
                        thread_column = variant
                        break
                
                for row in reader:
                    # Extract existing thread_id if available
                    existing_thread = None
                    if thread_column and row.get(thread_column):
                        existing_thread = str(row[thread_column]).strip()
                        # Handle empty strings or "None" values
                        if existing_thread.lower() in ('', 'none', 'null'):
                            existing_thread = None
                    
                    turn = DisentangledTurn(
                        user_id=row['user_id'],
                        turn_id=row['turn_id'],
                        turn_text=row['turn_text'],
                        reply_to_turn=row.get('reply_to_turn'),
                        thread_id=existing_thread,
                        # If there's a thread_id, we can assume it was previously annotated
                        annotator_id='imported' if existing_thread else None,
                        annotation_timestamp=datetime.now() if existing_thread else None,
                        annotation_notes=f"Imported from {file_path}" if existing_thread else None
                    )
                    turns.append(turn)
        else:  # json
            with open(file_path, 'r') as file:
                data = json.load(file)
                for turn_data in data['turns']:
                    # For JSON, we can directly use the thread_id if it exists
                    turn = DisentangledTurn.parse_obj(turn_data)
                    # Set annotation metadata if thread_id exists
                    if turn.thread_id:
                        turn.annotator_id = turn.annotator_id or 'imported'
                        turn.annotation_timestamp = turn.annotation_timestamp or datetime.now()
                        turn.annotation_notes = turn.annotation_notes or f"Imported from {file_path}"
                    turns.append(turn)

        room_id = Path(file_path).stem
        chat_room = DisentanglementChatRoom(room_id=room_id, turns=turns)
        self.disentanglement_rooms[room_id] = chat_room
        self._save_room(chat_room)
        
        return {
            "message": f"Successfully imported chat room {room_id}",
            "total_turns": len(turns),
            "pre_annotated_turns": sum(1 for turn in turns if turn.thread_id is not None)
        }

    async def export_chatroom(
        self, 
        room_id: str, 
        format: Literal["csv", "json"] = "csv",
        output_path: Optional[str] = None
    ) -> str:
        """Export chat room data to CSV or JSON"""
        if room_id not in self.disentanglement_rooms:
            raise HTTPException(status_code=404, detail="Chat room not found")

        chat_room = self.disentanglement_rooms[room_id]
        
        if output_path is None:
            output_path = self.data_dir / f"export_{room_id}.{format}"
        
        if format == "csv":
            with open(output_path, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'user_id', 'turn_id', 'turn_text', 'reply_to_turn',
                    'thread_id', 'annotator_id', 
                    'annotation_timestamp', 'annotation_notes'
                ])
                writer.writeheader()
                for turn in chat_room.turns:
                    writer.writerow(turn.dict())
        else:  # json
            with open(output_path, 'w') as file:
                json.dump(chat_room.dict(), file, default=str, indent=2)

        return str(output_path)

    async def get_chatroom(self, room_id: str):
        if room_id not in self.disentanglement_rooms:
            raise HTTPException(status_code=404, detail="Chat room not found")
        return self.disentanglement_rooms[room_id]

    async def annotate_turn(
        self,
        room_id: str,
        turn_id: str,
        annotator_id: str,
        thread_id: Optional[str] = None,
        annotation_notes: Optional[str] = None
    ):
        """Annotate a turn with thread information"""
        if room_id not in self.disentanglement_rooms:
            raise HTTPException(status_code=404, detail="Chat room not found")
        
        chat_room = self.disentanglement_rooms[room_id]
        for turn in chat_room.turns:
            if turn.turn_id == turn_id:
                turn.thread_id = thread_id
                turn.annotator_id = annotator_id
                turn.annotation_timestamp = datetime.now()
                turn.annotation_notes = annotation_notes
                # Save changes to disk
                self._save_room(chat_room)
                return {
                    "message": f"Turn {turn_id} annotated",
                    "annotation_timestamp": turn.annotation_timestamp
                }
        
        raise HTTPException(status_code=404, detail="Turn not found")
    
    async def get_thread_summary(self, room_id: str):
        if room_id not in self.disentanglement_rooms:
            raise HTTPException(status_code=404, detail="Chat room not found")
        
        chat_room = self.disentanglement_rooms[room_id]
        threads = {}
        for turn in chat_room.turns:
            if turn.thread_id:
                if turn.thread_id not in threads:
                    threads[turn.thread_id] = []
                threads[turn.thread_id].append(turn.turn_id)
        
        return {
            "room_id": room_id,
            "thread_count": len(threads),
            "threads": threads
        }

    async def list_chatrooms(self):
        """Get a list of all available chat rooms with basic metadata"""
        rooms_summary = []
        for room_id, room in self.disentanglement_rooms.items():
            rooms_summary.append({
                "room_id": room_id,
                "turn_count": len(room.turns),
                "annotated_turns": sum(1 for turn in room.turns if turn.thread_id is not None),
                "thread_count": len(set(turn.thread_id for turn in room.turns if turn.thread_id is not None))
            })
        return rooms_summary

    async def delete_chatroom(self, room_id: str):
        """Delete a chat room and its data"""
        if room_id not in self.disentanglement_rooms:
            raise HTTPException(status_code=404, detail="Chat room not found")
        
        # Remove from memory
        del self.disentanglement_rooms[room_id]
        
        # Remove from disk
        file_path = self.data_dir / f"{room_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        return {"message": f"Chat room {room_id} deleted successfully"} 