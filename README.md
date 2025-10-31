# 🚀 SmartServe - AI-Powered Recruitment Platform

> An intelligent, multi-agent workforce recruitment and job matching platform powered by OpenAI GPT-4o, LangChain, and ChromaDB.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange.svg)](https://langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

SmartServe is a next-generation recruitment platform that uses AI agents to automate and enhance the hiring process. It provides separate, intelligent experiences for employers and job seekers, powered by semantic matching, natural language processing, and automated document generation.

### Key Features

- 🤖 **AI Chat Interface** - Natural language interaction with GPT-4o
- 🔍 **Semantic Job Matching** - ChromaDB vector search for intelligent candidate-job pairing
- 📊 **Role-Based Dashboards** - Separate analytics for employers and employees
- 📄 **Automated Document Generation** - AI-powered offer letters and NDAs
- 🔔 **Real-Time Notifications** - WebSocket-based instant updates
- 🛠️ **10+ AI Tools** - Specialized tools for resume parsing, job enhancement, and more
- 🔐 **JWT Authentication** - Secure role-based access control

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                   (Chat / Dashboard / API)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Agent Dispatcher                           │
│           (Routes by Role: Employer/Employee)                │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
┌───────▼────────┐              ┌─────────▼────────┐
│   Orchestrator │              │   Orchestrator   │
│   (Employer)   │              │   (Employee)     │
│   GPT-4o       │              │   GPT-4o         │
└───────┬────────┘              └─────────┬────────┘
        │                                  │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │       Tool Ecosystem        │
        │  (10 LangChain BaseTools)   │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼─────────┐
│   PostgreSQL   │          │   ChromaDB        │
│   (SQLAlchemy) │          │   (Vectors)       │
└────────────────┘          └───────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework:** FastAPI
- **AI/ML:** OpenAI GPT-4o, GPT-4 Turbo, text-embedding-3-large
- **Agent Framework:** LangChain
- **Vector Database:** ChromaDB
- **Database:** SQLite (SQLAlchemy ORM)
- **Real-time:** WebSockets
- **Authentication:** JWT (PassLib, python-jose)
- **NLP:** Spacy

### AI Tools (10 Implemented)
1. **ResumeParserTool** - Extracts skills and summaries from resumes
2. **InterviewSchedulerTool** - Schedules interviews with calendar integration
3. **ProfileAnalyzerTool** - AI-powered candidate profile analysis
4. **JobDescriptionEnhancer** - Improves job postings with GPT-4 Turbo
5. **EmbeddingGenerator** - Creates semantic embeddings
6. **MatchingTool** - Semantic job-candidate matching
7. **NotificationTool** - Real-time push notifications
8. **OnboardingTool** - Generates offer letters and NDAs
9. **ApplicationTool** - Manages job applications
10. **JobFinderTool** - Semantic job search

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/manpower_connector.git
cd manpower_connector
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. **Initialize database**
```bash
python -c "from backend.db.sql_db import init_sql_db; init_sql_db()"
```

6. **Run the application**
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access the API**
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## 📚 API Documentation

### Authentication
```bash
# Register a new user
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "role": "employee"  # or "employer"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Chat Interface
```bash
# Send a message to AI assistant
POST /api/chat/message
Headers: Authorization: Bearer <token>
{
  "message": "Find me Python developer jobs in New York",
  "session_id": "optional-session-id"
}
```

### Direct Tool Invocation
```bash
# List available tools
GET /api/tools/available
Headers: Authorization: Bearer <token>

# Invoke a tool directly
POST /api/tools/invoke
Headers: Authorization: Bearer <token>
{
  "tool_name": "JobFinderTool",
  "parameters": {
    "search_query": "Python developer",
    "location": "New York",
    "limit": 10
  }
}
```

### Analytics
```bash
# Get role-specific dashboard analytics
GET /api/analytics/dashboard
Headers: Authorization: Bearer <token>
```

## 🗂️ Project Structure

```
manpower_connector/
├── backend/
│   ├── orchestration/          # AI orchestration layer
│   │   ├── orchestrator.py     # LangChain AgentExecutor
│   │   ├── agent_dispatcher.py # Role-based routing
│   │   └── workflows/          # Predefined workflows
│   ├── tools_langchain/        # 10 LangChain BaseTools
│   │   ├── resume_parser_tool.py
│   │   ├── job_finder_tool.py
│   │   ├── matching_tool.py
│   │   └── ...
│   ├── chat/                   # Chat interface
│   │   └── chat_routes.py
│   ├── routes/                 # API endpoints
│   │   ├── auth_routes.py
│   │   ├── analytics_routes.py
│   │   ├── tool_routes.py
│   │   └── ...
│   ├── db/                     # Database layer
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── sql_db.py
│   │   └── vector_db.py        # ChromaDB
│   ├── notifications/          # WebSocket manager
│   └── main.py                 # FastAPI application
├── vectors/                    # ChromaDB storage (gitignored)
├── .env                        # Environment variables (gitignored)
├── .env.example                # Example configuration
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_REASONING=gpt-4o
OPENAI_MODEL_ENHANCEMENT=gpt-4-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Application Settings
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 📊 Features by Role

### For Employers
- ✅ Post and enhance job descriptions with AI
- ✅ Automatic candidate matching and ranking
- ✅ Profile analysis and insights
- ✅ Interview scheduling
- ✅ Automated onboarding document generation
- ✅ Application pipeline analytics

### For Employees
- ✅ Intelligent job search and recommendations
- ✅ Resume parsing and skill extraction
- ✅ One-click job applications
- ✅ Match score visibility
- ✅ Interview tracking
- ✅ Application status monitoring

## 🧪 Testing

### Manual Testing with API Docs
1. Navigate to http://localhost:8000/docs
2. Use the interactive Swagger UI
3. Test each endpoint with sample data

### Example Test Flow
1. Register as employee
2. Login and get JWT token
3. Send chat message: "Find Python jobs"
4. View job recommendations
5. Apply to a job
6. Check analytics dashboard

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Development Roadmap

- [ ] React frontend with Tailwind CSS
- [ ] Enhanced matching algorithms
- [ ] Calendar integration (Google/Outlook)
- [ ] Email notifications
- [ ] Resume upload and parsing
- [ ] Video interview integration
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Mobile app

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- OpenAI for GPT-4o and embedding models
- LangChain for the agent framework
- FastAPI for the excellent web framework
- ChromaDB for vector search capabilities

## 📞 Support

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using AI and modern Python technologies**
