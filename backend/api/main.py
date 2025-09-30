"""
File Management System for Replit App Storage
Provides comprehensive file and folder management capabilities.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import os
import tempfile
import zipfile
import io
from pathlib import Path
import mimetypes

from files.utils import FileManager
from files.models import (
    FileInfo, 
    FolderInfo, 
    CreateFolderRequest, 
    FileListResponse,
    DeleteRequest,
    UploadResponse
)

app = FastAPI(title="File Management API", description="Comprehensive file explorer for Replit App Storage")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize file manager
file_manager = FileManager()


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "File Management API",
        "version": "1.0.0",
        "description": "Comprehensive file explorer for Replit App Storage"
    }


@app.post("/folders", response_model=Dict[str, str])
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


@app.post("/files/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    path: Optional[str] = None
):
    """
    Upload a file to the specified path
    
    Args:
        file: The file to upload
        path: Optional destination path (defaults to root)
        
    Returns:
        Upload confirmation with file details
    """
    try:
        file_info = await file_manager.upload_file(file, path)
        return UploadResponse(
            message="File uploaded successfully",
            file_info=file_info
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/files/upload-multiple", response_model=List[UploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = FastAPIFile(...),
    path: Optional[str] = None
):
    """
    Upload multiple files to the specified path
    
    Args:
        files: List of files to upload
        path: Optional destination path (defaults to root)
        
    Returns:
        List of upload confirmations
    """
    try:
        results = []
        for file in files:
            file_info = await file_manager.upload_file(file, path)
            results.append(UploadResponse(
                message="File uploaded successfully",
                file_info=file_info
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/files", response_model=FileListResponse)
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
        file_list = file_manager.get_files(
            path=path,
            include_hidden=include_hidden,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return file_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/files/search")
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


@app.delete("/files")
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


@app.delete("/files/batch")
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


@app.get("/files/download/{file_path:path}")
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
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/files/download-folder/{folder_path:path}")
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
        
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={folder_name}.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/files/copy")
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


@app.post("/files/move")
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


@app.get("/files/info/{file_path:path}")
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


@app.get("/files/preview/{file_path:path}")
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


@app.get("/storage/stats")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)