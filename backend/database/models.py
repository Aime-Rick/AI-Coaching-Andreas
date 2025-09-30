from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
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
    vector_store_id = Column(String(255), nullable=True)  # Associated document context
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="chat")  # 'chat', 'report', 'system'
    timestamp = Column(DateTime, default=datetime.utcnow)
    tokens_used = Column(Integer, nullable=True)  # For tracking usage
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")