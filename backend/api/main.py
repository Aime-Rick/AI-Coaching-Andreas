"""
File Management System for AWS S3
Provides comprehensive file and folder management capabilities.
""" 
from fastapi import FastAPI, HTTPException, UploadFile, File as FastAPIFile, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import List, Optional, Dict, Any
import os
import tempfile
import zipfile
import io
import urllib.parse
from pathlib import Path
import mimetypes
import asyncio
import time
import logging
from pydantic import BaseModel, Field

from backend.files.utils import FileManager
from backend.files.models import (
    FileInfo, 
    FolderInfo, 
    CreateFolderRequest, 
    FileListResponse,
    DeleteRequest,
    UploadResponse
)

# Import assistant functions
try:
    from backend.assistant.main import (
        generate_chat_response, 
        generate_report,
        get_chat_sessions,
        get_chat_history,
        get_session_reports,
        delete_chat_session,
        update_session_title,
        create_vector_store_from_folder,
        create_vector_store_from_file_list,
        remove_vector_store,
        start_chat_session,
        end_chat_session,
        get_session_vector_store,
        cleanup_orphaned_resources,
        force_cleanup_session
    )
    from backend.assistant.cleanup_scheduler import (
        start_cleanup_scheduler,
        stop_cleanup_scheduler,
        manual_cleanup,
        cleanup_scheduler
    )
    cleanup_available = True
except ImportError:
    # Handle case where assistant module is not available
    generate_chat_response = None
    generate_report = None
    get_chat_sessions = None
    get_chat_history = None
    get_session_reports = None
    delete_chat_session = None
    update_session_title = None
    create_vector_store_from_folder = None
    create_vector_store_from_file_list = None
    remove_vector_store = None
    start_chat_session = None
    end_chat_session = None
    get_session_vector_store = None
    cleanup_orphaned_resources = None
    force_cleanup_session = None
    start_cleanup_scheduler = None
    stop_cleanup_scheduler = None
    manual_cleanup = None
    cleanup_scheduler = None
    cleanup_available = False

app = FastAPI(
    title="AI Coaching File Management API", 
    description="Comprehensive file management system with AI coaching capabilities",
    version="1.0.0",
    tags_metadata=[
        {
            "name": "System",
            "description": "System information and health checks"
        },
        {
            "name": "File Management",
            "description": "Core file and folder operations - create, read, update, delete files and folders"
        },
        {
            "name": "File Operations",
            "description": "Advanced file operations - upload, download, copy, move, search"
        },
        {
            "name": "AI Chat",
            "description": "AI-powered chat functionality with session management"
        },
        {
            "name": "AI Reports",
            "description": "AI-generated coaching reports and analysis"
        },
        {
            "name": "Vector Stores",
            "description": "Vector store management for AI document processing"
        },
        {
            "name": "Session Management",
            "description": "Chat session lifecycle and history management"
        },
        {
            "name": "System Maintenance",
            "description": "Automatic cleanup, scheduled tasks, and system maintenance operations"
        },
        {
            "name": "Storage",
            "description": "Storage statistics and disk usage information"
        }
    ]
)

