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
                 api_key=os.getenv("OPENAI_API_KEY"),
                 temperature=0)

chat_prompt="""
You are an AI assistant designed to answer user queries using the provided context documents.  

## Rules
1. Always prioritize the information found in the retrieved documents when generating responses.  
2. If the answer is clearly present in the documents, respond concisely and accurately based only on that content.  
3. If the documents contain partial or ambiguous information, acknowledge the uncertainty and provide the most relevant parts without inventing facts.  
4. If no useful information is found in the documents, explicitly state that the answer is not available in the provided context. Do **not** hallucinate.  
5. Maintain a clear, helpful, and professional tone.  
6. If the user asks questions outside the scope of the documents, politely explain that you can only respond based on the provided materials.
7. Do **not** include any citations, file references, or technical tokens.  

## Output Format
- Directly answer the user’s question. 
- Your answer should be clear, well structured, and to the point.  
"""

REPORT_PROMPTS = {
    "en": {
        "prompt": """You are an expert health and wellness coaching assistant.  

Your task is to analyze client anamnesis documents (covering weight, goals, illnesses, medications, sleep, digestion, hormones, lifestyle, etc.) and generate a **clear, professional, and well-structured report** for the coach.  

The report must strictly follow this structure:

---

**Summary of the Client’s Situation**  
- Write 3–6 concise bullet points or short paragraphs summarizing the client’s health status, lifestyle habits, challenges, and personal goals.  
- Keep it professional and easy to read. Avoid overly technical terms.  

---

**Key Priorities for Coaching**  
Present the most important focus areas in a **numbered list**, in order of priority. For each priority:  
- State the focus area clearly (e.g., Sleep Routine, Nutrition Habits, Stress Management, Physical Activity).  
- Provide 1–2 short sentences explaining *why* this is important and how it connects to the client’s goals.  

---
Do not include any additional sections or information beyond what is specified above.
**Formatting & Style Rules:**  
- Use **bold headings** exactly as shown above.  
- Use short paragraphs and bullet points for readability.  
- When generating coaching priorities, use a plain text ordered list (e.g., “1.”, “2.”, “3.”) without any bullets, indentation, or subpoints. Each priority should appear on a single line in plain text.
- Keep the tone professional, supportive, and actionable.  
- Do **not** include medical diagnoses.  
- Do **not** include any citations, file references, or technical tokens.  
- Output **only** the structured coaching report.  
- Write the entire report in natural, professional English.  

The final document should look polished, easy to read, and ready to share with the coach.
""",
        "query": """You have been provided with the client anamnesis documents.
Please generate a structured coaching report that includes:  
- A clear summary of the client’s current situation.  
- Suggested coaching priorities, listed in order of importance, with short explanations for each.  """
    },
    "de": {
        "prompt": """Du bist ein Experte für Gesundheits- und Wellness-Coaching.  

Deine Aufgabe besteht darin, die Anamnesedokumente eines Klienten (Gewicht, Ziele, Krankheiten, Medikamente, Schlaf, Verdauung, Hormone, Lebensstil usw.) zu analysieren und einen **klaren, professionellen und gut strukturierten Bericht** für den Coach zu erstellen.  

Der Bericht muss strikt folgende Struktur haben:

---

**Zusammenfassung der Situation des Klienten**  
- Formuliere 3–6 kurze Stichpunkte oder Absätze, die den Gesundheitszustand, Gewohnheiten, Herausforderungen und Ziele des Klienten zusammenfassen.  
- Bleibe professionell und leicht verständlich. Vermeide unnötig technische Begriffe.  

---

**Wichtige Coaching-Prioritäten**  
Stelle die wichtigsten Fokusthemen in einer **nummerierten Liste** in Reihenfolge der Priorität dar. Für jede Priorität gilt:  
- Benenne das Fokusthema klar (z. B. Schlafroutine, Ernährungsgewohnheiten, Stressmanagement, körperliche Aktivität).  
- Gib 1–2 kurze Sätze an, warum dieses Thema wichtig ist und wie es mit den Zielen des Klienten zusammenhängt.  

---
Nimm keine zusätzlichen Abschnitte oder Informationen auf, die hier nicht vorgegeben sind.
**Formatierungs- und Stilregeln:**  
- Verwende **fett gedruckte Überschriften** genau wie oben angegeben.  
- Nutze kurze Absätze und Stichpunkte für gute Lesbarkeit.  
- Beim Erstellen der Coaching-Prioritäten verwende eine einfache nummerierte Textliste (z. B. „1.“, „2.“, „3.“), ohne Aufzählungszeichen, Einrückungen oder Unterpunkte. Jede Priorität soll in einer einzelnen Zeile als Klartext erscheinen.
- Bleibe professionell, unterstützend und handlungsorientiert.  
- Stelle keine medizinischen Diagnosen.  
- Füge keine Quellenangaben, Dateiverweise oder technischen Tokens hinzu.  
- Gib **nur** den strukturierten Coaching-Bericht aus.  
- Schreibe den gesamten Bericht in natürlichem, professionellem Deutsch.  

Das Ergebnis soll sauber formatiert, leicht lesbar und sofort mit dem Coach teilbar sein.
""",
        "query": """Dir liegen die Anamnesedokumente des Klienten vor.
Bitte erstelle einen strukturierten Coaching-Bericht, der Folgendes enthält:  
- Eine klare Zusammenfassung der aktuellen Situation des Klienten.  
- Coaching-Prioritäten in Reihenfolge der Wichtigkeit, jeweils mit kurzen Begründungen.  """
    }
}

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
    
    # Extract text content from response (handle both string and structured formats)
    if isinstance(response.content, str):
        response_content = response.content
    elif isinstance(response.content, list):
        # Extract text from structured content blocks
        response_content = ""
        for block in response.content:
            if isinstance(block, dict) and block.get('type') == 'text':
                response_content += block.get('text', '')
            elif isinstance(block, str):
                response_content += block
        if not response_content:
            response_content = str(response.content)
    else:
        response_content = str(response.content)
    
    # Save assistant response to database
    # Note: You might want to calculate actual tokens used here
    memory_service.add_message(session_id, "assistant", response_content, "chat")
    
    db.close()
    
    return {
        "response": response_content,
        "session_id": session_id,
        "message_count": len(chat_history) + 2  # +2 for current user message and response
    }


