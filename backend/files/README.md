# File Management System for AWS S3

A comprehensive file explorer and management system built for AWS S3, providing all the essential features of a modern file manager.

## Features

### 📁 Folder Management
- **Create folders** with nested directory support
- **Navigate** through folder hierarchies
- **Delete folders** with recursive options
- **List folder contents** with sorting and filtering

### 📄 File Operations
- **Upload single or multiple files**
- **Download files** individually or as ZIP archives
- **Delete files** with batch operations
- **Copy and move files** between directories
- **File search** with pattern matching and type filtering

### 🔍 Advanced Features
- **File preview** for text files
- **Storage statistics** and usage analytics
- **File type detection** and MIME type support
- **Batch operations** for multiple files
- **Hidden file handling**
- **Comprehensive error handling**

## API Endpoints

### Folder Operations
- `POST /folders` - Create a new folder
- `GET /files?path={folder_path}` - List folder contents

### File Upload
- `POST /files/upload` - Upload a single file
- `POST /files/upload-multiple` - Upload multiple files

### File Management
- `GET /files` - List files and folders
- `DELETE /files` - Delete a file or folder
- `DELETE /files/batch` - Delete multiple items
- `GET /files/search` - Search for files

### Download Operations
- `GET /files/download/{file_path}` - Download a file
- `GET /files/download-folder/{folder_path}` - Download folder as ZIP

### File Operations
- `POST /files/copy` - Copy a file
- `POST /files/move` - Move a file
- `GET /files/info/{file_path}` - Get file information
- `GET /files/preview/{file_path}` - Preview file content

### Storage Information
- `GET /storage/stats` - Get storage usage statistics

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. The main dependencies include:
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `boto3` - AWS SDK for Python
- `botocore` - AWS SDK core libraries
- `pydantic` - Data validation
- `python-multipart` - File upload support

## Usage

### Starting the API Server

```bash
cd files
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Basic Examples

#### Create a Folder
```bash
curl -X POST "http://localhost:8000/folders" \
  -H "Content-Type: application/json" \
  -d '{"folder_name": "my_documents", "parent_path": "projects"}'
```

#### Upload a File
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -F "file=@document.pdf" \
  -F "path=my_documents"
```

#### List Files
```bash
curl "http://localhost:8000/files?path=my_documents&sort_by=name&sort_order=asc"
```

#### Download a File
```bash
curl "http://localhost:8000/files/download/my_documents/document.pdf" \
  --output document.pdf
```

#### Search Files
```bash
curl "http://localhost:8000/files/search?query=report&file_type=pdf"
```

#### Get Storage Stats
```bash
curl "http://localhost:8000/storage/stats"
```

### Python SDK Usage

```python
from files import FileManager, CreateFolderRequest

# Initialize file manager with S3 credentials
file_manager = FileManager(
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key", 
    aws_region="us-east-1",
    bucket_name="your-bucket-name"
)

# Create a folder
folder_path = file_manager.create_folder("my_project", "documents")

# Get file list
file_list = file_manager.get_files("documents/my_project")

# Search files
results = file_manager.search_files("*.pdf", path="documents")

# Get storage statistics
stats = file_manager.get_storage_stats()
```

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## File Structure

```
files/
├── __init__.py          # Package initialization
├── main.py             # FastAPI application and endpoints
├── utils.py            # FileManager class and utility functions
├── models.py           # Pydantic models for request/response
└── README.md           # This documentation
```

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request` - Invalid parameters or operation errors
- `404 Not Found` - File or folder not found
- `500 Internal Server Error` - Server or storage errors

All errors return a structured JSON response with detailed error messages.

## Limitations

- File paths are case-sensitive
- Maximum file size depends on S3 limits (5GB per PUT operation, 5TB with multipart upload)
- Folder operations simulate traditional file systems using placeholder files
- AWS credentials must be properly configured for access
- S3 bucket must exist and be accessible with provided credentials

## Security Considerations

- Always use IAM roles or access keys with minimal required permissions
- Enable S3 bucket versioning for data protection
- Consider using S3 bucket policies to restrict access
- Use HTTPS endpoints for data encryption in transit
- Enable S3 server-side encryption for data at rest

## Supported File Types

The system supports all file types with automatic MIME type detection:
- **Documents**: PDF, DOC, DOCX, TXT, MD
- **Images**: JPG, PNG, GIF, SVG, WEBP
- **Videos**: MP4, AVI, MOV, WEBM
- **Audio**: MP3, WAV, OGG, FLAC
- **Archives**: ZIP, TAR, GZ, RAR
- **Code**: PY, JS, HTML, CSS, JSON, XML
- **And many more...**

## Configuration

### Environment Variables

The application requires AWS credentials and S3 configuration. You can provide these via environment variables:

```bash
# AWS Credentials
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
export AWS_REGION=us-east-1

# S3 Configuration
export S3_BUCKET_NAME=your-bucket-name
export S3_ENDPOINT_URL=https://s3.amazonaws.com  # Optional: for S3-compatible services
```

### Alternative Configuration

You can also pass credentials directly when initializing the FileManager:

```python
file_manager = FileManager(
    aws_access_key_id="your_access_key",
    aws_secret_access_key="your_secret_key",
    aws_region="us-east-1", 
    bucket_name="your-bucket-name",
    endpoint_url="https://s3.amazonaws.com"  # Optional
)
```

## Contributing

This file management system is designed to be modular and extensible. Key areas for enhancement:
- Additional file operation endpoints
- Enhanced search capabilities
- File versioning support
- Advanced permissions management
- Integration with other storage backends

## Support

For issues or questions, please refer to the AWS S3 documentation or create an issue in the project repository.

### Useful Links

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [S3 API Reference](https://docs.aws.amazon.com/s3/latest/API/)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)