# Performance optimization middleware with enhanced error handling
@app.middleware("http")
async def add_performance_headers(request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log slow requests
        if process_time > 5.0:  # Log requests taking more than 5 seconds
            logging.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
        
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["Cache-Control"] = "no-cache"
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logging.error(f"Request failed: {request.method} {request.url.path} after {process_time:.2f}s - {str(e)}")
        raise

# Add performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize file manager
file_manager = FileManager(skip_validation=True)  # Skip S3 validation for development
REPORTS_FOLDER_PATH = os.getenv("REPORTS_FOLDER_PATH", "Reports")


def ensure_reports_folder_exists() -> None:
    """Ensure the reports folder exists in the storage backend."""
    reports_path = "/".join(segment for segment in REPORTS_FOLDER_PATH.strip().split("/") if segment)

    if not reports_path:
        print("⚠️ Reports folder path is empty; skipping automatic creation")
        return

    if getattr(file_manager, "_development_mode", False):
        print("ℹ️ Skipping Reports folder creation (file manager running without S3)")
        return

    if not hasattr(file_manager, "s3_client"):
        print("ℹ️ Skipping Reports folder creation (S3 client not initialized)")
        return

    try:
        info = file_manager.get_file_info(reports_path)
        if info.get("is_folder", False):
            return
        print(f"⚠️ Path '{reports_path}' already exists but is not a folder; skipping automatic creation")
    except HTTPException as http_exc:
        if http_exc.status_code != 404:
            print(f"⚠️ Could not verify Reports folder: {http_exc.detail}")
            return

        try:
            parts = reports_path.split("/")
            clean_parts = [part for part in parts if part]
            folder_name = clean_parts[-1]
            parent_path = "/".join(clean_parts[:-1]) or None
            created_path = file_manager.create_folder(folder_name, parent_path=parent_path)
            print(f"✅ Created missing '{created_path}' folder on startup")
        except Exception as creation_error:
            print(f"⚠️ Failed to create Reports folder automatically: {creation_error}")
    except Exception as error:
        print(f"⚠️ Could not verify Reports folder: {error}")
MAX_PARALLEL_UPLOADS = 20

# Application lifecycle events (using older event handlers for compatibility)
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    ensure_reports_folder_exists()

    if cleanup_available and start_cleanup_scheduler:
        try:
            start_cleanup_scheduler()
            print("✅ Cleanup scheduler started automatically on application startup")
        except Exception as e:
            print(f"⚠️ Warning: Could not start cleanup scheduler on startup: {str(e)}")

@app.on_event("shutdown")  
async def shutdown_event():
    """Application shutdown tasks"""
    if cleanup_available and stop_cleanup_scheduler:
        try:
            stop_cleanup_scheduler()
            print("✅ Cleanup scheduler stopped on application shutdown")
        except Exception as e:
            print(f"⚠️ Warning: Could not stop cleanup scheduler on shutdown: {str(e)}")

# Alternative lifespan approach for newer FastAPI versions (commented out for compatibility)
# from contextlib import asynccontextmanager
# 
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     if cleanup_available and start_cleanup_scheduler:
#         try:
#             start_cleanup_scheduler()
#             print("✅ Cleanup scheduler started automatically on application startup")
#         except Exception as e:
#             print(f"⚠️ Warning: Could not start cleanup scheduler on startup: {str(e)}")
#     
#     yield
#     
#     # Shutdown
#     if cleanup_available and stop_cleanup_scheduler:
#         try:
#             stop_cleanup_scheduler()
#             print("✅ Cleanup scheduler stopped on application shutdown")
#         except Exception as e:
#             print(f"⚠️ Warning: Could not stop cleanup scheduler on shutdown: {str(e)}")

# Pydantic models for chat and report endpoints
class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message")
    session_id: str = Field(..., description="Session ID for the chat")
    vector_store_id: Optional[str] = Field(None, description="Optional vector store ID (if not using session-managed store)")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant's response")
    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Number of messages in the session")

class ReportRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for the report")
    vector_store_id: Optional[str] = Field(None, description="Optional vector store ID (if not using session-managed store)")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    language: Optional[str] = Field(None, description="Optional language code for the generated report")

class ReportResponse(BaseModel):
    report: str = Field(..., description="Generated coaching report")
    session_id: str = Field(..., description="Session identifier")
    type: str = Field(default="report", description="Response type")

class VectorStoreRequest(BaseModel):
    folder_path: Optional[str] = Field(None, description="Path to folder for vector store")
    file_paths: Optional[List[str]] = Field(None, description="List of file paths for vector store")
    store_name: Optional[str] = Field(None, description="Optional custom name for vector store")

class VectorStoreResponse(BaseModel):
    vector_store_id: str = Field(..., description="Created vector store ID")
    message: str = Field(..., description="Success message")

class SessionResponse(BaseModel):
    sessions: List[Dict[str, Any]] = Field(..., description="List of chat sessions")

class SessionHistoryResponse(BaseModel):
    history: List[Dict[str, Any]] = Field(..., description="Chat history for session")

class SessionUpdateRequest(BaseModel):
    title: str = Field(..., description="New title for the session")


class StartChatSessionRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User identifier")
    folder_path: Optional[str] = Field(None, description="Path to folder for vector store")
    file_paths: Optional[List[str]] = Field(None, description="List of file paths for vector store")
    session_title: Optional[str] = Field(None, description="Optional title for the session")
    current_session_id: Optional[str] = Field(None, description="Current session ID to clean up before starting new session")


class StartChatSessionResponse(BaseModel):
    session_id: str = Field(..., description="Created session ID")
    vector_store_id: str = Field(..., description="Created vector store ID")
    message: str = Field(..., description="Success message")


class EndChatSessionRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to end")


class EndChatSessionResponse(BaseModel):
    message: str = Field(..., description="Success message")
    cleanup_status: Dict[str, Any] = Field(..., description="Detailed cleanup status")
    session_id: str = Field(..., description="Session identifier that was cleaned up")
    vector_store_id: Optional[str] = Field(None, description="Vector store ID that was cleaned up")
    messages_deleted: int = Field(0, description="Number of messages that were deleted")


@app.get("/", response_model=Dict[str, str], tags=["System"])
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "File Management API",
        "version": "1.0.0",
        "description": "Comprehensive file explorer for AWS S3"
    }


