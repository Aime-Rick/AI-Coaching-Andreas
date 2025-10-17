# AI Coaching Platform

> A comprehensive AI-powered coaching application for health and wellness professionals, featuring intelligent document analysis, chat assistance, and automated report generation.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://www.typescriptlang.org/)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Hardware Requirements](#-hardware-requirements)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Performance](#-performance)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Production Deployment](#-production-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality
- 🗂️ **Smart File Management** - Upload, organize, and manage client documents with AWS S3 integration
- 💬 **AI Chat Assistant** - Context-aware conversations using OpenAI GPT models with document retrieval
- 📊 **Automated Report Generation** - Generate comprehensive coaching reports in multiple languages
- 🔍 **Vector Search** - Intelligent document search using OpenAI embeddings
- 📁 **Folder-Based Sessions** - Organize coaching sessions by client folders
- 🔐 **Session Management** - Persistent chat history with SQLite/PostgreSQL database

### Advanced Features
- 🖼️ **Image OCR** - Extract text from images using Tesseract
- 📈 **Excel Processing** - Intelligent parsing of spreadsheet data
- 🌍 **Multi-language Support** - Reports in English, German, and more
- 🚀 **Performance Optimized** - Database indexing, caching, and connection pooling
- 📦 **File Compression** - GZip compression for API responses
- ♻️ **Resource Cleanup** - Automatic cleanup of orphaned resources

---

## 🏗️ Architecture

```
AI-Coaching-Andreas/
├── backend/                    # Python FastAPI backend
│   ├── api/                   # API routes and endpoints
│   │   └── main.py           # Main FastAPI application
│   ├── assistant/            # AI assistant logic
│   │   ├── main.py          # Chat and report generation
│   │   ├── utils.py         # Vector store management
│   │   └── cleanup_scheduler.py  # Resource cleanup
│   ├── database/             # Database layer
│   │   ├── connection.py    # Connection pooling (optimized)
│   │   ├── models.py        # SQLAlchemy models with indexes
│   │   └── chat_memory.py   # Chat history management
│   ├── files/                # File processing
│   │   ├── utils.py         # S3 file manager (optimized)
│   │   ├── excel_processor.py   # Excel/CSV processing
│   │   └── image_processor.py   # OCR and image analysis
│   └── cache.py              # Enhanced caching system
│
├── frontend/                  # React TypeScript frontend
│   ├── client/src/
│   │   ├── components/       # React components
│   │   │   ├── AIAssistantSection.tsx
│   │   │   ├── FilesSection.tsx
│   │   │   └── ReportEditorModal.tsx
│   │   ├── lib/              # Utilities
│   │   │   ├── api.ts       # API client (optimized)
│   │   │   ├── queryClient.ts   # React Query config
│   │   │   └── optimizations.ts # Performance utilities
│   │   └── i18n/            # Internationalization
│   └── server/               # Express server for production
│
├── migrate_performance_indexes.py  # Database migration script
├── requirements.txt          # Python dependencies
└── .env                      # Environment configuration
```

---

## 📚 Prerequisites

### Required Software

#### Backend
- **Python**: 3.11 or higher
- **pip**: Latest version
- **Virtual Environment**: `venv` or `virtualenv`

#### Frontend
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher (comes with Node.js)

