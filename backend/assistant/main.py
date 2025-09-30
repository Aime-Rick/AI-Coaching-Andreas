from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import Runnable
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from backend.database.connection import get_db, create_tables
from backend.database.chat_memory import ChatMemoryService
from backend.database.models import ChatMessage
from backend.assistant.utils import create_vector_store, create_vector_store_from_files, delete_vector_store

load_dotenv()

# Initialize database
create_tables()

llm = ChatOpenAI(model="gpt-5-mini", 
                 max_completion_tokens=20000, 
                 organization="Andreas Project",
                 api_key=os.getenv("OPENAI_API_KEY"))

chat_prompt="""
You are an AI assistant designed to answer user queries using the provided context documents.  

## Rules
1. Always prioritize the information found in the retrieved documents when generating responses.  
2. If the answer is clearly present in the documents, respond concisely and accurately based only on that content.  
3. If the documents contain partial or ambiguous information, acknowledge the uncertainty and provide the most relevant parts without inventing facts.  
4. If no useful information is found in the documents, explicitly state that the answer is not available in the provided context. Do **not** hallucinate.  
5. Maintain a clear, helpful, and professional tone.  
6. If the user asks questions outside the scope of the documents, politely explain that you can only respond based on the provided materials.  

## Output Format
- Directly answer the user’s question.    
"""

report_prompt = """
You are an expert health and wellness coaching assistant.  
Your role is to analyze client anamnesis documents (covering weight, goals, illnesses, medications, sleep, digestion, hormones, lifestyle, etc.) and generate a **structured report** for the coach.  

The report must include:
1. **Summary of the client’s situation** — provide a clear, professional overview of their health status, challenges, and goals.  
2. **Key priorities for coaching** — suggest the most important areas to focus on first (e.g., lifestyle habits, nutrition, sleep, stress management, etc.), with reasoning behind the order of priorities.  
3. **Clarity and structure** — use headings, bullet points, and concise explanations. Keep the tone professional, supportive, and actionable.  

Do not give medical diagnoses. Instead, highlight coaching priorities and suggestions that support the client in achieving their goals.
"""

report_query="""
You have been provided with the client anamnesis documents.
Please generate a structured coaching report that includes:  
- A clear summary of the client’s current situation.  
- Suggested coaching priorities, listed in order of importance, with short explanations for each.  """

report_messages = [{"role": "system", "content": report_prompt},
                {"role": "user", "content": report_query}]

