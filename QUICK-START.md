# 🚀 Quick Start Guide

> Get your AI Coaching Platform running in 10 minutes!

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] OpenAI API key ([Get one](https://platform.openai.com/api-keys))
- [ ] AWS account with S3 bucket ([Create](https://aws.amazon.com/))
- [ ] Git installed
- [ ] Terminal/Command prompt access

---

## ⚡ 5-Step Setup

### Step 1: Clone and Navigate (30 seconds)

```bash
git clone https://github.com/Aime-Rick/AI-Coaching-Andreas.git
cd AI-Coaching-Andreas
```

### Step 2: Backend Setup (2 minutes)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng
# macOS: brew install tesseract
```

### Step 3: Configure Environment (2 minutes)

Create `.env` file in project root:

```env
# OpenAI (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key-here

# AWS S3 (REQUIRED)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Application
ENVIRONMENT=development
SQLITE_DB_PATH=ai_coaching.db
DEBUG=false
VITE_API_URL=http://localhost:8000
```

### Step 4: Initialize Database (30 seconds)

```bash
python3 migrate_performance_indexes.py
```

Expected output:
```
✓ Created index: idx_user_active_updated
✓ Created index: idx_vector_store
✓ Created index: idx_session_type_timestamp
✓ Created index: idx_session_timestamp
✓ Database migration completed successfully!
```

### Step 5: Install Frontend (2 minutes)

```bash
cd frontend
npm install
cd ..
```

---

## 🎬 Running the Application

### Terminal 1: Start Backend

```bash
source venv/bin/activate
uvicorn backend.api.main:app --reload
```

✅ Backend running at: **http://localhost:8000**

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

✅ Frontend running at: **http://localhost:5173**

---

## ✅ Verification

### 1. Test Backend
```bash
curl http://localhost:8000/
# Should return: {"message":"File Management API",...}
```

### 2. Test API Docs
Open: **http://localhost:8000/docs**

### 3. Test Frontend
Open: **http://localhost:5173**

### 4. Check Performance
```bash
curl http://localhost:8000/performance
# Should show cache statistics
```

---

## 🎯 First Use

1. **Create a folder** in Files section (e.g., "TestClient")
2. **Upload documents** to that folder
3. **Go to AI Assistant** section
4. **Select the folder** from dropdown
5. **Wait for session** to initialize (~3-5 seconds)
6. **Ask a question** about the documents
7. **Generate a report** when ready

---

## 📊 Hardware Requirements

### Minimum (Development)
```
CPU: 2-4 cores
RAM: 8 GB
Storage: 50 GB SSD
Network: 100 Mbps
```

### Recommended (Production)
```
CPU: 4-8 cores
RAM: 16-32 GB
Storage: 200-500 GB NVMe SSD
Network: 1 Gbps
```

**Cost**: $40-200/month depending on cloud provider

---

## 🐛 Common Issues

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Kill process
lsof -i :8000
kill -9 <PID>
```

### "OpenAI API error"
- Check your API key in `.env`
- Verify it's a valid key at https://platform.openai.com/api-keys
- Ensure you have credits

### "S3 connection failed"
- Verify AWS credentials in `.env`
- Test: `aws s3 ls s3://your-bucket-name`
- Check bucket permissions

### "Database locked"
```bash
# Stop all backend processes
ps aux | grep uvicorn
kill -9 <PID>
```

---

## 📚 Next Steps

- Read full [README.md](README.md) for detailed documentation
- Check [PERFORMANCE-OPTIMIZATION-GUIDE.md](PERFORMANCE-OPTIMIZATION-GUIDE.md) for tuning
- Review [API Documentation](http://localhost:8000/docs) after starting backend
- Explore example use cases in Usage Guide section

---

## 🆘 Need Help?

1. Check [README.md](README.md) Troubleshooting section
2. Review terminal output for error messages
3. Verify all prerequisites are installed
4. Open issue on GitHub
5. Check `.env` configuration

---

## ✨ Success!

If you see:
- ✅ Backend at http://localhost:8000
- ✅ Frontend at http://localhost:5173
- ✅ No errors in terminals
- ✅ Can access UI in browser

**You're ready to go! 🎉**

---

## 🔗 Quick Links

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Performance**: http://localhost:8000/performance

---

**Total Setup Time**: ~10 minutes ⏱️

Happy coaching! 💪
