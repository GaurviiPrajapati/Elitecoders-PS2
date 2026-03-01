# conversation.py - Data models for web UI conversations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import json
import uuid


@dataclass
class Message:
    """Single message in conversation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = ""  # "user" or "assistant"
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)  # source URLs, citations, etc.
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data):
        return Message(**data)


@dataclass
class Conversation:
    """Complete conversation session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    current_domain: str = "general"
    current_mode: str = "TECHNICAL"
    title: str = ""  # optional conversation title
    archived: bool = False
    
    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add message to conversation"""
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        self.updated_at = datetime.utcnow().isoformat()
        return msg
    
    def get_messages_for_llm(self):
        """Format messages for LLM invocation"""
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in self.messages
        ]
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_domain": self.current_domain,
            "current_mode": self.current_mode,
            "title": self.title,
            "archived": self.archived
        }
    
    @staticmethod
    def from_dict(data):
        conv = Conversation(
            session_id=data.get("session_id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            current_domain=data.get("current_domain", "general"),
            current_mode=data.get("current_mode", "TECHNICAL"),
            title=data.get("title", ""),
            archived=data.get("archived", False)
        )
        conv.messages = [
            Message.from_dict(msg) for msg in data.get("messages", [])
        ]
        return conv


@dataclass
class UserSession:
    """User session metadata"""
    user_id: str = ""
    active_session_id: str = ""  # current conversation
    conversation_history: List[str] = field(default_factory=list)  # session IDs
    user_preferences: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data):
        return UserSession(**data)