def generate_chat_response(message: str, vector_store_id: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
    """
    Generate a chat response with memory management.
    
    Args:
        message: User's message
        vector_store_id: ID of the vector store for document context
        session_id: Optional existing session ID (required for session-managed flow)
        user_id: Optional user identifier
    
    Returns:
        Dict with response, session_id, and message details
    """
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    # For session-managed flow, session_id should already exist
    if not session_id:
        # Legacy behavior: create new session if none provided
        session_id = memory_service.create_session(
            user_id=user_id,
            vector_store_id=vector_store_id,
            title=f"Chat about: {message[:50]}..."
        )
    
    # Get chat history for context
    chat_history = memory_service.get_recent_messages(session_id, limit=10)
    
    # Build messages with history
    messages = [{"role": "system", "content": chat_prompt}]
    
    # Add chat history
    for hist_msg in chat_history:
        messages.append({
            "role": hist_msg.role,
            "content": hist_msg.content
        })
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    # Save user message to database
    memory_service.add_message(session_id, "user", message, "chat")
    
    # Generate response
    tools = [
        {
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }
    ]
    model_with_tools = llm.bind_tools(tools)
    
    response = model_with_tools.invoke(messages)
    response_content = response.content
    
    # Save assistant response to database
    # Note: You might want to calculate actual tokens used here
    memory_service.add_message(session_id, "assistant", response_content, "chat")
    
    db.close()
    
    return {
        "response": response_content,
        "session_id": session_id,
        "message_count": len(chat_history) + 2  # +2 for current user message and response
    }


def generate_report(vector_store_id: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
    """
    Generate a coaching report with memory management.
    
    Args:
        vector_store_id: ID of the vector store for document context
        session_id: Optional existing session ID (required for session-managed flow)
        user_id: Optional user identifier
    
    Returns:
        Dict with report content, session_id, and details
    """
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    # For session-managed flow, session_id should already exist
    if not session_id:
        # Legacy behavior: create new session if none provided
        session_id = memory_service.create_session(
            user_id=user_id,
            vector_store_id=vector_store_id,
            title="Coaching Report Generation"
        )
    
    # Save the report generation request
    memory_service.add_message(session_id, "user", report_query, "report")
    
    # Bind tools to the model
    tools = [
        {
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }
    ]
    model_with_tools = llm.bind_tools(tools)

    response = model_with_tools.invoke(report_messages)
    report_content = response.content
    
    # Save the report to database
    memory_service.add_message(session_id, "assistant", report_content, "report")
    
    db.close()
    
    return {
        "report": report_content,
        "session_id": session_id,
        "type": "report"
    }

# Additional helper functions for chat management

def get_chat_sessions(user_id: str, limit: int = 50) -> List[Dict]:
    """Get all chat sessions for a user"""
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    sessions = memory_service.get_user_sessions(user_id, limit)
    
    result = []
    for session in sessions:
        stats = memory_service.get_session_stats(session.session_id)
        result.append(stats)
    
    db.close()
    return result

def get_chat_history(session_id: str) -> List[Dict]:
    """Get full chat history for a session"""
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    messages = memory_service.get_chat_history(session_id)
    
    result = []
    for msg in messages:
        result.append({
            "role": msg.role,
            "content": msg.content,
            "message_type": msg.message_type,
            "timestamp": msg.timestamp.isoformat(),
            "tokens_used": msg.tokens_used
        })
    
    db.close()
    return result

def delete_chat_session(session_id: str) -> bool:
    """Delete a chat session"""
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    result = memory_service.delete_session(session_id)
    db.close()
    return result

def update_session_title(session_id: str, title: str) -> bool:
    """Update a session's title"""
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    result = memory_service.update_session_title(session_id, title)
    db.close()
    return result

# Vector Store Management Functions

def create_vector_store_from_folder(folder_path: str, store_name: Optional[str] = None) -> str:
    """
    Create a vector store from all files in a folder
    
    Args:
        folder_path: Path to folder in file management system (e.g., "documents/client_files")
        store_name: Optional custom name for the vector store
    
    Returns:
        Vector store ID
    """
    return create_vector_store(folder_path, store_name)

def create_vector_store_from_file_list(file_paths: List[str], store_name: Optional[str] = None) -> str:
    """
    Create a vector store from a list of specific files
    
    Args:
        file_paths: List of file paths in the file management system
        store_name: Optional custom name for the vector store
    
    Returns:
        Vector store ID
    """
    return create_vector_store_from_files(file_paths, store_name)

def remove_vector_store(vector_store_id: str) -> bool:
    """
    Delete a vector store
    
    Args:
        vector_store_id: ID of the vector store to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        delete_vector_store(vector_store_id)
        return True
    except Exception as e:
        print(f"Error deleting vector store {vector_store_id}: {str(e)}")
        return False


# Session Lifecycle Management Functions

def start_chat_session(user_id: Optional[str] = None, folder_path: Optional[str] = None, file_paths: Optional[List[str]] = None, session_title: Optional[str] = None) -> Dict:
    """
    Start a new chat session with automatic vector store creation
    
    Args:
        user_id: Optional user identifier
        folder_path: Optional path to folder for vector store creation
        file_paths: Optional list of file paths for vector store creation
        session_title: Optional title for the session
    
    Returns:
        Dict with session_id, vector_store_id, and success message
    """
    try:
        # Create vector store first
        if folder_path:
            store_name = session_title or f"Session Documents - {folder_path}"
            vector_store_id = create_vector_store_from_folder(folder_path, store_name)
        elif file_paths:
            store_name = session_title or f"Session Documents - {len(file_paths)} files"
            vector_store_id = create_vector_store_from_file_list(file_paths, store_name)
        else:
            raise ValueError("Either folder_path or file_paths must be provided")
        
        # Create chat session with vector store
        db = next(get_db())
        memory_service = ChatMemoryService(db)
        
        session_title = session_title or f"Chat Session - {vector_store_id[:8]}"
        session_id = memory_service.create_session(
            user_id=user_id,
            vector_store_id=vector_store_id,
            title=session_title
        )
        
        db.close()
        
        return {
            "session_id": session_id,
            "vector_store_id": vector_store_id,
            "message": "Chat session started successfully with vector store created"
        }
        
    except Exception as e:
        # Clean up vector store if session creation fails
        if 'vector_store_id' in locals():
            try:
                remove_vector_store(vector_store_id)
            except:
                pass
        raise Exception(f"Failed to start chat session: {str(e)}")


def end_chat_session(session_id: str) -> Dict:
    """
    End a chat session and clean up the vector store
    
    Args:
        session_id: Session identifier
    
    Returns:
        Dict with success message and cleanup status
    """
    try:
        db = next(get_db())
        memory_service = ChatMemoryService(db)
        
        # Get session to retrieve vector store ID
        session = memory_service.get_session(session_id)
        if not session:
            db.close()
            raise ValueError(f"Session not found: {session_id}")
        
        vector_store_id = session.vector_store_id
        
        # Delete the session (this will also delete all messages due to cascade)
        success = memory_service.delete_session(session_id)
        db.close()
        
        if not success:
            raise Exception("Failed to delete session")
        
        # Clean up vector store if it exists
        vector_store_deleted = False
        if vector_store_id:
            vector_store_deleted = remove_vector_store(vector_store_id)
        
        return {
            "message": "Chat session ended successfully",
            "vector_store_deleted": vector_store_deleted
        }
        
    except Exception as e:
        raise Exception(f"Failed to end chat session: {str(e)}")


def get_session_vector_store(session_id: str) -> Optional[str]:
    """
    Get the vector store ID associated with a session
    
    Args:
        session_id: Session identifier
    
    Returns:
        Vector store ID if found, None otherwise
    """
    try:
        db = next(get_db())
        memory_service = ChatMemoryService(db)
        
        session = memory_service.get_session(session_id)
        db.close()
        
        if session:
            return session.vector_store_id
        return None
        
    except Exception as e:
        print(f"Error getting session vector store: {str(e)}")
        return None
