# FastAPI-based REST service for the chatbot system.
# This file exposes prediction endpoints and mock APIs
# intended for integration with a frontend dashboard.

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from chatbot.chatbot_core import ChatBot  # Main chatbot class

# Initialize chatbot with the trained model
chatbot = ChatBot(model_path="models/chatbot.pt")

app = FastAPI(title="Operations Dashboard API")

# Enable CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can be restricted to specific domains for security
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------- Request / Response Models ----------
class ChatRequest(BaseModel):
    text: str

class ChatResponse(BaseModel):
    intent: str
    sentiment: str
    entities: dict
    intent_prob: List[float]
    sent_prob: List[float]
    response_text: Optional[str] = None

# ---------- ChatBot Endpoint ----------
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Validate non-empty input
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty text provided")
    
    # Run chatbot prediction
    result = chatbot.predict(request.text)
    
    return ChatResponse(
        intent=result['intent'],
        sentiment=result['sentiment'],
        entities=result.get('entities', {}),
        intent_prob=result.get('intent_prob', []),
        sent_prob=result.get('sent_prob', []),
        response_text=result.get('response', None)
    )

# ---------- Mock / Placeholder Endpoints ----------
@app.get("/api/tasks")
async def get_tasks():
    # Return mock task management data
    return {
        "total_tasks": 16,
        "completed_tasks": 10,
        "overdue_tasks": 2,
        "tasks": [
            {"id": 1, "title": "Task 1", "team_name": "Team A", "status": "completed", "due_date": "2026-01-25"},
            {"id": 2, "title": "Task 2", "team_name": "Team B", "status": "pending", "due_date": "2026-01-27"},
        ]
    }

@app.get("/api/teams")
async def get_teams():
    # Return mock team information
    return [
        {"id": 1, "name": "Team A", "members": ["Alice", "Bob"]},
        {"id": 2, "name": "Team B", "members": ["Charlie", "David"]},
    ]

@app.get("/api/meetings")
async def get_meetings():
    # Return mock meeting schedule data
    return [
        {"id": 1, "title": "Weekly Sync", "scheduled_date": "2026-01-24T10:00:00", "status": "scheduled"},
        {"id": 2, "title": "Project Kickoff", "scheduled_date": "2026-01-25T14:00:00", "status": "pending"},
    ]

@app.get("/api/notifications")
async def get_notifications():
    # Return mock notification data
    return [
        {"id": 1, "title": "System Update", "message": "Server will restart at midnight", "notification_type": "system"},
        {"id": 2, "title": "New Task Assigned", "message": "You have been assigned a new task", "notification_type": "task"},
    ]

# ---------- Application Entry Point ----------
if name == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
