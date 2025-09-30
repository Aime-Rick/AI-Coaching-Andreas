# AI Coaching Chat Memory System

This system provides persistent chat memory management for the AI coaching application, allowing users to have continuous conversations across multiple sessions.

## Features

- 🧠 **Persistent Chat Memory**: Conversations are stored and can be resumed
- 💬 **Multi-Session Support**: Multiple chat sessions per user
- 📊 **Report Generation**: Generate coaching reports with context
- 🔄 **Session Management**: Create, update, delete, and list chat sessions
- 🏗️ **Dual Database Support**: SQLite for development, PostgreSQL for production
- 📈 **Usage Tracking**: Track message counts and token usage

## Architecture

### Database Models

#### ChatSession
- `session_id`: Unique identifier for each chat session
- `user_id`: Optional user identification
- `title`: Auto-generated or user-provided session title
- `vector_store_id`: Associated document context for RAG
- `created_at`, `updated_at`: Timestamps
- `is_active`: Soft delete flag

#### ChatMessage  
- `session_id`: Links to parent chat session
- `role`: Message role (user, assistant, system)
- `content`: Message content
- `message_type`: Type (chat, report, system)
- `timestamp`: When message was created
- `tokens_used`: Optional token tracking

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# For Development (SQLite)
ENVIRONMENT=development
OPENAI_API_KEY=your_openai_api_key
SQLITE_DB_PATH=ai_coaching.db

# For Production (PostgreSQL)
ENVIRONMENT=production
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_coaching
```

### 3. Initialize Database

Run the migration script:

```bash
python migrate_db.py
```

## Usage

### Basic Chat with Memory

```python
from backend.assistant.main import generate_chat_response

# Start new conversation
result = generate_chat_response(
    message="Hello, I need help with my fitness goals",
    vector_store_id="your_vector_store_id",
    user_id="user123"
)

session_id = result["session_id"]
print(result["response"])

# Continue conversation
result = generate_chat_response(
    message="What about my diet?",
    vector_store_id="your_vector_store_id", 
    session_id=session_id  # Continue same session
)
```

### Session Management

```python
from backend.assistant.main import (
    get_chat_sessions,
    get_chat_history,
    delete_chat_session,
    update_session_title
)

# List user's chat sessions
sessions = get_chat_sessions("user123")

# Get full chat history
history = get_chat_history(session_id)

# Update session title
update_session_title(session_id, "Fitness Coaching Session")

# Delete session
delete_chat_session(session_id)
```

### Generate Reports

```python
from backend.assistant.main import generate_report

result = generate_report(
    vector_store_id="your_vector_store_id",
    user_id="user123"
)

print(result["report"])
```

## Demo Application

Run the interactive demo:

```bash
python chat_demo.py
```

This provides a CLI interface to test all chat memory features:

- Start new chats
- Continue existing conversations
- View chat history
- Manage sessions
- Generate reports

## Database Configuration

### Development (SQLite)
- Automatically creates `ai_coaching.db` file
- No additional setup required
- Perfect for development and testing

### Production (PostgreSQL)
- Requires PostgreSQL server
- Set `ENVIRONMENT=production` in `.env`
- Configure database connection details

Example PostgreSQL setup:

```sql
CREATE DATABASE ai_coaching;
CREATE USER coaching_app WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_coaching TO coaching_app;
```

## API Integration

The chat memory system is designed to integrate with web frameworks. Here's an example FastAPI integration:

```python
from fastapi import FastAPI, Depends
from backend.assistant.main import generate_chat_response
from backend.database.connection import get_db

app = FastAPI()

@app.post("/chat")
async def chat_endpoint(
    message: str,
    vector_store_id: str,
    session_id: str = None,
    user_id: str = None
):
    result = generate_chat_response(
        message=message,
        vector_store_id=vector_store_id,
        session_id=session_id,
        user_id=user_id
    )
    return result
```

## Key Benefits

1. **Contextual Conversations**: The AI remembers previous messages in the same session
2. **User Session Management**: Each user can have multiple ongoing conversations
3. **Scalable**: Works with both SQLite (dev) and PostgreSQL (production)
4. **RAG Integration**: Each session can be associated with specific document contexts
5. **Usage Tracking**: Monitor token usage and conversation metrics

## Best Practices

1. **Session Limits**: Implement reasonable limits on message history for context
2. **Cleanup**: Periodically clean up old or inactive sessions
3. **Token Management**: Monitor and limit token usage per session
4. **Error Handling**: Always handle database connection errors gracefully
5. **Security**: Validate session ownership before allowing access

## Troubleshooting

### Database Connection Issues
- Check that your database server is running
- Verify connection credentials in `.env`
- Run `python migrate_db.py` to test connection

### Memory Issues
- Large chat histories can consume significant tokens
- Consider implementing message limits or summarization
- Monitor database size and implement cleanup routines

### Performance
- Add database indexes for frequently queried fields
- Consider pagination for large chat histories
- Use connection pooling for high-traffic scenarios