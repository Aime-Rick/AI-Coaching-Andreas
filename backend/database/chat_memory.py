from sqlalchemy.orm import Session
from backend.database.models import ChatSession, ChatMessage
from typing import List, Optional
import uuid
from datetime import datetime

class ChatMemoryService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, user_id: Optional[str] = None, vector_store_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Create a new chat session and return session_id"""
        session_id = str(uuid.uuid4())
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            vector_store_id=vector_store_id,
            title=title or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return self.db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    
    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[ChatSession]:
        """Get all sessions for a user"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    def get_all_sessions(self, limit: int = 1000) -> List[ChatSession]:
        """Get all active sessions in the database"""
        return self.db.query(ChatSession).filter(
            ChatSession.is_active == True
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    def add_message(self, session_id: str, role: str, content: str, message_type: str = "chat", tokens_used: Optional[int] = None) -> ChatMessage:
        """Add a message to a chat session"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            tokens_used=tokens_used
        )
        
        self.db.add(message)
        
        # Update session's updated_at timestamp
        session = self.get_session(session_id)
        if session:
            session.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a session, ordered by timestamp"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.asc()).limit(limit).all()
    
    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get the most recent messages for context"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()[::-1]  # Reverse to get chronological order
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        session = self.get_session(session_id)
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session (soft delete)"""
        session = self.get_session(session_id)
        if session:
            session.is_active = False
            session.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session and all its messages"""
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
    
    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        message_count = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
        total_tokens = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.tokens_used.isnot(None)
        ).with_entities(ChatMessage.tokens_used).all()
        
        total_tokens_used = sum(tokens[0] for tokens in total_tokens if tokens[0])
        
        return {
            "session_id": session_id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": message_count,
            "total_tokens_used": total_tokens_used,
            "vector_store_id": session.vector_store_id
        }