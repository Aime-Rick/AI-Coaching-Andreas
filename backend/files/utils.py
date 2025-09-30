"""
Utility functions for file management with AWS S3
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
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
    """Main file management class for AWS S3 operations"""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        skip_validation: bool = False
    ):
        """
        Initialize the file manager with AWS S3 client
        
        Args:
            aws_access_key_id: AWS access key ID (uses env var if not provided)
            aws_secret_access_key: AWS secret access key (uses env var if not provided)
            aws_region: AWS region (uses env var if not provided)
            bucket_name: S3 bucket name (uses env var if not provided)
            endpoint_url: Optional S3 endpoint URL for S3-compatible services
            skip_validation: Skip bucket validation (useful for development)
        """
        try:
            # Get credentials from environment if not provided
            self.aws_access_key_id = aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
            self.aws_secret_access_key = aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
            self.aws_region = aws_region or os.getenv('AWS_REGION', 'us-east-1')
            self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
            
            # Handle endpoint URL - filter out empty strings and comments
            endpoint_url_env = os.getenv('S3_ENDPOINT_URL', '').strip()
            if endpoint_url_env and not endpoint_url_env.startswith('#'):
                self.endpoint_url = endpoint_url or endpoint_url_env
            else:
                self.endpoint_url = endpoint_url
            
            if not self.bucket_name:
                if skip_validation:
                    self.bucket_name = "development-bucket"
                    print("WARNING: No S3 bucket configured. Using development mode.")
                    return
                else:
                    raise ValueError("S3 bucket name must be provided via constructor or S3_BUCKET_NAME environment variable")
            
            # Initialize S3 client
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            
            # Create S3 client with optional endpoint URL for S3-compatible services
            client_config = {}
            if self.endpoint_url and self.endpoint_url.strip():
                client_config['endpoint_url'] = self.endpoint_url.strip()
            
            self.s3_client = session.client('s3', **client_config)
            self.s3_resource = session.resource('s3', **client_config)
            self.bucket = self.s3_resource.Bucket(self.bucket_name)
            
            # Verify bucket access (skip if in development mode)
            if not skip_validation:
                try:
                    self.s3_client.head_bucket(Bucket=self.bucket_name)
                except ClientError as e:
                    error_code = int(e.response['Error']['Code'])
                    if error_code == 404:
                        raise ValueError(f"S3 bucket '{self.bucket_name}' does not exist or is not accessible")
                    elif error_code == 403:
                        raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'. Check your credentials and permissions")
                    else:
                        raise ValueError(f"Failed to access S3 bucket '{self.bucket_name}': {str(e)}")
                    
        except NoCredentialsError:
            if skip_validation:
                print("WARNING: No AWS credentials found. Running in development mode.")
                self._development_mode = True
                return
            raise ValueError("AWS credentials not found. Please provide credentials via constructor or environment variables")
        except Exception as e:
            if skip_validation:
                print(f"WARNING: S3 initialization failed: {str(e)}. Running in development mode.")
                self._development_mode = True
                return
            raise Exception(f"Failed to initialize S3 client: {str(e)}")
    
    def _check_development_mode(self):
        """Check if running in development mode and raise appropriate error"""
        if hasattr(self, '_development_mode') and self._development_mode:
            raise Exception("S3 operations not available in development mode. Please configure AWS credentials and S3 bucket.")
    
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
        Create a folder in S3 (simulated using a placeholder object)
        
        Args:
            folder_name: Name of the folder to create
            parent_path: Optional parent directory path
            
        Returns:
            Full path of the created folder
        """
        self._check_development_mode()
        
        if not folder_name or folder_name.strip() == "":
            raise ValueError("Folder name cannot be empty")
        
        # Clean folder name
        folder_name = folder_name.strip()
        
        # Construct full folder path
        if parent_path:
            parent_path = self._normalize_path(parent_path)
            folder_path = f"{parent_path}/{folder_name}"
        else:
            folder_path = folder_name
        
        # Ensure folder path ends with /
        if not folder_path.endswith('/'):
            folder_path += '/'
        
        try:
            # Create folder placeholder in S3 (empty object with trailing slash)
            placeholder_key = f"{folder_path}.folder_placeholder"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=placeholder_key,
                Body='',
                ContentType='text/plain'
            )
            
            return folder_path.rstrip('/')
        except Exception as e:
            raise Exception(f"Failed to create folder: {str(e)}")
    
    async def upload_file(self, file: UploadFile, path: Optional[str] = None) -> FileInfo:
        """
        Upload a file to S3
        
        Args:
            file: File to upload
            path: Optional destination path
            
        Returns:
            FileInfo object with upload details
        """
        self._check_development_mode()
        
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
            
            # Determine content type
            content_type = self._get_content_type(file.filename)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=content,
                ContentType=content_type
            )
            
            # Reset file pointer for any additional operations
            await file.seek(0)
            
            # Return file info
            return FileInfo(
                name=file.filename,
                path=file_path,
                size=len(content),
                content_type=content_type,
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
        Get files and folders in the specified path from S3
        
        Args:
            path: Optional folder path (defaults to root)
            include_hidden: Whether to include hidden files
            sort_by: Sort criteria (name, size, modified, type)
            sort_order: Sort order (asc, desc)
            
        Returns:
            FileListResponse with files and folders
        """
        self._check_development_mode()
        
        path = self._normalize_path(path)
        
        try:
            files = []
            folders = set()
            
            # Set up S3 list parameters
            list_params = {
                'Bucket': self.bucket_name,
                'Delimiter': '/'  # This helps us get "folders"
            }
            
            if path:
                list_params['Prefix'] = f"{path}/"
            
            # Get objects from S3
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(**list_params):
                # Handle "folders" (common prefixes)
                if 'CommonPrefixes' in page:
                    for prefix_info in page['CommonPrefixes']:
                        folder_name = prefix_info['Prefix'].rstrip('/').split('/')[-1]
                        if folder_name and (include_hidden or not folder_name.startswith('.')):
                            folder_path = prefix_info['Prefix'].rstrip('/')
                            folders.add(FolderInfo(
                                name=folder_name,
                                path=folder_path,
                                is_folder=True,
                                modified=datetime.now()
                            ))
                
                # Handle files
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Skip placeholder files
                        if obj['Key'].endswith('.folder_placeholder'):
                            continue
                        
                        # Skip the path itself if it's a "folder"
                        if obj['Key'].endswith('/'):
                            continue
                        
                        # Get file name from key
                        if path:
                            # Remove the prefix to get relative path
                            relative_key = obj['Key'][len(path)+1:] if obj['Key'].startswith(f"{path}/") else obj['Key']
                        else:
                            relative_key = obj['Key']
                        
                        # Skip files in subdirectories (we only want direct children)
                        if '/' in relative_key:
                            continue
                        
                        filename = relative_key
                        
                        # Skip hidden files if not requested
                        if not include_hidden and filename.startswith('.'):
                            continue
                        
                        files.append(FileInfo(
                            name=filename,
                            path=obj['Key'],
                            size=obj['Size'],
                            content_type=self._get_content_type(filename),
                            extension=self._get_file_extension(filename),
                            is_folder=False,
                            modified=obj['LastModified']
                        ))
            
            # Combine files and folders
            all_items = list(folders) + files
            
            # Sort files
            if sort_by == "name":
                all_items.sort(key=lambda x: x.name.lower(), reverse=(sort_order == "desc"))
            elif sort_by == "size":
                all_items.sort(key=lambda x: getattr(x, 'size', 0), reverse=(sort_order == "desc"))
            elif sort_by == "modified":
                all_items.sort(key=lambda x: x.modified, reverse=(sort_order == "desc"))
            elif sort_by == "type":
                # Sort by type: folders first, then by extension
                all_items.sort(key=lambda x: (
                    0 if x.is_folder else 1,
                    x.name.lower()
                ), reverse=(sort_order == "desc"))
            
            return FileListResponse(
                path=path or "",
                files=all_items,
                total_count=len(all_items)
            )
            
        except Exception as e:
            raise Exception(f"Failed to get files: {str(e)}")
    
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
        Delete a file or folder from S3
        
        Args:
            path: Path to delete
            recursive: Whether to delete folders recursively
            
        Returns:
            Deletion result
        """
        path = self._normalize_path(path)
        
        try:
            # Check if it's a folder by looking for objects with this prefix
            list_params = {
                'Bucket': self.bucket_name,
                'Prefix': f"{path}/",
                'MaxKeys': 1
            }
            
            response = self.s3_client.list_objects_v2(**list_params)
            is_folder = 'Contents' in response or self._object_exists(f"{path}/.folder_placeholder")
            
            if is_folder:
                if not recursive:
                    # Check if folder is empty (has any non-placeholder objects)
                    all_objects_response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=f"{path}/"
                    )
                    
                    if 'Contents' in all_objects_response:
                        non_placeholder_objects = [
                            obj for obj in all_objects_response['Contents']
                            if not obj['Key'].endswith('.folder_placeholder')
                        ]
                        if non_placeholder_objects:
                            raise ValueError("Cannot delete non-empty folder without recursive flag")
                
                # Delete all objects in the folder
                deleted_count = 0
                paginator = self.s3_client.get_paginator('list_objects_v2')
                
                for page in paginator.paginate(Bucket=self.bucket_name, Prefix=f"{path}/"):
                    if 'Contents' in page:
                        # Prepare objects for batch deletion
                        objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                        
                        if objects_to_delete:
                            delete_response = self.s3_client.delete_objects(
                                Bucket=self.bucket_name,
                                Delete={'Objects': objects_to_delete}
                            )
                            deleted_count += len(delete_response.get('Deleted', []))
                
                # Also try to delete the folder placeholder
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=f"{path}/.folder_placeholder"
                    )
                except ClientError:
                    pass  # Ignore if placeholder doesn't exist
                
                return {
                    "message": f"Folder deleted successfully",
                    "path": path,
                    "type": "folder",
                    "deleted_items": deleted_count
                }
            else:
                # Delete single file
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=path
                    )
                    return {
                        "message": "File deleted successfully",
                        "path": path,
                        "type": "file"
                    }
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        raise HTTPException(status_code=404, detail=f"File not found: {path}")
                    raise
                
        except HTTPException:
            raise
        except Exception as e:
            raise Exception(f"Failed to delete item: {str(e)}")
    
    def _object_exists(self, key: str) -> bool:
        """
        Check if an object exists in S3
        
        Args:
            key: S3 object key
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def download_file(self, file_path: str) -> Tuple[bytes, str, str]:
        """
        Download a single file from S3
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (file_content, content_type, filename)
        """
        file_path = self._normalize_path(file_path)
        
        try:
            # Download file content from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            content = response['Body'].read()
            filename = self._get_filename(file_path)
            content_type = self._get_content_type(filename)
            
            return content, content_type, filename
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            raise Exception(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    def download_folder(self, folder_path: str) -> Tuple[bytes, str]:
        """
        Download a folder as ZIP archive from S3
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            Tuple of (zip_content, folder_name)
        """
        folder_path = self._normalize_path(folder_path)
        
        try:
            # List all objects in the folder
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=f"{folder_path}/"
            )
            
            objects_found = False
            # Create ZIP archive in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            # Skip placeholder files
                            if obj['Key'].endswith('.folder_placeholder'):
                                continue
                            
                            objects_found = True
                            
                            # Download file content from S3
                            response = self.s3_client.get_object(
                                Bucket=self.bucket_name,
                                Key=obj['Key']
                            )
                            content = response['Body'].read()
                            
                            # Add to ZIP with relative path
                            relative_path = obj['Key'][len(folder_path)+1:]
                            zip_file.writestr(relative_path, content)
            
            if not objects_found:
                raise HTTPException(status_code=404, detail=f"Folder not found or empty: {folder_path}")
            
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
    def copy_file(self, source_path: str, destination_path: str) -> Dict[str, str]:
        """
        Copy a file to a new location in S3
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            Copy result
        """
        source_path = self._normalize_path(source_path)
        destination_path = self._normalize_path(destination_path)
        
        try:
            # Copy object within S3
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_path
            }
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_path
            )
            
            return {
                "message": "File copied successfully",
                "source": source_path,
                "destination": destination_path
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail=f"Source file not found: {source_path}")
            raise Exception(f"Failed to copy file: {str(e)}")
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
        Get detailed information about a file in S3
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information
        """
        file_path = self._normalize_path(file_path)
        
        try:
            # Check if file exists and get metadata
            try:
                response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
                raise
            
            # Get file info from S3 response
            filename = self._get_filename(file_path)
            
            return {
                "name": filename,
                "path": file_path,
                "size": response.get('ContentLength', 0),
                "extension": self._get_file_extension(filename),
                "content_type": response.get('ContentType', self._get_content_type(filename)),
                "is_text": self._is_text_file(filename),
                "parent_path": self._get_parent_path(file_path),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag', '').strip('"')
            }
            
        except HTTPException:
            raise
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
            
            # Download and check size from S3
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            content = response['Body'].read()
            
            if len(content) > max_size:
                # Return truncated content
                text_content = content[:max_size].decode('utf-8', errors='ignore')
                return {
                    "content": text_content,
                    "truncated": True,
                    "size": len(content),
                    "preview_size": len(text_content),
                    "content_type": response.get('ContentType', self._get_content_type(filename))
                }
            else:
                # Return full content
                text_content = content.decode('utf-8', errors='ignore')
                return {
                    "content": text_content,
                    "truncated": False,
                    "size": len(content),
                    "content_type": response.get('ContentType', self._get_content_type(filename))
                }
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            raise Exception(f"Failed to preview file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to preview file: {str(e)}")
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics from S3
        
        Returns:
            Storage statistics
        """
        try:
            # List all objects to calculate stats
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Skip placeholder files
                        if obj['Key'].endswith('.folder_placeholder'):
                            continue
                        
                        # Skip directory markers
                        if obj['Key'].endswith('/'):
                            continue
                        
                        total_files += 1
                        size = obj.get('Size', 0)
                        total_size += size
                        
                        # Count file types
                        extension = self._get_file_extension(obj['Key'])
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