#### External Services
- **OpenAI API Key**: Required for AI features ([Get one here](https://platform.openai.com/api-keys))
- **AWS Account**: For S3 file storage ([Create account](https://aws.amazon.com/))
- **Tesseract OCR**: For image text extraction

#### Database
- **SQLite**: Included with Python (development only)
- **PostgreSQL**: 14+ (REQUIRED for production)

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Aime-Rick/AI-Coaching-Andreas.git
cd AI-Coaching-Andreas
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### 2.2 Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

#### 2.3 Install System Dependencies (OCR)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Add Tesseract to PATH

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to root directory
cd ..
```

---

## ⚙️ Configuration

### Step 1: Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env

# Or create manually
touch .env
```

### Step 2: Configure `.env` File

```env
# ============================================
# OpenAI Configuration (REQUIRED)
# ============================================
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# ============================================
# AWS S3 Configuration (REQUIRED)
# ============================================
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Optional: For S3-compatible services (MinIO, DigitalOcean Spaces, etc.)
# S3_ENDPOINT_URL=https://your-endpoint-url.com

# ============================================
# Database Configuration
# ============================================
# Development (SQLite)
ENVIRONMENT=development
SQLITE_DB_PATH=ai_coaching.db

# Production (PostgreSQL - REQUIRED)
# Uncomment these for production deployment:
# ENVIRONMENT=production
# DB_USER=postgres
# DB_PASSWORD=your-secure-password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=ai_coaching

# ============================================
# Application Settings
# ============================================
DEBUG=false
REPORTS_FOLDER_PATH=Reports

# ============================================
# Frontend Configuration
# ============================================
VITE_API_URL=http://localhost:8000
```

### Step 3: AWS S3 Setup

#### Option A: Create S3 Bucket (AWS)

```bash
# Using AWS CLI
aws s3 mb s3://your-bucket-name --region us-east-1

# Set bucket permissions (adjust as needed)
aws s3api put-public-access-block \
  --bucket your-bucket-name \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Option B: Use Alternative Storage

The application supports S3-compatible storage:
- **MinIO** (self-hosted)
- **DigitalOcean Spaces**
- **Wasabi**
- **Backblaze B2**

Configure `S3_ENDPOINT_URL` in `.env` for these services.

### Step 4: Database Migration

Run the performance optimization migration:

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run migration
python3 migrate_performance_indexes.py
```

Expected output:
```
INFO:__main__:Starting database migration...
INFO:__main__:✓ Tables verified
INFO:__main__:Database type: SQLite
INFO:__main__:✓ Created index: idx_user_active_updated
INFO:__main__:✓ Created index: idx_vector_store
INFO:__main__:✓ Created index: idx_session_type_timestamp
INFO:__main__:✓ Created index: idx_session_timestamp
INFO:__main__:✓ Database migration completed successfully!
```

---

## 🎯 Running the Application

### Development Mode (Recommended for Testing)

#### Terminal 1: Start Backend

```bash
# Navigate to project root
cd AI-Coaching-Andreas

# Activate virtual environment
source venv/bin/activate

# Start FastAPI backend with auto-reload
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Backend will be available at: **http://localhost:8000**

#### Terminal 2: Start Frontend

```bash
# Open new terminal
cd AI-Coaching-Andreas/frontend

# Start development server
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Frontend will be available at: **http://localhost:5173**

### Verification Steps

#### 1. Check Backend Health

```bash
# Test API is running
curl http://localhost:8000/

# Expected response:
# {"message":"File Management API","version":"1.0.0","description":"..."}
```

#### 2. Check Performance Endpoint

```bash
# View cache statistics
curl http://localhost:8000/performance

# Expected response includes cache stats and metrics
```

#### 3. Access API Documentation

Open in browser: **http://localhost:8000/docs**

You should see the interactive Swagger UI with all API endpoints.

#### 4. Access Frontend

Open in browser: **http://localhost:5173**

You should see the AI Coaching Platform interface.

---

## 💻 Hardware Requirements

### Minimum Requirements (Development/Testing)
**Suitable for: 10-20 concurrent users**

```yaml
CPU: 2-4 cores (2.0 GHz or higher)
RAM: 8 GB
Storage: 50 GB SSD
  - Application: 10 GB
  - Database: 20 GB
  - Temporary files: 20 GB
Network: 100 Mbps
Operating System: Ubuntu 22.04 LTS, macOS 12+, or Windows 10+
```

**Estimated Monthly Cost:** $40-60/month on cloud providers

### Recommended Requirements (Production)
**Suitable for: 50-100 concurrent users**

```yaml
CPU: 4-8 cores (3.0 GHz or higher)
  - FastAPI workers: 3-4 cores
  - Database operations: 2-3 cores
  - File processing: 1-2 cores

RAM: 16-32 GB
  - Python/FastAPI: 4-8 GB
  - SQLite connection pool: 2-4 GB
  - In-memory cache: 2-4 GB
  - File operations: 2-4 GB
  - System overhead: 2-4 GB
  - Buffer: 4-8 GB

Storage: 200-500 GB NVMe SSD
  - Application code: 5 GB
  - SQLite database: 50-100 GB (with indexes)
  - S3 cache/temp: 50-100 GB
  - Vector stores: 20-50 GB
  - Logs: 10-20 GB
  - Free space: 65-215 GB

Network: 1 Gbps
  - Upload: 500 Mbps
  - Download: 500 Mbps

Operating System: Ubuntu 22.04 LTS (recommended)
```

**Recommended Cloud Instances:**
- **AWS**: t3.xlarge or c6i.xlarge ($100-200/month)
- **Google Cloud**: n2-standard-4 ($120-180/month)
- **Azure**: Standard_D4s_v3 ($140-190/month)
- **DigitalOcean**: Performance Droplet 8GB ($96/month)

### High-Performance Requirements (Enterprise)
**Suitable for: 100-500 concurrent users**

```yaml
CPU: 16-32 cores (3.5 GHz or higher)
RAM: 64-128 GB
Storage: 1-2 TB NVMe SSD (RAID 10)
  - IOPS: 50,000+
  - Latency: <1ms
Network: 10 Gbps with load balancer
```

**Recommended Setup:**
- Load balancer (NGINX/AWS ALB)
- 2-4 application servers
- Dedicated PostgreSQL server
- Redis cache cluster
- CDN for static assets

**Estimated Monthly Cost:** $400-800/month

### Performance Expectations

With recommended production hardware:

| Metric | Target |
|--------|--------|
| **Page Load Time** | 1-2 seconds |
| **File Listing** | 0.5-1 second |
| **Chat Response** | 4-6 seconds |
| **Report Generation** | 8-12 seconds |
| **File Upload (50MB)** | 5-10 seconds |
| **API Response Time** | 50-200ms |
| **Concurrent Users** | 50-100 |
| **Requests/Minute** | 1000+ |

---

## 📖 Usage Guide

### 1. First-Time Setup

#### Create Client Folders

1. Navigate to **Files** section
2. Click **Create Folder**
3. Name it after your client (e.g., "John_Doe")
4. Upload client documents (anamnesis forms, health records, etc.)

#### Supported File Types

- **Documents**: PDF, DOCX, TXT, MD
- **Spreadsheets**: XLSX, XLS, CSV
- **Images**: JPG, PNG, GIF, BMP, TIFF (with OCR)
- **Data**: JSON, XML

### 2. Starting a Chat Session

1. Navigate to **AI Assistant** section
2. Select a client folder from the dropdown
3. Wait for session initialization (~2-5 seconds)
4. Start asking questions about the client

**Example Questions:**
```
- "What are the client's main health goals?"
- "Summarize the client's sleep patterns"
- "What medications is the client taking?"
- "What are the key challenges mentioned?"
```

### 3. Generating Reports

1. Ensure you have an active chat session
2. Click **Generate Report** button
3. Wait for generation (8-15 seconds)
4. Review and edit the report in the modal
5. Download as PDF or save to Reports folder

**Report Sections:**
- Summary of client's situation (3-6 bullet points)
- Key coaching priorities (numbered list with explanations)

### 4. Multi-Language Support

Reports can be generated in multiple languages:
- **English** (default)
- **German** (Deutsch)

Language is auto-detected or can be specified in settings.

### 5. Session Management

#### Switch Between Clients
- Select different folder from dropdown
- Previous session is automatically cleaned up
- New session starts with fresh context

#### View Chat History
- All messages are stored in database
- Access via session list
- Filter by date or client

#### End Session
- Click "End Session" or switch folders
- Vector stores are cleaned up automatically
- Chat history is preserved

---

## 📡 API Documentation

### Interactive Documentation

Once the backend is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### File Management
```http
GET    /files                    # List files and folders
POST   /files/upload            # Upload single file
POST   /files/upload-multiple   # Upload multiple files
DELETE /files                   # Delete file or folder
GET    /files/download/{path}   # Download file
POST   /folders                 # Create folder
```

#### AI Assistant
```http
POST   /chat                    # Send chat message
POST   /report                  # Generate coaching report
GET    /sessions                # List chat sessions
POST   /sessions/start          # Start new session
POST   /sessions/end            # End session
GET    /sessions/{id}/history   # Get chat history
```

#### System
```http
GET    /                        # Health check
GET    /performance             # Performance metrics
GET    /storage/stats           # Storage statistics
```

### Example API Calls

#### Upload File
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf" \
  -F "path=ClientFolder"
```

#### Start Chat Session
```bash
curl -X POST "http://localhost:8000/sessions/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "coach_123",
    "folder_path": "ClientFolder",
    "session_title": "Coaching Session - John Doe"
  }'
```

#### Send Chat Message
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the client'\''s main goals?",
    "session_id": "session-uuid-here"
  }'
```

---

## ⚡ Performance

### Optimizations Applied

✅ **Database**: Connection pooling, composite indexes, WAL mode  
✅ **Caching**: In-memory cache with 70%+ hit rate  
✅ **File Operations**: Optimized S3 transfers with chunking  
✅ **API**: GZip compression, request deduplication  
✅ **Frontend**: React Query optimization, lazy loading  
✅ **AI**: Faster model (gpt-4o-mini), reduced tokens  

### Performance Metrics

See **[PERFORMANCE-OPTIMIZATION-GUIDE.md](PERFORMANCE-OPTIMIZATION-GUIDE.md)** for detailed information.

### Monitoring

```bash
# Check cache statistics
curl http://localhost:8000/performance

# View logs
tail -f logs/app.log

# Monitor slow requests (look for warnings)
# "Slow request: GET /files took 5.23s"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. OpenAI API Errors

**Error**: `openai.AuthenticationError: Invalid API key`

**Solution**:
```bash
# Verify API key in .env
cat .env | grep OPENAI_API_KEY

# Test API key
python3 -c "from openai import OpenAI; client = OpenAI(); print('API key valid')"
```

#### 3. S3 Connection Issues

**Error**: `S3 bucket not accessible`

**Solution**:
```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name

# Or test with Python
python3 -c "import boto3; s3 = boto3.client('s3'); print(s3.list_buckets())"

# Check .env configuration
cat .env | grep AWS
```

#### 4. Database Locked

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
```bash
# Check for multiple backend instances
ps aux | grep uvicorn

# Kill extra processes
kill -9 <PID>

# Re-run database migration
python3 migrate_performance_indexes.py
```

#### 5. Port Already in Use

**Error**: `Address already in use: 8000`

**Solution**:
```bash
# Find process using port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn backend.api.main:app --reload --port 8001
```

#### 6. Frontend Build Errors

**Error**: `npm ERR! Cannot find module`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### 7. OCR Not Working

**Error**: `TesseractNotFoundError`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

### Debug Mode

Enable detailed logging:

```bash
# In .env file
DEBUG=true

# Restart backend
uvicorn backend.api.main:app --reload --log-level debug
```

### Getting Help

1. Check logs in terminal output
2. Review `.env` configuration
3. Consult [PERFORMANCE-OPTIMIZATION-GUIDE.md](PERFORMANCE-OPTIMIZATION-GUIDE.md)
4. Check [GitHub Issues](https://github.com/Aime-Rick/AI-Coaching-Andreas/issues)
5. Contact support

---

## 👨‍💻 Development

### Project Structure

```
backend/
  api/          # FastAPI routes
  assistant/    # AI logic
  database/     # Data models
  files/        # File processing

frontend/
  client/src/
    components/ # React components
    lib/        # Utilities
    i18n/       # Translations
```

### Development Workflow

#### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

#### 2. Make Changes

Backend changes trigger auto-reload (uvicorn --reload)  
Frontend changes trigger hot-reload (Vite HMR)

#### 3. Test Changes

```bash
# Backend tests (if available)
pytest

# Frontend tests
cd frontend
npm test

# Type checking
npm run type-check
```

#### 4. Commit and Push

```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### Code Style

**Backend (Python)**:
- Follow PEP 8
- Use type hints
- Document functions with docstrings

**Frontend (TypeScript)**:
- Follow ESLint rules
- Use TypeScript strict mode
- Document complex components

### Adding New Features

#### Backend Endpoint

1. Add route in `backend/api/main.py`
2. Implement logic in appropriate module
3. Update OpenAPI documentation
4. Test with curl or Postman

#### Frontend Component

1. Create component in `frontend/client/src/components/`
2. Add types in `types/`
3. Integrate with React Query
4. Add translations in `i18n/resources.ts`

---

## 🚀 Production Deployment

### Preparation

#### 1. Update Environment

```env
# .env for production
ENVIRONMENT=production
DEBUG=false

# Use PostgreSQL
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=ai_coaching

# Production API URL
VITE_API_URL=https://api.yourdomain.com
```

#### 2. Database Migration

```bash
# Run migrations
python3 migrate_performance_indexes.py

# Backup database
pg_dump ai_coaching > backup_$(date +%Y%m%d).sql
```

#### 3. Build Frontend

```bash
cd frontend
npm run build

# Output in: frontend/dist/
```

### Deployment Options

#### Option 1: Docker (Recommended)

Create `Dockerfile`:

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY migrate_performance_indexes.py .
COPY .env .

# Run migrations
RUN python3 migrate_performance_indexes.py

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
# Build
docker build -t ai-coaching-backend .

# Run
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  ai-coaching-backend
```

#### Option 2: Systemd Service

Create `/etc/systemd/system/ai-coaching.service`:

```ini
[Unit]
Description=AI Coaching Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ai-coaching
Environment="PATH=/var/www/ai-coaching/venv/bin"
ExecStart=/var/www/ai-coaching/venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ai-coaching
sudo systemctl start ai-coaching
sudo systemctl status ai-coaching
```

#### Option 3: NGINX + Gunicorn

Install Gunicorn:

```bash
pip install gunicorn
```

Start with Gunicorn:

```bash
gunicorn backend.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

NGINX configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/ai-coaching/frontend/dist;
    }
}
```

### Security Checklist

- [ ] Use HTTPS/SSL certificates
- [ ] Set strong passwords in environment variables
- [ ] Enable firewall (allow only necessary ports)
- [ ] Regular security updates
- [ ] Database backups scheduled
- [ ] API rate limiting configured
- [ ] CORS properly configured for production domain
- [ ] Environment variables not committed to git

### Monitoring

Set up monitoring for:
- Server CPU/RAM usage
- Database performance
- API response times
- Error rates
- Cache hit rates

Recommended tools:
- **Prometheus + Grafana** (metrics)
- **Sentry** (error tracking)
- **New Relic** (APM)

---

## 📊 Performance Benchmarks

### Before Optimization
- Page load: 3-4 seconds
- File listing: 2-3 seconds
- Chat response: 8-10 seconds
- Database queries: 200-500ms

### After Optimization
- Page load: **1-2 seconds** (50-67% faster)
- File listing: **0.5-1 second** (60-67% faster)
- Chat response: **4-6 seconds** (40-50% faster)
- Database queries: **50-100ms** (75-80% faster)

See **[PERFORMANCE-OPTIMIZATION-GUIDE.md](PERFORMANCE-OPTIMIZATION-GUIDE.md)** for details.

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits atomic and well-described

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT models and embeddings
- **FastAPI** for the excellent Python web framework
- **React** and **TypeScript** for modern frontend development
- **Tesseract** for OCR capabilities
- **AWS S3** for reliable file storage

---

## 📞 Support

- **Documentation**: See `docs/` folder
- **Issues**: [GitHub Issues](https://github.com/Aime-Rick/AI-Coaching-Andreas/issues)
- **Email**: support@yourdomain.com

---

## 🗺️ Roadmap

- [ ] Multi-user authentication system
- [ ] Real-time collaboration features
- [ ] Mobile application (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Integration with calendar systems
- [ ] Video call integration
- [ ] Payment processing
- [ ] Client portal
- [ ] Multi-language UI (beyond reports)
- [ ] Advanced file versioning

---

## 📈 Version History

### v1.0.0 (Current)
- Initial release
- Core chat and report features
- File management with S3
- Performance optimizations
- Multi-language report support

---

**Built with ❤️ for health and wellness coaches**

For questions or support, please open an issue on GitHub.
