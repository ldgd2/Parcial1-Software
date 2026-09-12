import asyncio
from typing import Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # sala_id -> { "host": WebSocket, "guests": { guest_id: WebSocket }, "pending_guests": { guest_id: info } }
        self.salas: Dict[str, Dict[str, Any]] = {}

    def _init_sala(self, sala_id: str):
        if sala_id not in self.salas:
            self.salas[sala_id] = {
                "host": None,
                "guests": {},
                "pending_guests": {},
                "approved_guests": set(),
                "readonly_guests": set(), # Set of guest_ids that can only view
                "guest_nicknames": {}, # Store mapping of guest_id -> nickname for active users
                "locked_elements": {} # element_id -> username
            }

    async def connect_host(self, websocket: WebSocket, sala_id: str):
        await websocket.accept()
        self._init_sala(sala_id)
        self.salas[sala_id]["host"] = websocket

    async def connect_guest(self, websocket: WebSocket, sala_id: str, guest_id: str, nickname: str = None):
        await websocket.accept()
        self._init_sala(sala_id)
        self.salas[sala_id]["guests"][guest_id] = websocket
        if nickname:
            self.salas[sala_id]["guest_nicknames"][guest_id] = nickname

    def add_pending_guest(self, sala_id: str, guest_id: str, nickname: str):
        self._init_sala(sala_id)
        self.salas[sala_id]["pending_guests"][guest_id] = nickname

    def remove_pending_guest(self, sala_id: str, guest_id: str):
        if sala_id in self.salas:
            if guest_id in self.salas[sala_id]["pending_guests"]:
                del self.salas[sala_id]["pending_guests"][guest_id]

    def disconnect(self, websocket: WebSocket, sala_id: str):
        if sala_id in self.salas:
            sala = self.salas[sala_id]
            if sala["host"] == websocket:
                sala["host"] = None
            else:
                for guest_id, ws in list(sala["guests"].items()):
                    if ws == websocket:
                        del sala["guests"][guest_id]
                        # Don't delete from guest_nicknames to remember them if they reconnect
                        break

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def broadcast_to_sala(self, message: dict, sala_id: str, exclude: WebSocket = None):
        if sala_id in self.salas:
            sala = self.salas[sala_id]
            tasks = []
            
            # Send to host
            if sala["host"] and sala["host"] != exclude:
                tasks.append(self.send_personal_message(message, sala["host"]))
            
            # Send to guests
            for ws in sala["guests"].values():
                if ws != exclude:
                    tasks.append(self.send_personal_message(message, ws))
                    
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def notify_host(self, sala_id: str, message: dict):
        if sala_id in self.salas and self.salas[sala_id]["host"]:
            await self.send_personal_message(message, self.salas[sala_id]["host"])
            
    async def kick_user(self, sala_id: str, guest_id: str):
        if sala_id in self.salas:
            sala = self.salas[sala_id]
            if guest_id in sala["guests"]:
                ws = sala["guests"][guest_id]
                await self.send_personal_message({"type": "kicked"}, ws)
                await ws.close()
                del sala["guests"][guest_id]
            sala["approved_guests"].discard(guest_id)
            sala["readonly_guests"].discard(guest_id)
            if guest_id in sala["pending_guests"]:
                del sala["pending_guests"][guest_id]

manager = ConnectionManager()
