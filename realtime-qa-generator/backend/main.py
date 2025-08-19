import json
from typing import List

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Realtime QA Generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple connection manager
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                self.connections.remove(connection)

manager = ConnectionManager()

# Request/Response models
class TranscriptRequest(BaseModel):
    transcript: str
    session_id: str = "default"

# Routes
@app.get("/")
async def root():
    return {"message": "QA Generator Running"}

@app.post("/generate-questions")
async def generate_questions(request: TranscriptRequest):
    # Simple question generation based on transcript
    transcript_preview = request.transcript[:100] + "..." if len(request.transcript) > 100 else request.transcript
    
    questions = [
        f"What is the main concept in: '{transcript_preview}'?",
        "How would you explain this to someone else?", 
        "What questions does this raise for you?",
        "How might this apply in real situations?"
    ]
    
    return {"questions": questions, "transcript_length": len(request.transcript)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle real-time transcript chunks here
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)