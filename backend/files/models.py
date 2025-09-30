"""
Pydantic models for file management API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any, Dict
from datetime import datetime


class FileInfo(BaseModel):
    """Information about a file"""
    name: str = Field(..., description="Name of the file")
    path: str = Field(..., description="Full path to the file")
    size: int = Field(0, description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    extension: str = Field("", description="File extension")
    is_folder: bool = Field(False, description="Whether this is a folder")
    modified: datetime = Field(default_factory=datetime.now, description="Last modified timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FolderInfo(BaseModel):
    """Information about a folder"""
    name: str = Field(..., description="Name of the folder")
    path: str = Field(..., description="Full path to the folder")
    is_folder: bool = Field(True, description="Always True for folders")
    modified: datetime = Field(default_factory=datetime.now, description="Last modified timestamp")
    item_count: Optional[int] = Field(None, description="Number of items in the folder")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CreateFolderRequest(BaseModel):
    """Request model for creating a folder"""
    folder_name: str = Field(..., description="Name of the folder to create", min_length=1)
    parent_path: Optional[str] = Field(None, description="Parent directory path (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "folder_name": "my_documents",
                "parent_path": "projects/2024"
            }
        }


class DeleteRequest(BaseModel):
    """Request model for deleting files or folders"""
    path: str = Field(..., description="Path to the file or folder to delete")
    recursive: bool = Field(False, description="Whether to delete folders recursively")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "documents/old_files",
                "recursive": True
            }
        }


class UploadResponse(BaseModel):
    """Response model for file uploads"""
    message: str = Field(..., description="Upload status message")
    file_info: FileInfo = Field(..., description="Information about the uploaded file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "File uploaded successfully",
                "file_info": {
                    "name": "document.pdf",
                    "path": "uploads/document.pdf",
                    "size": 1024000,
                    "content_type": "application/pdf",
                    "extension": ".pdf",
                    "is_folder": False,
                    "modified": "2024-01-01T12:00:00"
                }
            }
        }


class FileListResponse(BaseModel):
    """Response model for file listing"""
    path: str = Field(..., description="Current directory path")
    files: List[Union[FileInfo, FolderInfo]] = Field(..., description="List of files and folders")
    total_count: int = Field(..., description="Total number of items")
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "documents",
                "files": [
                    {
                        "name": "subfolder",
                        "path": "documents/subfolder",
                        "is_folder": True,
                        "modified": "2024-01-01T12:00:00"
                    },
                    {
                        "name": "report.pdf",
                        "path": "documents/report.pdf",
                        "size": 2048000,
                        "content_type": "application/pdf",
                        "extension": ".pdf",
                        "is_folder": False,
                        "modified": "2024-01-01T12:00:00"
                    }
                ],
                "total_count": 2
            }
        }


class SearchRequest(BaseModel):
    """Request model for file search"""
    query: str = Field(..., description="Search query or pattern", min_length=1)
    path: Optional[str] = Field(None, description="Path to search in (optional)")
    file_type: Optional[str] = Field(None, description="File type filter (optional)")
    case_sensitive: bool = Field(False, description="Whether search is case sensitive")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "report",
                "path": "documents/2024",
                "file_type": "pdf",
                "case_sensitive": False
            }
        }


class SearchResponse(BaseModel):
    """Response model for file search"""
    query: str = Field(..., description="Search query used")
    results: List[Union[FileInfo, FolderInfo]] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_path: Optional[str] = Field(None, description="Path searched in")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "report",
                "results": [
                    {
                        "name": "annual_report.pdf",
                        "path": "documents/2024/annual_report.pdf",
                        "size": 3072000,
                        "content_type": "application/pdf",
                        "extension": ".pdf",
                        "is_folder": False,
                        "modified": "2024-01-01T12:00:00"
                    }
                ],
                "total_results": 1,
                "search_path": "documents/2024"
            }
        }


class CopyMoveRequest(BaseModel):
    """Request model for copy/move operations"""
    source_path: str = Field(..., description="Source file or folder path")
    destination_path: str = Field(..., description="Destination path")
    overwrite: bool = Field(False, description="Whether to overwrite existing files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_path": "documents/old_location/file.txt",
                "destination_path": "documents/new_location/file.txt",
                "overwrite": False
            }
        }


class BatchOperationRequest(BaseModel):
    """Request model for batch operations"""
    paths: List[str] = Field(..., description="List of paths to operate on", min_items=1)
    operation: str = Field(..., description="Operation to perform", pattern="^(delete|copy|move)$")
    destination_path: Optional[str] = Field(None, description="Destination path for copy/move operations")
    recursive: bool = Field(False, description="Whether to operate recursively on folders")
    
    class Config:
        json_schema_extra = {
            "example": {
                "paths": ["file1.txt", "file2.txt", "folder1"],
                "operation": "delete",
                "recursive": True
            }
        }


class BatchOperationResponse(BaseModel):
    """Response model for batch operations"""
    operation: str = Field(..., description="Operation performed")
    results: List[Dict[str, Any]] = Field(..., description="Results for each path")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "delete",
                "results": [
                    {"path": "file1.txt", "status": "success", "message": "File deleted successfully"},
                    {"path": "file2.txt", "status": "error", "message": "File not found"}
                ],
                "success_count": 1,
                "error_count": 1
            }
        }


class StorageStats(BaseModel):
    """Storage usage statistics"""
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size in bytes")
    total_size_mb: float = Field(..., description="Total size in megabytes")
    file_types: Dict[str, int] = Field(..., description="Count of files by type")
    most_common_type: Optional[str] = Field(None, description="Most common file type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 150,
                "total_size": 104857600,
                "total_size_mb": 100.0,
                "file_types": {
                    ".pdf": 45,
                    ".jpg": 30,
                    ".txt": 25,
                    ".docx": 20,
                    "no_extension": 30
                },
                "most_common_type": ".pdf"
            }
        }


class PreviewResponse(BaseModel):
    """Response model for file preview"""
    content: Optional[str] = Field(None, description="File content (for text files)")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    truncated: bool = Field(False, description="Whether content was truncated")
    preview_size: Optional[int] = Field(None, description="Size of preview content")
    error: Optional[str] = Field(None, description="Error message if preview not available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is the beginning of the text file...",
                "content_type": "text/plain",
                "size": 5000,
                "truncated": True,
                "preview_size": 1000
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }