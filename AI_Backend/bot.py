# bot.py - Web UI Bot Engine with Session Management

import os
from dotenv import load_dotenv, find_dotenv
import logging

load_dotenv(find_dotenv())

from .sme_engine import SMEEngine
from .agent import AgentFactory
from .session_manager import session_manager
from .conversation import Conversation

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Get the directory of this file for relative paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

AVAILABLE_DOMAINS = {
    "legal_compliance": os.path.join(BACKEND_DIR, "domains/legal_compliance.json"),
    "financial_analysis": os.path.join(BACKEND_DIR, "domains/financial_advisor.json"),
    "cybersecurity": os.path.join(BACKEND_DIR, "domains/cybersecurity.json"),
    "general": os.path.join(BACKEND_DIR, "domains/general.json")
}


class WebUIBot:
    """
    Web UI Bot Engine
    - Manages conversations per user via SessionManager
    - Handles agent invocation with multi-turn context
    - No Telegram dependencies
    """
    
    def __init__(self):
        self.sme_engine = SMEEngine(os.path.join(BACKEND_DIR, "domains/general.json"))
        self.agent_factory = AgentFactory()
        self.session_manager = session_manager
    
    def get_or_create_conversation(self, user_id: str) -> Conversation:
        """Get user's active conversation or create new one"""
        active_conv = self.session_manager.get_active_conversation(user_id)
        if active_conv:
            return active_conv
        
        # Create new conversation
        return self.session_manager.create_conversation(user_id)
    
    def classify_domain(self, user_text):
        """Classify user input into a domain"""
        prompt = f"""
Classify into:
- general
- legal_compliance
- financial_analysis
- cybersecurity

Respond ONLY with domain name.

User Query:
{user_text}
"""
        try:
            llm = self.agent_factory.llm
            response = llm.invoke(prompt)
            raw = response.content.strip().lower()

            for key in AVAILABLE_DOMAINS:
                if key in raw:
                    return key
        except Exception as e:
            logging.error(f"Domain classification error: {e}")
        
        return "general"
    
    def set_mode(self, user_id: str, mode: str) -> dict:
        """Set conversation mode for a user"""
        mode = mode.upper()
        
        if mode not in ["TECHNICAL", "EXECUTIVE", "AUDIT", "CLIENT"]:
            return {"error": "Invalid mode. Choose: TECHNICAL, EXECUTIVE, AUDIT, CLIENT"}
        
        self.session_manager.set_user_mode(user_id, mode)
        
        return {"status": f"Mode set to {mode}", "mode": mode}
    
    def set_domain(self, user_id: str, domain: str) -> dict:
        """Set conversation domain for a user"""
        if domain not in AVAILABLE_DOMAINS:
            return {"error": f"Invalid domain. Choose: {', '.join(AVAILABLE_DOMAINS.keys())}"}
        
        self.session_manager.set_user_domain(user_id, domain)
        
        return {"status": f"Domain set to {domain}", "domain": domain}
    
    def get_modes(self) -> dict:
        """Get available modes"""
        return {
            "available_modes": ["TECHNICAL", "EXECUTIVE", "AUDIT", "CLIENT"],
            "descriptions": {
                "TECHNICAL": "Use deep technical analysis and structured reasoning.",
                "EXECUTIVE": "Provide concise strategic summaries.",
                "AUDIT": "Focus strictly on compliance, risk, and verification.",
                "CLIENT": "Use simple, accessible language."
            }
        }
    
    def get_domains(self) -> dict:
        """Get available domains"""
        return {
            "available_domains": list(AVAILABLE_DOMAINS.keys()),
            "descriptions": {
                "general": "General knowledge and advice",
                "legal_compliance": "Legal and regulatory compliance",
                "financial_analysis": "Financial analysis and planning",
                "cybersecurity": "Cybersecurity and threat analysis"
            }
        }
    
    def process_message(self, user_id: str, user_text: str) -> dict:
        """
        Process user message and return agent response
        Maintains conversation history and context
        """
        try:
            # Get or create conversation
            conversation = self.get_or_create_conversation(user_id)
            
            # Add user message to conversation
            conversation.add_message("user", user_text)
            
            # Detect domain
            detected_domain = self.classify_domain(user_text)
            conversation.current_domain = detected_domain
            
            # Load domain configuration
            domain_path = AVAILABLE_DOMAINS.get(detected_domain, AVAILABLE_DOMAINS["general"])
            self.sme_engine.switch_domain(domain_path)
            system_prompt = self.sme_engine.build_system_prompt()
            
            # Get current mode from session
            mode = conversation.current_mode
            
            mode_instruction = {
                "TECHNICAL": "Use deep technical analysis and structured reasoning.",
                "EXECUTIVE": "Provide concise strategic summaries.",
                "AUDIT": "Focus strictly on compliance, risk, and verification.",
                "CLIENT": "Use simple, accessible language."
            }.get(mode, "Use deep technical analysis and structured reasoning.")
            
            system_prompt = f"{system_prompt}\n\nOUTPUT MODE:\n{mode_instruction}"
            
            # Create agent with updated prompt
            agent = self.agent_factory.create_agent(system_prompt)
            
            # Invoke agent with full conversation history
            messages = conversation.get_messages_for_llm()
            response = agent.invoke({"messages": messages})
            
            # Extract reply
            last_message = response.get("messages", [])[-1]
            
            reply = ""
            if hasattr(last_message, "content"):
                if isinstance(last_message.content, list):
                    text_parts = [
                        block.get("text", "")
                        for block in last_message.content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    reply = "\n".join(text_parts)
                else:
                    reply = str(last_message.content)
            
            if not reply.strip():
                reply = "⚠️ No response generated."
            
            # Cap length
            reply = reply[:8000]
            
            # Add assistant response to conversation
            conversation.add_message("assistant", reply, {
                "domain": detected_domain,
                "mode": mode
            })
            
            # Persist conversation
            self.session_manager._save_conversation_to_disk(conversation)
            
            return {
                "success": True,
                "session_id": conversation.session_id,
                "domain": detected_domain,
                "mode": mode,
                "response": reply,
                "message_count": len(conversation.messages)
            }
        
        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            logging.error(f"User {user_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "response": error_msg
            }
    
    def get_conversation_history(self, user_id: str, session_id: str = None) -> dict:
        """Get conversation history for a user"""
        if session_id:
            conv = self.session_manager.get_conversation(session_id)
        else:
            conv = self.session_manager.get_active_conversation(user_id)
        
        if not conv:
            return {"error": "Conversation not found"}
        
        return {
            "session_id": conv.session_id,
            "messages": [msg.to_dict() for msg in conv.messages],
            "domain": conv.current_domain,
            "mode": conv.current_mode,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at
        }
    
    def get_all_conversations(self, user_id: str) -> dict:
        """Get all conversations for a user"""
        conversations = self.session_manager.get_user_conversations(user_id)
        
        return {
            "conversations": [
                {
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                    "message_count": len(conv.messages),
                    "domain": conv.current_domain,
                    "mode": conv.current_mode
                }
                for conv in conversations
            ],
            "total": len(conversations)
        }
    
    def create_new_conversation(self, user_id: str, title: str = "") -> dict:
        """Create a new conversation for user"""
        conv = self.session_manager.create_conversation(user_id, title)
        
        return {
            "session_id": conv.session_id,
            "title": conv.title,
            "created_at": conv.created_at
        }
    
    def switch_conversation(self, user_id: str, session_id: str) -> dict:
        """Switch user's active conversation"""
        success = self.session_manager.set_active_conversation(user_id, session_id)
        
        if not success:
            return {"error": "Conversation not found"}
        
        return {"status": "Conversation switched", "session_id": session_id}
    
    def delete_conversation(self, user_id: str, session_id: str) -> dict:
        """Delete a conversation"""
        conv = self.session_manager.get_conversation(session_id)
        if not conv or conv.user_id != user_id:
            return {"error": "Conversation not found or unauthorized"}
        
        self.session_manager.delete_conversation(session_id)
        
        return {"status": "Conversation deleted"}


# Global bot instance
bot = WebUIBot()