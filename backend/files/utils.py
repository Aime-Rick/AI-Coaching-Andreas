"""
Utility functions for file management with Replit App Storage
"""

from replit.object_storage import Client
from replit.object_storage.errors import ObjectNotFoundError, BucketNotFoundError
from fastapi import UploadFile, HTTPException
from typing import List, Optional, Dict, Any, Tuple
import os
import tempfile
import zipfile
import io
from pathlib import Path
import mimetypes
from datetime import datetime
import re

from .models import FileInfo, FolderInfo, FileListResponse


class FileManager:
    """Main file management class for Replit App Storage operations"""
    
    def __init__(self, bucket_id: Optional[str] = None):
        """
        Initialize the file manager with Replit App Storage client
        
        Args:
            bucket_id: Optional bucket ID, uses default if not provided
        """
        try:
            self.client = Client(bucket_id=bucket_id)
        except Exception as e:
            raise Exception(f"Failed to initialize Replit App Storage client: {str(e)}")
    
    def _normalize_path(self, path: Optional[str]) -> str:
        """
        Normalize file path for consistent handling
        
        Args:
            path: Input path
            
        Returns:
            Normalized path
        """
        if not path:
            return ""
        
        # Remove leading slashes and normalize
        path = path.strip().lstrip("/")
        
        # Ensure folder paths end with /
        return path
    
    def _get_parent_path(self, path: str) -> str:
        """
        Get parent directory path
        
        Args:
            path: File or folder path
            
        Returns:
            Parent directory path
        """
        if "/" not in path:
            return ""
        return "/".join(path.split("/")[:-1])
    
    def _get_filename(self, path: str) -> str:
        """
        Extract filename from path
        
        Args:
            path: File path
            
        Returns:
            Filename
        """
        return path.split("/")[-1]
    
    def _get_file_extension(self, filename: str) -> str:
        """
        Get file extension
        
        Args:
            filename: Name of the file
            
        Returns:
            File extension
        """
        return Path(filename).suffix.lower()
    
    def _get_content_type(self, filename: str) -> str:
        """
        Determine content type from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            MIME content type
        """
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"
    
    def _is_text_file(self, filename: str) -> bool:
        """
        Check if file is a text file based on extension
        
        Args:
            filename: Name of the file
            
        Returns:
            True if text file, False otherwise
        """
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml',
            '.yml', '.yaml', '.csv', '.sql', '.log', '.ini', '.cfg', '.conf'
        }
        return self._get_file_extension(filename) in text_extensions
    
    def create_folder(self, folder_name: str, parent_path: Optional[str] = None) -> str:
        """
        Create a new folder
        
        Args:
            folder_name: Name of the folder to create
            parent_path: Optional parent directory path
            
        Returns:
            Full path of created folder
        """
        # Validate folder name
        if not folder_name or folder_name.strip() == "":
            raise ValueError("Folder name cannot be empty")
        
        # Check for invalid characters
        invalid_chars = '<>:"|?*'
        if any(char in folder_name for char in invalid_chars):
            raise ValueError(f"Folder name contains invalid characters: {invalid_chars}")
        
        # Normalize paths
        parent_path = self._normalize_path(parent_path)
        folder_name = folder_name.strip()
        
        # Construct full folder path
        if parent_path:
            folder_path = f"{parent_path}/{folder_name}/"
        else:
            folder_path = f"{folder_name}/"
        
        # Check if folder already exists
        try:
            objects = self.client.list(prefix=folder_path, max_results=1)
            if objects:
                raise ValueError(f"Folder already exists: {folder_path}")
        except Exception:
            pass  # Folder doesn't exist, which is what we want
        
        # Create folder by uploading a placeholder file
        placeholder_path = f"{folder_path}.folder_placeholder"
        try:
            self.client.upload_from_text(placeholder_path, "")
            return folder_path.rstrip("/")
        except Exception as e:
            raise Exception(f"Failed to create folder: {str(e)}")
    
    async def upload_file(self, file: UploadFile, path: Optional[str] = None) -> FileInfo:
        """
        Upload a file to the specified path
        
        Args:
            file: File to upload
            path: Optional destination path
            
        Returns:
            FileInfo object with upload details
        """
        if not file.filename:
            raise ValueError("File must have a filename")
        
        # Normalize path
        path = self._normalize_path(path)
        
        # Construct full file path
        if path:
            file_path = f"{path}/{file.filename}"
        else:
            file_path = file.filename
        
        try:
            # Read file content
            content = await file.read()
            
            # Upload to Replit App Storage
            self.client.upload_from_bytes(file_path, content)
            
            # Reset file pointer for any additional operations
            await file.seek(0)
            
            # Return file info
            return FileInfo(
                name=file.filename,
                path=file_path,
                size=len(content),
                content_type=self._get_content_type(file.filename),
                extension=self._get_file_extension(file.filename),
                is_folder=False,
                modified=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def get_files(
        self, 
        path: Optional[str] = None, 
        include_hidden: bool = False,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> FileListResponse:
        """
        Get files and folders in the specified path
        
        Args:
            path: Optional folder path
            include_hidden: Whether to include hidden files
            sort_by: Sort criteria
            sort_order: Sort order
            
        Returns:
            FileListResponse with files and folders
        """
        path = self._normalize_path(path)
        
        try:
            # List objects with prefix
            prefix = f"{path}/" if path else ""
            objects = self.client.list(prefix=prefix)
            
            files = []
            folders = set()
            
            for obj in objects:
                # Skip placeholder files
                if obj.name.endswith('.folder_placeholder'):
                    continue
                
                # Remove prefix from object name
                relative_path = obj.name[len(prefix):] if prefix else obj.name
                
                # Skip hidden files if not requested
                if not include_hidden and relative_path.startswith('.'):
                    continue
                
                # Check if this is a direct child or nested
                if "/" in relative_path:
                    # This is a nested item, add its parent folder
                    folder_name = relative_path.split("/")[0]
                    folders.add(folder_name)
                else:
                    # This is a direct file
                    files.append(FileInfo(
                        name=relative_path,
                        path=obj.name,
                        size=getattr(obj, 'size', 0),
                        content_type=self._get_content_type(relative_path),
                        extension=self._get_file_extension(relative_path),
                        is_folder=False,
                        modified=getattr(obj, 'updated', datetime.now())
                    ))
            
            # Add folder info
            for folder_name in folders:
                folder_path = f"{prefix}{folder_name}" if prefix else folder_name
                files.append(FolderInfo(
                    name=folder_name,
                    path=folder_path,
                    is_folder=True,
                    modified=datetime.now()
                ))
            
            # Sort files
            if sort_by == "name":
                files.sort(key=lambda x: x.name.lower(), reverse=(sort_order == "desc"))
            elif sort_by == "size":
                files.sort(key=lambda x: getattr(x, 'size', 0), reverse=(sort_order == "desc"))
            elif sort_by == "modified":
                files.sort(key=lambda x: x.modified, reverse=(sort_order == "desc"))
            elif sort_by == "type":
                files.sort(key=lambda x: (not x.is_folder, x.name.lower()), reverse=(sort_order == "desc"))
            
            return FileListResponse(
                path=path or "/",
                files=files,
                total_count=len(files)
            )
            
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")
    
    def search_files(
        self, 
        query: str, 
        path: Optional[str] = None, 
        file_type: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Search for files matching the query
        
        Args:
            query: Search query or pattern
            path: Optional search path
            file_type: Optional file type filter
            
        Returns:
            List of matching files
        """
        try:
            # Get all files in the specified path
            file_list = self.get_files(path=path, include_hidden=True)
            
            # Filter based on query
            results = []
            query_lower = query.lower()
            
            for file_info in file_list.files:
                # Skip folders if searching for specific file type
                if file_type and file_info.is_folder:
                    continue
                
                # Check name match
                name_match = query_lower in file_info.name.lower()
                
                # Check file type match
                type_match = True
                if file_type and not file_info.is_folder:
                    type_match = file_info.extension.lower() == f".{file_type.lower()}"
                
                if name_match and type_match:
                    results.append(file_info)
            
            return results
            
        except Exception as e:
            raise Exception(f"Failed to search files: {str(e)}")
    
    def delete_item(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Delete a file or folder
        
        Args:
            path: Path to delete
            recursive: Whether to delete folders recursively
            
        Returns:
            Deletion result
        """
        path = self._normalize_path(path)
        
        try:
            # Check if it's a folder by listing with prefix
            objects = self.client.list(prefix=f"{path}/", max_results=1)
            is_folder = bool(objects) or self.client.exists(f"{path}/.folder_placeholder")
            
            if is_folder:
                if not recursive:
                    # Check if folder is empty
                    folder_objects = self.client.list(prefix=f"{path}/")
                    non_placeholder_objects = [
                        obj for obj in folder_objects 
                        if not obj.name.endswith('.folder_placeholder')
                    ]
                    if non_placeholder_objects:
                        raise ValueError("Cannot delete non-empty folder without recursive flag")
                
                # Delete all objects in the folder
                all_objects = self.client.list(prefix=f"{path}/")
                deleted_count = 0
                for obj in all_objects:
                    self.client.delete(obj.name, ignore_not_found=True)
                    deleted_count += 1
                
                # Also try to delete the folder placeholder
                self.client.delete(f"{path}/.folder_placeholder", ignore_not_found=True)
                
                return {
                    "message": f"Folder deleted successfully",
                    "path": path,
                    "type": "folder",
                    "deleted_items": deleted_count
                }
            else:
                # Delete single file
                self.client.delete(path)
                return {
                    "message": "File deleted successfully",
                    "path": path,
                    "type": "file"
                }
                
        except ObjectNotFoundError:
            raise HTTPException(status_code=404, detail=f"File or folder not found: {path}")
        except Exception as e:
            raise Exception(f"Failed to delete item: {str(e)}")
    
    def download_file(self, file_path: str) -> Tuple[bytes, str, str]:
        """
        Download a single file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (file_content, content_type, filename)
        """
        file_path = self._normalize_path(file_path)
        
        try:
            # Download file content
            content = self.client.download_as_bytes(file_path)
            filename = self._get_filename(file_path)
            content_type = self._get_content_type(filename)
            
            return content, content_type, filename
            
        except ObjectNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    def download_folder(self, folder_path: str) -> Tuple[bytes, str]:
        """
        Download a folder as ZIP archive
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            Tuple of (zip_content, folder_name)
        """
        folder_path = self._normalize_path(folder_path)
        
        try:
            # List all objects in the folder
            objects = self.client.list(prefix=f"{folder_path}/")
            
            if not objects:
                raise HTTPException(status_code=404, detail=f"Folder not found or empty: {folder_path}")
            
            # Create ZIP archive in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for obj in objects:
                    # Skip placeholder files
                    if obj.name.endswith('.folder_placeholder'):
                        continue
                    
                    # Download file content
                    content = self.client.download_as_bytes(obj.name)
                    
                    # Add to ZIP with relative path
                    relative_path = obj.name[len(folder_path)+1:]
                    zip_file.writestr(relative_path, content)
            
            zip_buffer.seek(0)
            folder_name = self._get_filename(folder_path) or "download"
            
            return zip_buffer.getvalue(), folder_name
            
        except Exception as e:
            raise Exception(f"Failed to download folder: {str(e)}")
    
    def copy_file(self, source_path: str, destination_path: str) -> Dict[str, str]:
        """
        Copy a file to a new location
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            Copy result
        """
        source_path = self._normalize_path(source_path)
        destination_path = self._normalize_path(destination_path)
        
        try:
            self.client.copy(source_path, destination_path)
            return {
                "message": "File copied successfully",
                "source": source_path,
                "destination": destination_path
            }
        except ObjectNotFoundError:
            raise HTTPException(status_code=404, detail=f"Source file not found: {source_path}")
        except Exception as e:
            raise Exception(f"Failed to copy file: {str(e)}")
    
    def move_file(self, source_path: str, destination_path: str) -> Dict[str, str]:
        """
        Move a file to a new location
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            Move result
        """
        # Copy then delete
        copy_result = self.copy_file(source_path, destination_path)
        self.delete_item(source_path)
        
        return {
            "message": "File moved successfully",
            "source": source_path,
            "destination": destination_path
        }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information
        """
        file_path = self._normalize_path(file_path)
        
        try:
            # Check if file exists
            if not self.client.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            
            # Get file info (basic implementation)
            filename = self._get_filename(file_path)
            
            return {
                "name": filename,
                "path": file_path,
                "extension": self._get_file_extension(filename),
                "content_type": self._get_content_type(filename),
                "is_text": self._is_text_file(filename),
                "parent_path": self._get_parent_path(file_path)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get file info: {str(e)}")
    
    def preview_file(self, file_path: str, max_size: int = 1024*1024) -> Dict[str, Any]:
        """
        Get a preview of file content
        
        Args:
            file_path: Path to the file
            max_size: Maximum file size to preview
            
        Returns:
            File preview
        """
        file_path = self._normalize_path(file_path)
        
        try:
            filename = self._get_filename(file_path)
            
            # Check if it's a text file
            if not self._is_text_file(filename):
                return {
                    "error": "Preview not available for this file type",
                    "content_type": self._get_content_type(filename)
                }
            
            # Download and check size
            content = self.client.download_as_bytes(file_path)
            
            if len(content) > max_size:
                # Return truncated content
                text_content = content[:max_size].decode('utf-8', errors='ignore')
                return {
                    "content": text_content,
                    "truncated": True,
                    "size": len(content),
                    "preview_size": len(text_content)
                }
            else:
                # Return full content
                text_content = content.decode('utf-8', errors='ignore')
                return {
                    "content": text_content,
                    "truncated": False,
                    "size": len(content)
                }
                
        except ObjectNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Failed to preview file: {str(e)}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics
        
        Returns:
            Storage statistics
        """
        try:
            # List all objects to calculate stats
            all_objects = self.client.list()
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            for obj in all_objects:
                # Skip placeholder files
                if obj.name.endswith('.folder_placeholder'):
                    continue
                
                total_files += 1
                size = getattr(obj, 'size', 0)
                total_size += size
                
                # Count file types
                extension = self._get_file_extension(obj.name)
                if extension:
                    file_types[extension] = file_types.get(extension, 0) + 1
                else:
                    file_types['no_extension'] = file_types.get('no_extension', 0) + 1
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024*1024), 2),
                "file_types": file_types,
                "most_common_type": max(file_types.items(), key=lambda x: x[1])[0] if file_types else None
            }
            
        except Exception as e:
            raise Exception(f"Failed to get storage stats: {str(e)}")