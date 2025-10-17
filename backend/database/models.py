from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(255), index=True, nullable=True)  # Optional user identification
    title = Column(String(500), nullable=True)  # Auto-generated or user-provided title
    vector_store_id = Column(String(255), nullable=True, index=True)  # Associated document context
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationship to messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", lazy="selectin")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_user_active_updated', 'user_id', 'is_active', 'updated_at'),
        Index('idx_vector_store', 'vector_store_id'),
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="chat", index=True)  # 'chat', 'report', 'system'
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tokens_used = Column(Integer, nullable=True)  # For tracking usage
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_session_type_timestamp', 'session_id', 'message_type', 'timestamp'),
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )