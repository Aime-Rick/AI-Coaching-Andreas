import os
from dotenv import load_dotenv
import tempfile
from openai import OpenAI
from typing import List, Optional
import io
import logging

load_dotenv()
from backend.files.utils import FileManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Get OpenAI client with proper error handling"""
    try:
        return OpenAI()
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        raise


client = get_openai_client()
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
        
        # Filter files suitable for vector processing including Excel and images
        suitable_files = []
        suitable_extensions = {
            '.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv', 
            '.py', '.js', '.html', '.xml', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'
        }
        
        processed_count = 0
        
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
                
                # Process Excel files before uploading to vector store
                if file_info.extension.lower() in {'.xls', '.xlsx', '.csv'}:
                    try:
                        from backend.files.excel_processor import ExcelProcessor
                        
                        # Use smart extraction that includes more data but handles large files
                        # For files under 1MB, include all data; for larger files, use smart sampling
                        if file_info.size < 1024 * 1024:  # 1MB threshold
                            text_content = ExcelProcessor.extract_complete_text_for_vector_store(file_content, filename)
                            logger.info(f"Complete data extraction for small Excel file: {filename}")
                        else:
                            text_content = ExcelProcessor.extract_text_for_vector_store(file_content, filename)
                            logger.info(f"Smart sampling for large Excel file: {filename}")
                            
                        file_content = text_content.encode('utf-8')
                        # Change filename extension to .txt so OpenAI accepts it
                        filename = filename.rsplit('.', 1)[0] + '_processed.txt'
                        print(f"✅ Processed Excel file: {file_info.name} → {filename}")
                    except Exception as excel_error:
                        print(f"⚠️ Excel processing failed for {filename}: {excel_error}")
                        continue
                
                # Process image files before uploading to vector store  
                elif file_info.extension.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
                    try:
                        from backend.files.image_processor import ImageProcessor
                        text_content = ImageProcessor.extract_text_for_vector_store(file_content, filename)
                        file_content = text_content.encode('utf-8')
                        # Change filename extension to .txt so OpenAI accepts it
                        filename = filename.rsplit('.', 1)[0] + '_processed.txt'
                        print(f"✅ Processed image file: {file_info.name} → {filename}")
                    except Exception as image_error:
                        print(f"⚠️ Image processing failed for {filename}: {image_error}")
                        continue
                
                # Create file-like object for OpenAI upload
                file_like_object = io.BytesIO(file_content)
                file_like_object.name = filename
                
                # Upload to vector store with retry logic
                try:
                    file_batch = client.vector_stores.files.upload_and_poll(
                        vector_store_id=vector_store.id,
                        file=file_like_object
                    )
                    
                    processed_count += 1
                    print(f"✅ Uploaded {filename} to vector store (status: {file_batch.status})")
                    
                except Exception as upload_error:
                    print(f"❌ Failed to upload {filename} to vector store: {upload_error}")
                    # Log the error but continue with other files
                    continue
                
            except Exception as e:
                print(f"❌ Failed to process {file_info.path}: {str(e)}")
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
        suitable_extensions = {
            '.txt', '.md', '.pdf', '.doc', '.docx', '.json', '.csv', 
            '.py', '.js', '.html', '.xml', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'
        }
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
                
                # Process Excel files before uploading to vector store
                if file_info.get('extension', '').lower() in {'.xls', '.xlsx', '.csv'}:
                    try:
                        from backend.files.excel_processor import ExcelProcessor
                        
                        # Use smart extraction that includes more data but handles large files
                        file_size = file_info.get('size', 0)
                        if file_size < 1024 * 1024:  # 1MB threshold
                            text_content = ExcelProcessor.extract_complete_text_for_vector_store(file_content, filename)
                            logger.info(f"Complete data extraction for small Excel file: {filename}")
                        else:
                            text_content = ExcelProcessor.extract_text_for_vector_store(file_content, filename)
                            logger.info(f"Smart sampling for large Excel file: {filename}")
                            
                        file_content = text_content.encode('utf-8')
                        # Change filename extension to .txt so OpenAI accepts it
                        filename = filename.rsplit('.', 1)[0] + '_processed.txt'
                        print(f"✅ Processed Excel file: {file_path} → {filename}")
                    except Exception as excel_error:
                        print(f"⚠️ Excel processing failed for {filename}: {excel_error}")
                        continue
                
                # Process image files before uploading to vector store
                elif file_info.get('extension', '').lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
                    try:
                        from backend.files.image_processor import ImageProcessor
                        text_content = ImageProcessor.extract_text_for_vector_store(file_content, filename)
                        file_content = text_content.encode('utf-8')
                        # Change filename extension to .txt so OpenAI accepts it
                        filename = filename.rsplit('.', 1)[0] + '_processed.txt'
                        print(f"✅ Processed image file: {file_path} → {filename}")
                    except Exception as image_error:
                        print(f"⚠️ Image processing failed for {filename}: {image_error}")
                        continue
                
                # Create a temporary file-like object for OpenAI upload
                file_like_object = io.BytesIO(file_content)
                file_like_object.name = filename  # OpenAI needs a name attribute
                
                # Upload to vector store with retry logic
                try:
                    file_batch = client.vector_stores.files.upload_and_poll(
                        vector_store_id=vector_store.id,
                        file=file_like_object
                    )
                    
                    print(f"✅ Uploaded {filename} to vector store (status: {file_batch.status})")
                    processed_count += 1
                    
                except Exception as upload_error:
                    print(f"❌ Failed to upload {filename} to vector store: {upload_error}")
                    # Log the error but continue with other files
                    continue
                
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

def delete_vector_store(store_id: str) -> bool:
    """Deletes a vector store and all its associated files.
    
    Args:
        store_id: ID of the vector store to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"Starting cleanup of vector store: {store_id}")
        
        # First, list all files in the vector store
        try:
            vector_store_files = client.vector_stores.files.list(vector_store_id=store_id)
            file_ids = [file.id for file in vector_store_files.data]
            
            print(f"Found {len(file_ids)} files in vector store {store_id}")
            
            # Delete each file from the vector store
            for file_id in file_ids:
                try:
                    client.vector_stores.files.delete(
                        vector_store_id=store_id,
                        file_id=file_id
                    )
                    print(f"✅ Removed file {file_id} from vector store")
                except Exception as e:
                    print(f"⚠️ Warning: Could not remove file {file_id} from vector store: {str(e)}")
                    
                # Also delete the file from OpenAI storage entirely
                try:
                    client.files.delete(file_id)
                    print(f"✅ Deleted file {file_id} from OpenAI storage")
                except Exception as e:
                    print(f"⚠️ Warning: Could not delete file {file_id} from OpenAI storage: {str(e)}")
                    
        except Exception as e:
            print(f"⚠️ Warning: Could not list files in vector store {store_id}: {str(e)}")
        
        # Finally, delete the vector store itself
        client.vector_stores.delete(vector_store_id=store_id)
        print(f"✅ Successfully deleted vector store {store_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting vector store {store_id}: {str(e)}")
        return False