import os
from dotenv import load_dotenv
import tempfile
from openai import OpenAI
from typing import List, Optional
import io
load_dotenv()
from backend.files.utils import FileManager

client = OpenAI()
file_manager = FileManager(skip_validation=True)  # Skip S3 validation for development


def create_vector_store(folder_path: str, store_name: Optional[str] = None) -> str:
    """
    Create a vector store from files in a folder using the File Management System
    
    Args:
        folder_path: Path to the folder containing files (e.g., "documents/client_data")
        store_name: Optional name for the vector store
    
    Returns:
        Vector store ID
    """
    if not store_name:
        store_name = f"Vector Store - {folder_path}"
    
    # Create vector store
    vector_store = client.vector_stores.create(name=store_name)
    
    try:
        # Get list of files in the folder
        file_list_response = file_manager.get_files(path=folder_path, include_hidden=False)
        
        if not file_list_response.files:
            print(f"No files found in folder: {folder_path}")
            return vector_store.id
        
        # Filter only actual files (not folders) and text-based files suitable for vector processing
        suitable_files = []
        suitable_extensions = {'.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv', '.py', '.js', '.html', '.xml'}
        
        for file_info in file_list_response.files:
            if not file_info.is_folder and file_info.extension.lower() in suitable_extensions:
                suitable_files.append(file_info)
        
        if not suitable_files:
            print(f"No suitable files found for vector processing in folder: {folder_path}")
            return vector_store.id
        
        print(f"Processing {len(suitable_files)} files for vector store...")
        
        # Process each file
        for file_info in suitable_files:
            try:
                # Download file content
                file_content, content_type, filename = file_manager.download_file(file_info.path)
                
                print(f"Processing file: {filename} ({file_info.size} bytes)")
                
                # Create a temporary file-like object for OpenAI upload
                file_like_object = io.BytesIO(file_content)
                file_like_object.name = filename  # OpenAI needs a name attribute
                
                # Upload to vector store
                file_batch = client.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store.id,
                    file=file_like_object
                )
                
                print(f"✅ Uploaded {filename} to vector store")
                
            except Exception as e:
                print(f"❌ Error processing file {file_info.name}: {str(e)}")
                continue
        
        print(f"✅ Vector store created successfully: {vector_store.id}")
        return vector_store.id
        
    except Exception as e:
        print(f"❌ Error creating vector store: {str(e)}")
        # Clean up vector store if creation failed
        try:
            client.vector_stores.delete(vector_store_id=vector_store.id)
        except:
            pass
        raise


def create_vector_store_from_files(file_paths: List[str], store_name: Optional[str] = None) -> str:
    """
    Create a vector store from specific file paths using the File Management System
    
    Args:
        file_paths: List of specific file paths to include
        store_name: Optional name for the vector store
    
    Returns:
        Vector store ID
    """
    if not store_name:
        store_name = f"Vector Store - {len(file_paths)} files"
    
    # Create vector store
    vector_store = client.vector_stores.create(name=store_name)
    
    try:
        suitable_extensions = {'.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv', '.py', '.js', '.html', '.xml'}
        processed_count = 0
        
        print(f"Processing {len(file_paths)} specific files for vector store...")
        
        # Process each file
        for file_path in file_paths:
            try:
                # Get file info to check if it's suitable
                file_info = file_manager.get_file_info(file_path)
                
                # Check if file extension is suitable for vector processing
                if file_info.get('extension', '').lower() not in suitable_extensions:
                    print(f"⚠️ Skipping {file_path}: File type not suitable for vector processing")
                    continue
                
                # Download file content
                file_content, content_type, filename = file_manager.download_file(file_path)
                
                print(f"Processing file: {filename}")
                
                # Create a temporary file-like object for OpenAI upload
                file_like_object = io.BytesIO(file_content)
                file_like_object.name = filename  # OpenAI needs a name attribute
                
                # Upload to vector store
                file_batch = client.vector_stores.files.upload_and_poll(
                    vector_store_id=vector_store.id,
                    file=file_like_object
                )
                
                print(f"✅ Uploaded {filename} to vector store")
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Error processing file {file_path}: {str(e)}")
                continue
        
        print(f"✅ Vector store created successfully: {vector_store.id} ({processed_count} files processed)")
        return vector_store.id
        
    except Exception as e:
        print(f"❌ Error creating vector store: {str(e)}")
        # Clean up vector store if creation failed
        try:
            client.vector_stores.delete(vector_store_id=vector_store.id)
        except:
            pass
        raise

def delete_vector_store(store_id: str):
    """Deletes a vector store by its ID."""
    client.vector_stores.delete(
        vector_store_id=store_id
    )