def generate_report(vector_store_id: str, session_id: Optional[str] = None, user_id: Optional[str] = None, language: Optional[str] = None) -> Dict:
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
    
    # Determine prompt language
    normalized_language = (language or "en").split("-")[0].lower()
    prompt_bundle = REPORT_PROMPTS.get(normalized_language, REPORT_PROMPTS["en"])
    report_messages = [
        {"role": "system", "content": prompt_bundle["prompt"]},
        {"role": "user", "content": prompt_bundle["query"]}
    ]

    # Save the report generation request
    memory_service.add_message(session_id, "user", prompt_bundle["query"], "report")
    
    # Bind tools to the model
    tools = [
        {
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }
    ]
    model_with_tools = llm.bind_tools(tools)

    response = model_with_tools.invoke(report_messages)
    
    # Extract text content from response (handle both string and structured formats)
    if isinstance(response.content, str):
        report_content = response.content
    elif isinstance(response.content, list):
        # Extract text from structured content blocks
        report_content = ""
        for block in response.content:
            if isinstance(block, dict) and block.get('type') == 'text':
                report_content += block.get('text', '')
            elif isinstance(block, str):
                report_content += block
        if not report_content:
            report_content = str(response.content)
    else:
        report_content = str(response.content)
    
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
    """Get full chat history for a session, excluding report messages"""
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

