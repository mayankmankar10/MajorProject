# SmartServe Quick Start Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Git
- OpenAI API Key

## Backend Setup

### 1. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Or activate (Windows CMD)
.\venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
# Install Python packages
pip install -r requirements.txt

# Download Spacy language model
python -m spacy download en_core_web_sm
```

### 3. Configure Environment

```powershell
# Copy example environment file
copy .env.example .env

# Edit .env and add your configuration:
# - OPENAI_API_KEY (required)
# - JWT_SECRET_KEY (generate a secure random string)
```

**Generate secure JWT_SECRET_KEY:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Initialize Database

```powershell
# Initialize SQL database
python -c "from backend.db.sql_db import init_sql_db; init_sql_db()"

# Initialize vector store
python -c "from backend.db.vector_db import init_vector_store; init_vector_store()"
```

### 5. Run Backend Server

```powershell
# Run with auto-reload for development
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Backend will be available at:
# - API: http://localhost:8000
# - Swagger Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

## Testing the API

### 1. Register a User (Employer)

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employer@example.com",
    "password": "SecurePass123!",
    "role": "employer",
    "company_name": "Tech Corp"
  }'
```

### 2. Register a User (Employee)

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employee@example.com",
    "password": "SecurePass123!",
    "role": "employee",
    "full_name": "John Doe"
  }'
```

### 3. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "employer@example.com",
    "password": "SecurePass123!"
  }'
```

**Response includes:**
- `access_token`: Use this for authenticated requests
- `user_id`: User identifier
- `role`: User role (employer/employee)

### 4. Get Current User Profile

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Test WebSocket Notification

```javascript
// In browser console or Node.js
const ws = new WebSocket('ws://localhost:8000/api/notifications/ws?token=YOUR_ACCESS_TOKEN');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Notification:', JSON.parse(event.data));

// Send ping to keep connection alive
setInterval(() => ws.send('ping'), 30000);
```

## Current API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user profile
- `POST /api/auth/verify-token` - Verify token validity

### Notifications
- `WS /api/notifications/ws` - WebSocket connection for real-time notifications
- `GET /api/notifications/` - List notifications
- `GET /api/notifications/unread-count` - Get unread count
- `POST /api/notifications/mark-read` - Mark notifications as read
- `POST /api/notifications/mark-all-read` - Mark all as read
- `DELETE /api/notifications/{id}` - Delete notification

### Health & Info
- `GET /` - API info and status
- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## LangChain Tools Available

The following tools have been implemented and can be used by the orchestrator:

1. **NotificationTool** (`send_notification`)
   - Send in-app notifications via WebSocket
   - Store notifications in database
   - Location: `backend/tools/notification_tool.py`

2. **EmbeddingGenerator** (`generate_embedding`)
   - Generate OpenAI embeddings from text
   - Uses text-embedding-3-large (3072 dimensions)
   - Location: `backend/tools/embedding_generator.py`

3. **JobDescriptionEnhancer** (`enhance_job_description`)
   - Enhance job descriptions using GPT-4 Turbo
   - Improve clarity, structure, and appeal
   - Location: `backend/tools/job_description_enhancer.py`

4. **MatchingTool** (`semantic_match`)
   - Semantic job-candidate matching via ChromaDB
   - Returns match scores and entity details
   - Location: `backend/tools/matching_tool.py`

5. **ResumeParserTool** (existing)
   - Parse resumes using Spacy NLP
   - Extract skills, experience, education
   - Location: `backend/agents/tools/resume_parser_tool.py`

## Database Schema

### Core Tables
- **users** - Unified authentication
- **employers** - Company profiles
- **employees** - Candidate profiles with skills, certifications
- **jobs** - Job postings with enhanced descriptions
- **applications** - Job applications with match scores
- **interviews** - Interview scheduling
- **onboarding_tasks** - Digital onboarding workflow
- **notifications** - In-app notifications

## Environment Variables Reference

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL_REASONING=gpt-4o
OPENAI_MODEL_ENHANCEMENT=gpt-4-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Database
DATABASE_URL=sqlite:///./manpower.db
VECTOR_DB_DIR=./vectors/chroma
VECTOR_DB_COLLECTION=smartserve_collection

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-32-chars-minimum
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# WebSocket
WS_HOST=0.0.0.0
WS_PORT=8001

# Application
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
LOG_FILE=smartserve.log
LOG_FORMAT=json
```

## Troubleshooting

### Common Issues

**1. Import Errors**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Spacy Model Not Found**
```powershell
python -m spacy download en_core_web_sm
```

**3. Database Errors**
```powershell
# Reset database
Remove-Item manpower.db -Force
python -c "from backend.db.sql_db import init_sql_db; init_sql_db()"
```

**4. OpenAI API Errors**
- Verify `OPENAI_API_KEY` in `.env`
- Check API quota at platform.openai.com
- Ensure billing is set up

**5. WebSocket Connection Issues**
- Check firewall allows port 8000
- Verify token is included in connection URL
- Check CORS settings in main.py

## Next Steps

1. **Implement Orchestration Layer** - Create LangChain AgentExecutor
2. **Build Chat Interface** - GPT-4o powered command parsing
3. **Refactor Existing Agents** - Update for new schema
4. **Create Frontend** - React + Tailwind UI
5. **Add More Tools** - FilterTool, OnboardingTool, etc.

## Development Workflow

```powershell
# Start backend
uvicorn backend.main:app --reload

# Run tests (when implemented)
pytest

# Format code
black backend/

# Lint code
flake8 backend/

# Type check
mypy backend/
```

## Support

For issues or questions:
1. Check WARP.md for detailed architecture
2. Check IMPLEMENTATION_PROGRESS.md for status
3. Review API documentation at /docs
4. Check logs in smartserve.log
