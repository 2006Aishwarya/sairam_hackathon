import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import (
    init_and_seed_db, get_db_connection, DB_PATH,
    get_all_chat_sessions, get_chat_session, save_chat_session,
    delete_chat_session, clear_all_chat_sessions
)
from tools.get_schema import get_schema
from tools.execute_query import execute_query
from agent import DatabaseAgent, ALL_TOOL_SPECS
from file_handler import process_uploaded_file

# Initialize database on backend start if missing
if not os.path.exists(DB_PATH):
    init_and_seed_db()

app = FastAPI(
    title="Advanced NVIDIA Nemotron Database Agent API",
    description="Conversational AI backend powered by NVIDIA Nemotron 3 Super 120B providing real-time streaming SSE, dynamic database schema discovery, read-only SQL execution, visual charts, ER/process diagrams, data insight synthesis, and spreadsheet file attachments.",
    version="2.0.0"
)

# Enable CORS for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = DatabaseAgent()

import asyncio
import time

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []
    db_path: Optional[str] = None
    api_key: Optional[str] = None
    attached_table: Optional[str] = None
    attached_file_name: Optional[str] = None
    request_id: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    max_rows: Optional[int] = 100
    db_path: Optional[str] = None

class SaveSessionRequest(BaseModel):
    session_id: str
    title: Optional[str] = "Untitled Session"
    messages: List[Dict[str, Any]]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Advanced NVIDIA Nemotron Database Agent API",
        "database": DB_PATH,
        "tools_count": len(ALL_TOOL_SPECS),
        "primary_model": os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")
    }

@app.get("/api/health")
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        tables_count = cursor.fetchone()[0]
        conn.close()
        return {
            "status": "healthy",
            "database_status": "connected",
            "tables_in_db": tables_count,
            "nvidia_configured": bool(os.environ.get("NVIDIA_API_KEY"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@app.post("/api/upload")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """
    Endpoint for users to attach Excel (.xlsx, .xls), CSV (.csv), or JSON (.json) data supporting files.
    Imports data into database tables for instant AI analysis, querying, and visualization.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file attached.")

    file_bytes = await file.read()
    res = process_uploaded_file(file_bytes, file.filename, DB_PATH)

    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))

    return res

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")
    
    response = agent.process_message(
        user_message=req.message,
        history=req.history,
        api_key=req.api_key,
        target_table=req.attached_table,
        attached_file_name=req.attached_file_name,
        request_id=req.request_id
    )
    return response

@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time backend stage progress updates.
    Runs sync generator in executor threadpool so concurrent requests do not block the event loop.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    request_id = req.request_id or f"req_{int(time.time() * 1000)}"

    async def event_generator():
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()

        def sync_stream_worker():
            try:
                for event in agent.process_message_stream(
                    user_message=req.message,
                    history=req.history,
                    api_key=req.api_key,
                    target_table=req.attached_table,
                    attached_file_name=req.attached_file_name,
                    request_id=request_id
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            except Exception as e:
                err_event = {
                    "request_id": request_id,
                    "event": "error",
                    "message": str(e)
                }
                loop.call_soon_threadsafe(queue.put_nowait, err_event)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        loop.run_in_executor(None, sync_stream_worker)

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/schema")
def schema_endpoint(table_name: Optional[str] = None):
    res = get_schema(table_name=table_name)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@app.post("/api/query")
def execute_query_endpoint(req: QueryRequest):
    res = execute_query(query=req.query, max_rows=req.max_rows, db_path=req.db_path)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@app.get("/api/tools")
def list_tools():
    return {
        "count": len(ALL_TOOL_SPECS),
        "tools": ALL_TOOL_SPECS
    }

@app.post("/api/seed")
def reseed_database():
    try:
        path = init_and_seed_db()
        return {
            "status": "success",
            "message": "Database successfully re-initialized and seeded with e-commerce sample data.",
            "path": path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed database: {str(e)}")

# ==============================================================================
# Chat History Management Endpoints
# ==============================================================================

@app.get("/api/history")
def list_history_sessions():
    """Returns all saved chat sessions sorted by last updated timestamp."""
    return {"sessions": get_all_chat_sessions()}

@app.get("/api/history/{session_id}")
def get_history_session(session_id: str):
    """Retrieve full message history for a specific chat session."""
    session = get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    return session

@app.post("/api/history")
def save_history_session(req: SaveSessionRequest):
    """Save or update a chat session with its full message history."""
    if not req.session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")
    return save_chat_session(req.session_id, req.title, req.messages)

@app.delete("/api/history/{session_id}")
def delete_history_session(session_id: str):
    """Delete a specific chat session."""
    return delete_chat_session(session_id)

@app.delete("/api/history")
def clear_all_history():
    """Clear all saved chat sessions."""
    return clear_all_chat_sessions()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