@app.post("/folders", response_model=Dict[str, str], tags=["File Management"])
async def create_folder(request: CreateFolderRequest):
    """
    Create a new folder in the specified path
    
    Args:
        request: Contains folder_name and optional parent_path
        
    Returns:
        Success message with created folder path
    """
    try:
        folder_path = file_manager.create_folder(
            folder_name=request.folder_name,
            parent_path=request.parent_path
        )
        return {
            "message": "Folder created successfully",
            "folder_path": folder_path
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/files/upload", response_model=UploadResponse, tags=["File Operations"])
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    path: Optional[str] = Form(None)
):
    """
    Upload a file to the specified path with enhanced error handling and timeout
    
    Args:
        file: The file to upload
        path: Optional destination path (defaults to root)
        
    Returns:
        Upload confirmation with file details
    """
    try:
        # Add file size validation
        if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            # Limit file size to prevent timeouts
            max_size = 500 * 1024 * 1024  # 500 MB
            if file_size > max_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File too large. Maximum size is {max_size // (1024*1024)} MB"
                )
        
        print(f"DEBUG: Upload file - path parameter: '{path}'")  # Debug logging
        file_info = await asyncio.wait_for(
            file_manager.upload_file(file, path),
            timeout=300.0  # 5 minute timeout
        )
        print(f"DEBUG: File uploaded to: '{file_info.path}'")  # Debug logging
        
        return UploadResponse(
            message="File uploaded successfully",
            file_info=file_info
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Upload timeout. Try uploading a smaller file.")
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        print(f"DEBUG: Upload error: {str(e)}")  # Debug logging
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await file.close()


@app.post("/files/upload-multiple", response_model=List[UploadResponse], tags=["File Operations"])
async def upload_multiple_files(
    files: List[UploadFile] = FastAPIFile(...),
    path: Optional[str] = Form(None)
):
    """
    Upload multiple files to the specified path
    
    Args:
        files: List of files to upload
        path: Optional destination path (defaults to root)
        
    Returns:
        List of upload confirmations
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    if len(files) > MAX_PARALLEL_UPLOADS:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upload more than {MAX_PARALLEL_UPLOADS} files at once."
        )

    semaphore = asyncio.Semaphore(MAX_PARALLEL_UPLOADS)

    async def upload_with_limit(upload_file: UploadFile) -> UploadResponse:
        async with semaphore:
            try:
                file_info = await file_manager.upload_file(upload_file, path)
                return UploadResponse(
                    message="File uploaded successfully",
                    file_info=file_info
                )
            finally:
                await upload_file.close()

    upload_tasks = [upload_with_limit(file) for file in files]
    results = await asyncio.gather(*upload_tasks, return_exceptions=True)

    responses: List[UploadResponse] = []
    errors = []

    for original_file, result in zip(files, results):
        if isinstance(result, Exception):
            if isinstance(result, HTTPException):
                error_message = result.detail
            else:
                error_message = str(result)
            errors.append({
                "file": original_file.filename or "unknown",
                "error": error_message
            })
        else:
            responses.append(result)

    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Failed to upload one or more files",
                "errors": errors
            }
        )

    return responses


@app.get("/files", response_model=FileListResponse, tags=["File Management"])
async def get_files(
    path: Optional[str] = None,
    include_hidden: bool = False,
    sort_by: str = "name",
    sort_order: str = "asc"
):
    """
    Get files and folders in the specified path
    
    Args:
        path: Optional folder path (defaults to root)
        include_hidden: Whether to include hidden files
        sort_by: Sort criteria (name, size, modified, type)
        sort_order: Sort order (asc, desc)
        
    Returns:
        List of files and folders with metadata
    """
    try:
        # Add performance optimization for file listing
        start_time = time.time()
        file_list = file_manager.get_files(
            path=path,
            include_hidden=include_hidden,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        process_time = time.time() - start_time
        if process_time > 1.0:
            logging.warning(f"Slow file listing: {path} took {process_time:.2f}s")
            
        return file_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/files/search", tags=["File Operations"])
async def search_files(
    query: str,
    path: Optional[str] = None,
    file_type: Optional[str] = None
):
    """
    Search for files and folders by name or pattern
    
    Args:
        query: Search query or pattern
        path: Optional path to search in (defaults to root)
        file_type: Optional file type filter
        
    Returns:
        List of matching files and folders
    """
    try:
        results = file_manager.search_files(
            query=query,
            path=path,
            file_type=file_type
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/files", tags=["File Management"])
async def delete_item(request: DeleteRequest):
    """
    Delete a file or folder
    
    Args:
        request: Contains path and optional recursive flag for folders
        
    Returns:
        Deletion confirmation
    """
    try:
        result = file_manager.delete_item(
            path=request.path,
            recursive=request.recursive
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/files/batch", tags=["File Operations"])
async def delete_multiple_items(paths: List[str], recursive: bool = False):
    """
    Delete multiple files or folders
    
    Args:
        paths: List of paths to delete
        recursive: Whether to delete folders recursively
        
    Returns:
        Batch deletion results
    """
    try:
        results = []
        for path in paths:
            result = file_manager.delete_item(path=path, recursive=recursive)
            results.append(result)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/files/download/{file_path:path}", tags=["File Operations"])
async def download_file(file_path: str):
    """
    Download a single file
    
    Args:
        file_path: Path to the file to download
        
    Returns:
        File content as streaming response
    """
    try:
        file_content, content_type, filename = file_manager.download_file(file_path)
        
        # Properly encode filename for Content-Disposition header
        encoded_filename = urllib.parse.quote(filename, safe='')
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/files/download-folder/{folder_path:path}", tags=["File Operations"])
async def download_folder(folder_path: str):
    """
    Download a folder as a ZIP archive
    
    Args:
        folder_path: Path to the folder to download
        
    Returns:
        ZIP archive containing folder contents
    """
    try:
        zip_content, folder_name = file_manager.download_folder(folder_path)
        
        # Properly encode filename for Content-Disposition header
        encoded_filename = urllib.parse.quote(f"{folder_name}.zip", safe='')
        
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/files/copy", tags=["File Operations"])
async def copy_file(source_path: str, destination_path: str):
    """
    Copy a file to a new location
    
    Args:
        source_path: Source file path
        destination_path: Destination file path
        
    Returns:
        Copy confirmation
    """
    try:
        result = file_manager.copy_file(source_path, destination_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/files/move", tags=["File Operations"])
async def move_file(source_path: str, destination_path: str):
    """
    Move a file to a new location
    
    Args:
        source_path: Source file path
        destination_path: Destination file path
        
    Returns:
        Move confirmation
    """
    try:
        result = file_manager.move_file(source_path, destination_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/files/info/{file_path:path}", tags=["File Management"])
async def get_file_info(file_path: str):
    """
    Get detailed information about a file or folder
    
    Args:
        file_path: Path to the file or folder
        
    Returns:
        Detailed file/folder information
    """
    try:
        info = file_manager.get_file_info(file_path)
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/files/preview/{file_path:path}", tags=["File Operations"])
async def preview_file(file_path: str, max_size: int = 1024*1024):  # 1MB default
    """
    Get a preview of file content (for text files)
    
    Args:
        file_path: Path to the file
        max_size: Maximum file size to preview
        
    Returns:
        File content preview
    """
    try:
        preview = file_manager.preview_file(file_path, max_size)
        return preview
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/storage/stats", tags=["Storage"])
async def get_storage_stats():
    """
    Get storage usage statistics
    
    Returns:
        Storage usage information
    """
    try:
        stats = file_manager.get_storage_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/files/analyze-image", tags=["File Operations"])
async def analyze_image_with_ai(
    file_path: str = Form(...),
    custom_prompt: Optional[str] = Form(None)
):
    """
    Analyze image using AI vision capabilities and OCR
    
    Args:
        file_path: Path to the image file to analyze
        custom_prompt: Optional custom analysis prompt
        
    Returns:
        AI analysis and extracted text from the image
    """
    try:
        # Download image
        content, content_type, filename = file_manager.download_file(file_path)
        
        # Check if it's an image
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File is not an image")
        
        # Import image processor and get OpenAI client
        from backend.files.image_processor import ImageProcessor
        
        try:
            from backend.assistant.utils import get_openai_client
            client = get_openai_client()
            
            # Analyze with AI Vision (if client available)
            try:
                ai_analysis = ImageProcessor.analyze_with_openai_vision(
                    content, client, custom_prompt
                )
            except Exception as vision_error:
                logging.warning(f"AI vision analysis failed: {vision_error}")
                ai_analysis = "AI vision analysis not available"
        except ImportError:
            ai_analysis = "AI vision analysis not available (OpenAI client not configured)"
        
        # Extract text with OCR
        ocr_text = ImageProcessor.extract_text_from_image(content)
        
        # Get image metadata
        image_info = ImageProcessor.get_image_info(content)
        
        return {
            "filename": filename,
            "file_path": file_path,
            "ai_analysis": ai_analysis,
            "extracted_text": ocr_text,
            "image_info": image_info,
            "analysis_type": "comprehensive"
        }
        
    except Exception as e:
        logging.error(f"Image analysis error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/files/debug-ocr", tags=["File Operations"])
async def debug_ocr_processing(
    file_path: str = Form(...),
    save_debug_images: bool = Form(False)
):
    """
    Debug OCR processing to understand why accuracy might be low
    
    Args:
        file_path: Path to the image file to debug
        save_debug_images: Whether to save intermediate processing images
        
    Returns:
        Detailed OCR analysis with different preprocessing methods
    """
    try:
        # Download image
        content, content_type, filename = file_manager.download_file(file_path)
        
        # Check if it's an image
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File is not an image")
        
        from backend.files.image_processor import ImageProcessor
        
        if save_debug_images:
            # Debug with image saving
            debug_results = ImageProcessor.debug_ocr_preprocessing(content)
            
            return {
                "filename": filename,
                "file_path": file_path,
                "debug_results": debug_results,
                "message": "Debug images saved to /tmp/ocr_debug/ for inspection"
            }
        else:
            # Just run OCR analysis without saving images
            ocr_text = ImageProcessor.extract_text_from_image(content)
            image_info = ImageProcessor.get_image_info(content)
            
            return {
                "filename": filename,
                "file_path": file_path,
                "extracted_text": ocr_text,
                "image_info": image_info,
                "text_length": len(ocr_text),
                "suggestions": [
                    "Try with save_debug_images=true to see preprocessing steps",
                    "Check if image resolution is sufficient (>300 DPI recommended)",
                    "Ensure text is horizontal and not rotated",
                    "Verify image has good contrast between text and background"
                ]
            }
        
    except Exception as e:
        logging.error(f"OCR debug error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Chat and Report endpoints

@app.post("/chat", response_model=ChatResponse, tags=["AI Chat"])
async def chat(request: ChatRequest):
    """
    Generate a chat response using the assistant
    
    Args:
        request: Chat request with message and session_id
        
    Returns:
        Chat response with assistant's reply and session information
    """
    if generate_chat_response is None or get_session_vector_store is None:
        raise HTTPException(status_code=500, detail="Chat functionality not available")
    
    try:
        # Get vector store from session if not provided
        vector_store_id = request.vector_store_id
        if not vector_store_id:
            vector_store_id = get_session_vector_store(request.session_id)
            if not vector_store_id:
                raise HTTPException(status_code=400, detail="No vector store found for session. Please start a chat session first.")
        
        result = generate_chat_response(
            message=request.message,
            vector_store_id=vector_store_id,
            session_id=request.session_id,
            user_id=request.user_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/report", response_model=ReportResponse, tags=["AI Reports"])
async def generate_coaching_report(request: ReportRequest):
    """
    Generate a coaching report based on client documents
    
    Args:
        request: Report request with session_id
        
    Returns:
        Generated coaching report
    """
    if generate_report is None or get_session_vector_store is None:
        raise HTTPException(status_code=500, detail="Report functionality not available")
    
    try:
        # Get vector store from session if not provided
        vector_store_id = request.vector_store_id
        if not vector_store_id:
            vector_store_id = get_session_vector_store(request.session_id)
            if not vector_store_id:
                raise HTTPException(status_code=400, detail="No vector store found for session. Please start a chat session first.")
        
        result = generate_report(
            vector_store_id=vector_store_id,
            session_id=request.session_id,
            user_id=request.user_id,
            language=request.language
        )
        return ReportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Vector Store Management endpoints

@app.post("/vector-stores", response_model=VectorStoreResponse, tags=["Vector Stores"])
async def create_vector_store(request: VectorStoreRequest):
    """
    Create a new vector store from files or folder
    
    Args:
        request: Vector store creation request with either folder_path or file_paths
        
    Returns:
        Vector store ID and confirmation message
    """
    if create_vector_store_from_folder is None or create_vector_store_from_file_list is None:
        raise HTTPException(status_code=500, detail="Vector store functionality not available")
    
    try:
        if request.folder_path and request.file_paths:
            raise HTTPException(status_code=400, detail="Provide either folder_path or file_paths, not both")
        
        if not request.folder_path and not request.file_paths:
            raise HTTPException(status_code=400, detail="Either folder_path or file_paths must be provided")
        
        if request.folder_path:
            vector_store_id = create_vector_store_from_folder(
                folder_path=request.folder_path,
                store_name=request.store_name
            )
        else:
            vector_store_id = create_vector_store_from_file_list(
                file_paths=request.file_paths,
                store_name=request.store_name
            )
        
        return VectorStoreResponse(
            vector_store_id=vector_store_id,
            message="Vector store created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/vector-stores/{vector_store_id}", tags=["Vector Stores"])
async def delete_vector_store(vector_store_id: str):
    """
    Delete a vector store
    
    Args:
        vector_store_id: ID of the vector store to delete
        
    Returns:
        Deletion confirmation
    """
    if remove_vector_store is None:
        raise HTTPException(status_code=500, detail="Vector store functionality not available")
    
    try:
        success = remove_vector_store(vector_store_id)
        if success:
            return {"message": "Vector store deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Vector store not found or could not be deleted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Session Management endpoints

@app.get("/sessions", response_model=SessionResponse, tags=["Session Management"])
async def get_user_sessions(user_id: str, limit: int = 50):
    """
    Get all chat sessions for a user
    
    Args:
        user_id: User identifier
        limit: Maximum number of sessions to return
        
    Returns:
        List of user's chat sessions
    """
    if get_chat_sessions is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        sessions = get_chat_sessions(user_id, limit)
        return SessionResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse, tags=["Session Management"])
async def get_session_history(session_id: str):
    """
    Get chat history for a session (excluding report messages)
    
    Args:
        session_id: Session identifier
        
    Returns:
        Chat history for the session (reports excluded)
    """
    if get_chat_history is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        history = get_chat_history(session_id)
        return SessionHistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/sessions/{session_id}/reports", response_model=SessionHistoryResponse, tags=["Session Management"])
async def get_session_reports_endpoint(session_id: str):
    """
    Get all report messages for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        All report messages for the session
    """
    if get_session_reports is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        reports = get_session_reports(session_id)
        return SessionHistoryResponse(history=reports)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/sessions/{session_id}", tags=["Session Management"])
async def delete_session(session_id: str):
    """
    Delete a chat session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Deletion confirmation
    """
    if delete_chat_session is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        success = delete_chat_session(session_id)
        if success:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/sessions/{session_id}/title", tags=["Session Management"])
async def update_session_title_endpoint(session_id: str, request: SessionUpdateRequest):
    """
    Update a session's title
    
    Args:
        session_id: Session identifier
        request: Request with new title
        
    Returns:
        Update confirmation
    """
    if update_session_title is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        success = update_session_title(session_id, request.title)
        if success:
            return {"message": "Session title updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found or could not be updated")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/sessions/start", response_model=StartChatSessionResponse, tags=["Session Management"])
async def start_chat_session_endpoint(request: StartChatSessionRequest):
    """
    Start a new chat session with automatic vector store creation
    
    Args:
        request: Session start request with files/folder and optional session info
        
    Returns:
        Session and vector store details
    """
    if start_chat_session is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        # Clean up current session if provided (for folder switching)
        if request.current_session_id and end_chat_session is not None:
            try:
                cleanup_result = end_chat_session(request.current_session_id)
                print(f"✅ Cleaned up previous session: {request.current_session_id}")
            except Exception as cleanup_error:
                print(f"⚠️ Warning: Could not fully clean up previous session {request.current_session_id}: {cleanup_error}")
                # Continue with new session creation even if cleanup fails
        
        if request.folder_path and request.file_paths:
            raise HTTPException(status_code=400, detail="Provide either folder_path or file_paths, not both")
        
        if not request.folder_path and not request.file_paths:
            raise HTTPException(status_code=400, detail="Either folder_path or file_paths must be provided")
        
        result = start_chat_session(
            user_id=request.user_id,
            folder_path=request.folder_path,
            file_paths=request.file_paths,
            session_title=request.session_title
        )
        return StartChatSessionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/sessions/end", response_model=EndChatSessionResponse, tags=["Session Management"])
async def end_chat_session_endpoint(request: EndChatSessionRequest):
    """
    End a chat session and clean up vector store
    
    Args:
        request: Session end request with session_id
        
    Returns:
        End session confirmation
    """
    if end_chat_session is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        result = end_chat_session(request.session_id)
        return EndChatSessionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/sessions/switch-folder", response_model=StartChatSessionResponse, tags=["Session Management"])
async def switch_folder_session(request: StartChatSessionRequest):
    """
    Switch to a new folder by ending current session and starting new one
    
    This endpoint properly cleans up the current session (including vector store and OpenAI files)
    before starting a new session with the selected folder.
    
    Args:
        request: Session switch request with new folder and current session info
        
    Returns:
        New session and vector store details
    """
    if start_chat_session is None or end_chat_session is None:
        raise HTTPException(status_code=500, detail="Session functionality not available")
    
    try:
        # Clean up current session if provided
        if request.current_session_id:
            try:
                cleanup_result = end_chat_session(request.current_session_id)
                print(f"✅ Cleaned up previous session: {request.current_session_id}")
                print(f"Cleanup details: {cleanup_result}")
            except Exception as cleanup_error:
                print(f"⚠️ Warning: Could not fully clean up previous session {request.current_session_id}: {cleanup_error}")
                # Continue with new session creation even if cleanup fails
        
        # Validate folder/file requirements
        if request.folder_path and request.file_paths:
            raise HTTPException(status_code=400, detail="Provide either folder_path or file_paths, not both")
        
        if not request.folder_path and not request.file_paths:
            raise HTTPException(status_code=400, detail="Either folder_path or file_paths must be provided")
        
        # Start new session
        result = start_chat_session(
            user_id=request.user_id,
            folder_path=request.folder_path,
            file_paths=request.file_paths,
            session_title=request.session_title
        )
        
        print(f"✅ Started new session: {result['session_id']} for folder: {request.folder_path}")
        return StartChatSessionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to switch folder session: {str(e)}")


@app.post("/sessions/cleanup-orphaned", tags=["Session Management"])
async def cleanup_orphaned_resources_endpoint():
    """
    Clean up orphaned resources (sessions without vector stores, vector stores without sessions)
    
    Returns:
        Cleanup statistics and results
    """
    if cleanup_orphaned_resources is None:
        raise HTTPException(status_code=500, detail="Cleanup functionality not available")
    
    try:
        result = cleanup_orphaned_resources()
        return {
            "message": "Orphaned resources cleanup completed",
            "cleanup_stats": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/sessions/{session_id}/force-cleanup", tags=["Session Management"])
async def force_cleanup_session_endpoint(session_id: str):
    """
    Force cleanup of a session even if partially deleted or corrupted
    
    Args:
        session_id: Session identifier to force cleanup
        
    Returns:
        Force cleanup results
    """
    if force_cleanup_session is None:
        raise HTTPException(status_code=500, detail="Cleanup functionality not available")
    
    try:
        result = force_cleanup_session(session_id)
        return {
            "message": f"Force cleanup completed for session {session_id}",
            "cleanup_results": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/system/cleanup/start-scheduler", tags=["System Maintenance"])
async def start_cleanup_scheduler_endpoint():
    """
    Start the automatic cleanup scheduler for background maintenance
    
    Returns:
        Scheduler start confirmation
    """
    if not cleanup_available or start_cleanup_scheduler is None:
        raise HTTPException(status_code=500, detail="Cleanup scheduler not available")
    
    try:
        start_cleanup_scheduler()
        return {
            "message": "Cleanup scheduler started successfully",
            "status": "running"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/system/cleanup/stop-scheduler", tags=["System Maintenance"])
async def stop_cleanup_scheduler_endpoint():
    """
    Stop the automatic cleanup scheduler
    
    Returns:
        Scheduler stop confirmation
    """
    if not cleanup_available or stop_cleanup_scheduler is None:
        raise HTTPException(status_code=500, detail="Cleanup scheduler not available")
    
    try:
        stop_cleanup_scheduler()
        return {
            "message": "Cleanup scheduler stopped successfully",
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/system/cleanup/manual", tags=["System Maintenance"])
async def manual_cleanup_endpoint():
    """
    Manually trigger a comprehensive system cleanup
    
    Returns:
        Cleanup results and statistics
    """
    if not cleanup_available or manual_cleanup is None:
        raise HTTPException(status_code=500, detail="Manual cleanup not available")
    
    try:
        result = manual_cleanup()
        return {
            "message": "Manual cleanup completed",
            "cleanup_results": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/system/cleanup/status", tags=["System Maintenance"])
async def cleanup_scheduler_status():
    """
    Get the current status of the cleanup scheduler
    
    Returns:
        Current scheduler status and statistics
    """
    if not cleanup_available or cleanup_scheduler is None:
        raise HTTPException(status_code=500, detail="Cleanup scheduler not available")
    
    try:
        return {
            "scheduler_running": cleanup_scheduler.running,
            "message": "Cleanup scheduler is running" if cleanup_scheduler.running else "Cleanup scheduler is stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)