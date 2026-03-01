# load environment variables from .env if present (search parent dirs)
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .bot import bot
import uvicorn


app = FastAPI(title="SME Web UI API", version="1.0.0")


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request to send a message in a conversation"""
    user_id: str
    message: str
    session_id: Optional[str] = None  # if not provided, uses active conversation


class SetModeRequest(BaseModel):
    """Request to set conversation mode"""
    user_id: str
    mode: str


class SetDomainRequest(BaseModel):
    """Request to set conversation domain"""
    user_id: str
    domain: str


class CreateConversationRequest(BaseModel):
    """Request to create new conversation"""
    user_id: str
    title: Optional[str] = None


class SwitchConversationRequest(BaseModel):
    """Request to switch active conversation"""
    user_id: str
    session_id: str


class DeleteConversationRequest(BaseModel):
    """Request to delete a conversation"""
    user_id: str
    session_id: str


# ============================================================================
# Health & Metadata Endpoints
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "SME Web UI API"}


@app.get("/api/modes")
async def get_modes():
    """Get available conversation modes"""
    return bot.get_modes()


@app.get("/api/domains")
async def get_domains():
    """Get available knowledge domains"""
    return bot.get_domains()


# ============================================================================
# Conversation Management Endpoints
# ============================================================================

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Send a message to the bot
    
    - Creates new conversation if user doesn't have one
    - Maintains full conversation history
    - Auto-detects domain and applies current mode
    """
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")
    
    result = bot.process_message(req.user_id, req.message)
    return result


@app.post("/api/conversations/create")
async def create_conversation(req: CreateConversationRequest):
    """Create a new conversation for a user"""
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    
    result = bot.create_new_conversation(req.user_id, req.title or "")
    return result


@app.post("/api/conversations/switch")
async def switch_conversation(req: SwitchConversationRequest):
    """Switch user's active conversation"""
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.session_id or not req.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    
    result = bot.switch_conversation(req.user_id, req.session_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.post("/api/conversations/delete")
async def delete_conversation(req: DeleteConversationRequest):
    """Delete a conversation"""
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.session_id or not req.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    
    result = bot.delete_conversation(req.user_id, req.session_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/api/conversations")
async def get_all_conversations(user_id: str):
    """Get all conversations for a user"""
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    
    result = bot.get_all_conversations(user_id)
    return result


@app.get("/api/conversations/{session_id}")
async def get_conversation(session_id: str, user_id: str):
    """Get a specific conversation with full message history"""
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    
    result = bot.get_conversation_history(user_id, session_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# ============================================================================
# User Preferences Endpoints
# ============================================================================

@app.post("/api/mode/set")
async def set_mode(req: SetModeRequest):
    """Set conversation mode for a user"""
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.mode or not req.mode.strip():
        raise HTTPException(status_code=400, detail="mode is required")
    
    result = bot.set_mode(req.user_id, req.mode)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@app.post("/api/domain/set")
async def set_domain(req: SetDomainRequest):
    """Set conversation domain for a user"""
    if not req.user_id or not req.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required")
    if not req.domain or not req.domain.strip():
        raise HTTPException(status_code=400, detail="domain is required")
    
    result = bot.set_domain(req.user_id, req.domain)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# ============================================================================
# Legacy Endpoint (Deprecated - kept for backwards compatibility)
# ============================================================================

class GenerateRequest(BaseModel):
    """Legacy request format"""
    message: str
    domain: Optional[str] = None
    mode: Optional[str] = None


@app.post("/generate")
async def generate_legacy(req: GenerateRequest):
    """
    Legacy endpoint - use /api/chat instead
    
    This endpoint is maintained for backwards compatibility.
    Single-turn responses without conversation history.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")
    
    try:
        result = bot.process_message("legacy_user", req.message)
        
        # For legacy compatibility, just return reply
        return {"reply": result.get("response", result.get("error", "No response"))}
    except Exception as e:
        return {"reply": f"⚠️ Error: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

