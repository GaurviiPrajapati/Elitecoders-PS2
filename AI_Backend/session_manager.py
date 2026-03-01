# session_manager.py - Web UI session and conversation management

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
import uuid
from .conversation import Conversation, UserSession, Message


class SessionManager:
    """Manages user sessions, conversations, and history for web UI"""
    
    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = storage_dir
        self.conversations: Dict[str, Conversation] = {}
        self.user_sessions: Dict[str, UserSession] = {}
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing conversations and sessions from disk
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load conversations from storage directory"""
        try:
            # Load conversations
            conv_dir = os.path.join(self.storage_dir, "conversations")
            if os.path.exists(conv_dir):
                for filename in os.listdir(conv_dir):
                    if filename.endswith(".json"):
                        try:
                            with open(os.path.join(conv_dir, filename), "r") as f:
                                data = json.load(f)
                                conv = Conversation.from_dict(data)
                                self.conversations[conv.session_id] = conv
                        except Exception as e:
                            print(f"Error loading conversation {filename}: {e}")
            
            # Load user sessions
            sessions_file = os.path.join(self.storage_dir, "user_sessions.json")
            if os.path.exists(sessions_file):
                try:
                    with open(sessions_file, "r") as f:
                        data = json.load(f)
                        for user_id, session_data in data.items():
                            self.user_sessions[user_id] = UserSession.from_dict(session_data)
                except Exception as e:
                    print(f"Error loading user sessions: {e}")
        except Exception as e:
            print(f"Error during disk load: {e}")
    
    def _save_conversation_to_disk(self, conversation: Conversation):
        """Save single conversation to disk"""
        try:
            conv_dir = os.path.join(self.storage_dir, "conversations")
            os.makedirs(conv_dir, exist_ok=True)
            
            filepath = os.path.join(conv_dir, f"{conversation.session_id}.json")
            with open(filepath, "w") as f:
                json.dump(conversation.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    def _save_user_sessions_to_disk(self):
        """Save all user sessions metadata to disk"""
        try:
            sessions_file = os.path.join(self.storage_dir, "user_sessions.json")
            data = {user_id: session.to_dict() 
                   for user_id, session in self.user_sessions.items()}
            with open(sessions_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving user sessions: {e}")
    
    def create_conversation(self, user_id: str, title: str = "") -> Conversation:
        """Create new conversation for user"""
        conv = Conversation(
            user_id=user_id,
            title=title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        )
        self.conversations[conv.session_id] = conv
        
        # Track in user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id=user_id)
        
        self.user_sessions[user_id].active_session_id = conv.session_id
        self.user_sessions[user_id].conversation_history.append(conv.session_id)
        
        self._save_conversation_to_disk(conv)
        self._save_user_sessions_to_disk()
        
        return conv
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID"""
        return self.conversations.get(session_id)
    
    def get_active_conversation(self, user_id: str) -> Optional[Conversation]:
        """Get user's active conversation"""
        if user_id not in self.user_sessions:
            return None
        
        session_id = self.user_sessions[user_id].active_session_id
        if not session_id:
            return None
        
        return self.conversations.get(session_id)
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user"""
        if user_id not in self.user_sessions:
            return []
        
        session_ids = self.user_sessions[user_id].conversation_history
        return [
            self.conversations[sid] 
            for sid in session_ids 
            if sid in self.conversations
        ]
    
    def add_message_to_conversation(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: dict = None
    ) -> Optional[Message]:
        """Add message to a conversation"""
        if session_id not in self.conversations:
            return None
        
        conv = self.conversations[session_id]
        msg = conv.add_message(role, content, metadata or {})
        
        self._save_conversation_to_disk(conv)
        return msg
    
    def set_user_mode(self, user_id: str, mode: str):
        """Set user's preferred mode"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id=user_id)
        
        self.user_sessions[user_id].user_preferences["mode"] = mode
        
        # Also set on active conversation if exists
        active_conv = self.get_active_conversation(user_id)
        if active_conv:
            active_conv.current_mode = mode
            self._save_conversation_to_disk(active_conv)
        
        self._save_user_sessions_to_disk()
    
    def set_user_domain(self, user_id: str, domain: str):
        """Set user's preferred domain"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id=user_id)
        
        self.user_sessions[user_id].user_preferences["domain"] = domain
        
        # Also set on active conversation if exists
        active_conv = self.get_active_conversation(user_id)
        if active_conv:
            active_conv.current_domain = domain
            self._save_conversation_to_disk(active_conv)
        
        self._save_user_sessions_to_disk()
    
    def get_user_preferences(self, user_id: str) -> dict:
        """Get user's session preferences"""
        if user_id not in self.user_sessions:
            return {
                "mode": "TECHNICAL",
                "domain": "general"
            }
        
        prefs = self.user_sessions[user_id].user_preferences
        return {
            "mode": prefs.get("mode", "TECHNICAL"),
            "domain": prefs.get("domain", "general")
        }
    
    def archive_conversation(self, session_id: str):
        """Archive a conversation"""
        if session_id in self.conversations:
            self.conversations[session_id].archived = True
            self._save_conversation_to_disk(self.conversations[session_id])
    
    def delete_conversation(self, session_id: str):
        """Delete a conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            
            # Remove from all user histories
            for user_session in self.user_sessions.values():
                if session_id in user_session.conversation_history:
                    user_session.conversation_history.remove(session_id)
                if user_session.active_session_id == session_id:
                    user_session.active_session_id = ""
            
            # Delete from disk
            try:
                filepath = os.path.join(self.storage_dir, "conversations", f"{session_id}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Error deleting conversation file: {e}")
            
            self._save_user_sessions_to_disk()
    
    def set_active_conversation(self, user_id: str, session_id: str) -> bool:
        """Switch user's active conversation"""
        if session_id not in self.conversations:
            return False
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id=user_id)
        
        self.user_sessions[user_id].active_session_id = session_id
        self.user_sessions[user_id].last_activity = datetime.utcnow().isoformat()
        self._save_user_sessions_to_disk()
        return True


# Global session manager instance
session_manager = SessionManager()