def get_session_reports(session_id: str) -> List[Dict]:
    """Get all report messages for a session"""
    db = next(get_db())
    memory_service = ChatMemoryService(db)
    
    reports = memory_service.get_session_reports(session_id)
    
    result = []
    for report in reports:
        result.append({
            "role": report.role,
            "content": report.content,
            "message_type": report.message_type,
            "timestamp": report.timestamp.isoformat(),
            "tokens_used": report.tokens_used
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
        
        # Get message count before deletion (only count chat messages, not reports)
        chat_messages = memory_service.get_chat_history(session_id)
        messages_deleted = len(chat_messages)
        
        # Delete the session (this will also delete all messages due to cascade)
        success = memory_service.delete_session(session_id)
        db.close()
        
        if not success:
            raise Exception("Failed to delete session")
        
        # Clean up vector store if it exists
        vector_store_deleted = False
        if vector_store_id:
            vector_store_deleted = remove_vector_store(vector_store_id)
        
        # Return structure expected by API
        cleanup_status = {
            "session_deleted": success,
            "vector_store_deleted": vector_store_deleted,
            "messages_deleted": messages_deleted
        }
        
        return {
            "message": "Chat session ended successfully",
            "cleanup_status": cleanup_status,
            "session_id": session_id,
            "vector_store_id": vector_store_id,
            "messages_deleted": messages_deleted
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


# Cleanup and maintenance functions

def cleanup_orphaned_resources() -> Dict:
    """
    Clean up orphaned resources (sessions without vector stores, vector stores without sessions)
    
    Returns:
        Dict with cleanup statistics and results
    """
    try:
        db = next(get_db())
        memory_service = ChatMemoryService(db)
        
        # Get all sessions
        all_sessions = memory_service.get_all_sessions()
        
        cleanup_stats = {
            "sessions_checked": len(all_sessions),
            "orphaned_sessions_cleaned": 0,
            "vector_stores_cleaned": 0,
            "errors": []
        }
        
        # Check each session for orphaned resources
        for session in all_sessions:
            try:
                # If session has a vector store ID, check if it actually exists
                if session.vector_store_id:
                    # Try to get vector store info to see if it exists
                    # This is a simple check - in a real implementation you might want to
                    # check with OpenAI API to see if the vector store actually exists
                    pass
                else:
                    # Session without vector store - this might be orphaned
                    # For now, we'll leave it as sessions can exist without vector stores
                    pass
                    
            except Exception as e:
                cleanup_stats["errors"].append(f"Error checking session {session.session_id}: {str(e)}")
        
        db.close()
        return cleanup_stats
        
    except Exception as e:
        return {
            "error": f"Failed to cleanup orphaned resources: {str(e)}",
            "sessions_checked": 0,
            "orphaned_sessions_cleaned": 0,
            "vector_stores_cleaned": 0,
            "errors": [str(e)]
        }


def force_cleanup_session(session_id: str) -> Dict:
    """
    Force cleanup of a session even if partially deleted or corrupted
    
    Args:
        session_id: Session identifier to force cleanup
        
    Returns:
        Dict with force cleanup results
    """
    try:
        db = next(get_db())
        memory_service = ChatMemoryService(db)
        
        cleanup_results = {
            "session_id": session_id,
            "session_deleted": False,
            "messages_deleted": 0,
            "vector_store_id": None,
            "vector_store_deleted": False,
            "errors": []
        }
        
        # Try to get session info
        try:
            session = memory_service.get_session(session_id)
            if session:
                cleanup_results["vector_store_id"] = session.vector_store_id
        except Exception as e:
            cleanup_results["errors"].append(f"Could not retrieve session info: {str(e)}")
        
        # Force delete session and messages
        try:
            # Get message count before deletion (only count chat messages, not reports)
            chat_messages = memory_service.get_chat_history(session_id)
            cleanup_results["messages_deleted"] = len(chat_messages)
            
            # Delete the session (cascade will delete messages)
            success = memory_service.delete_session(session_id)
            cleanup_results["session_deleted"] = success
            
            if not success:
                cleanup_results["errors"].append("Failed to delete session from database")
                
        except Exception as e:
            cleanup_results["errors"].append(f"Error deleting session: {str(e)}")
        
        # Try to cleanup vector store if we have the ID
        if cleanup_results["vector_store_id"]:
            try:
                vector_store_deleted = remove_vector_store(cleanup_results["vector_store_id"])
                cleanup_results["vector_store_deleted"] = vector_store_deleted
                
                if not vector_store_deleted:
                    cleanup_results["errors"].append("Failed to delete vector store")
                    
            except Exception as e:
                cleanup_results["errors"].append(f"Error deleting vector store: {str(e)}")
        
        db.close()
        return cleanup_results
        
    except Exception as e:
        return {
            "session_id": session_id,
            "session_deleted": False,
            "messages_deleted": 0,
            "vector_store_id": None,
            "vector_store_deleted": False,
            "errors": [f"Force cleanup failed: {str(e)}"]
        }
