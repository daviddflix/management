# Dev Team Manager - Backend

AI-powered backend service for automating team lead responsibilities and enhancing development workflows.

## 🌟 Features

### Team Management
- 🤖 AI-powered sprint planning and team coordination
- 📊 Automated task assignments and workload balancing  
- 🔄 Real-time team performance monitoring
- 👥 Team capacity and velocity tracking

### Task Management
- ✅ Automated task dependency analysis
- 📋 Smart task prioritization
- 🎯 AI-based task assignments
- 🔍 Blocker detection and resolution

### Quality Assurance
- 📈 Automated code quality metrics
- 🔎 Quality trend analysis
- 💡 AI-powered improvement suggestions
- 🎯 Sprint quality scoring

### Integrations
- 📅 Monday.com for project management
- 💬 Slack for team communications
- 🧠 OpenAI for AI assistance
- 📊 Prometheus for metrics
- 🐛 Sentry for error tracking

## 📦 AI Agents Architecture

The system is powered by three specialized AI agents, each handling specific aspects of team and project management:

### Team Lead Agent
The strategic overseer of the development process, focusing on high-level team management and coordination.

Features:
- 🎯 Sprint planning and goal setting
- 👥 Team composition and workload distribution
- 📊 Resource allocation and capacity planning
- 🔄 Cross-team coordination and communication
- 📈 Performance evaluation and feedback
- 🚀 Team velocity optimization
- 🎓 Mentorship and growth planning
- 🤝 Stakeholder communication management

### Task Management Agent
Handles the tactical aspects of project execution and task organization.

Features:
- 📋 Task breakdown and estimation
- 🔄 Dependency mapping and critical path analysis
- 📊 Task prioritization and scheduling
- 🎯 Intelligent task assignment based on skills and availability
- 🚧 Blocker identification and resolution
- 📈 Progress tracking and reporting
- ⏰ Deadline management and reminders
- 🔄 Task workflow optimization

### Quality Assurance Agent
Focuses on maintaining and improving code quality and development standards.

Features:
- 🔍 Code review automation and suggestions
- 📊 Quality metrics tracking and analysis
- 🐛 Bug pattern detection and prevention
- 🎯 Test coverage optimization
- 📈 Technical debt monitoring
- 🔄 Continuous improvement recommendations
- 📋 Best practices enforcement
- 🛡️ Security vulnerability scanning

### Agent Collaboration
The agents work together through:
- 🤝 Shared context and knowledge base
- 📊 Unified data processing pipeline
- 🔄 Cross-agent communication protocols
- 📈 Coordinated decision-making
- 🎯 Common goal alignment
- 🔍 Feedback loops and learning mechanisms

## 📦 Key Dependencies

### Core Framework
- **[FastAPI](https://fastapi.tiangolo.com/) (0.115.6)**: Modern, high-performance web framework for building APIs with Python based on standard Python type hints. Features automatic API documentation, data validation, and async support.
- **[Uvicorn](https://www.uvicorn.org/) (0.34.0)**: Lightning-fast ASGI server implementation, using uvloop and httptools for production-grade async server.
- **[Pydantic](https://docs.pydantic.dev/) (2.10.4)**: Data validation library using Python type annotations. Provides powerful data parsing, validation, and settings management.
- **[Pydantic-Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (2.7.0)**: Settings management using Pydantic models, perfect for handling environment variables and configuration.
- **[Python-Dotenv](https://github.com/theskumar/python-dotenv) (1.0.1)**: Loads environment variables from .env files, essential for configuration management.

### Database & ORM
- **[SQLAlchemy](https://www.sqlalchemy.org/) (2.0.36)**: The Python SQL toolkit and Object-Relational Mapper that provides application developers with the full power and flexibility of SQL.
- **[Alembic](https://alembic.sqlalchemy.org/) (1.14.0)**: Database migration tool for SQLAlchemy, handling schema versions and updates.

### Authentication & Security
- **[FastAPI Users](https://fastapi-users.github.io/fastapi-users/) (14.0.0)**: Ready-to-use and customizable users management for FastAPI. Handles registration, authentication, password reset, and more.
- **[FastAPI Sessions](https://github.com/jordanisaacs/fastapi-sessions) (0.3.2)**: Session management for FastAPI applications, providing secure session handling and storage.
- **[Python-Jose](https://python-jose.readthedocs.io/) (3.3.0)**: JavaScript Object Signing and Encryption (JOSE) implementation for Python for JWT token handling.
- **[Passlib](https://passlib.readthedocs.io/) (1.7.4)**: Password hashing library providing secure password storage and verification with bcrypt support.

### AI & Analytics
- **[OpenAI](https://platform.openai.com/docs/api-reference) (1.58.1)**: Official Python client for OpenAI's API, enabling integration with GPT models for AI-powered features.
- **[LangChain](https://python.langchain.com/) (0.3.13)**: Framework for developing applications powered by language models. Provides tools for prompt management, memory, and chains of operations.
- **[Pandas](https://pandas.pydata.org/) (2.2.3)**: Powerful data manipulation and analysis library. Offers data structures and operations for manipulating numerical tables and time series.
- **[NumPy](https://numpy.org/) (1.26.4)**: Fundamental package for scientific computing in Python. Provides support for large, multi-dimensional arrays and matrices.
- **[Plotly](https://plotly.com/python/) (5.24.1)**: Interactive visualization library for Python. Creates sophisticated, interactive visualizations for data analysis and reporting.

### External Service Integrations
- **[Monday SDK](https://developer.monday.com/api-reference/docs) (2.0.1)**: Official Python SDK for Monday.com's GraphQL API, enabling seamless integration with Monday.com's project management platform.
- **[Slack SDK](https://slack.dev/python-slack-sdk/) (3.34.0)**: Official Python SDK for building Slack apps and integrating with Slack's platform. Supports real-time messaging and web API.
- **[Sentry SDK](https://docs.sentry.io/platforms/python/) (2.19.2)**: Application monitoring and error tracking integration with FastAPI support.
- **[Prometheus Client](https://github.com/prometheus/client_python) (0.21.1)**: Monitoring and metrics collection library for Python applications.

### HTTP & Networking
- **[HTTPX](https://www.python-httpx.org/) (0.28.1)**: Modern, fully featured HTTP client for Python 3, supporting async/await. Used for making HTTP requests.
- **[AIOHTTP](https://docs.aiohttp.org/) (3.11.11)**: Asynchronous HTTP client/server framework for asyncio and Python.
- **[Python-Multipart](https://github.com/andrew-d/python-multipart) (0.0.17)**: Streaming multipart parser for Python, handling file uploads and form data.
- **[Asyncio](https://docs.python.org/3/library/asyncio.html) (3.4.3)**: Python's built-in asynchronous I/O framework for writing concurrent code.

### Time & Scheduling
- **[APScheduler](https://apscheduler.readthedocs.io/) (3.11.0)**: Advanced Python Scheduler for scheduling tasks and periodic job execution.
- **[Python-DateUtil](https://dateutil.readthedocs.io/) (2.9.0.post0)**: Powerful extensions to the standard datetime module for parsing and manipulating dates.
- **[PyTZ](https://pythonhosted.org/pytz/) (2024.2)**: World timezone definitions for Python. Used for handling timezone-aware datetime calculations.

### Document Processing
- **[Python-Docx](https://python-docx.readthedocs.io/) (1.1.2)**: Python library for creating and updating Microsoft Word (.docx) files.
- **[Python-PDF](https://github.com/mstamy2/PyPDF2) (0.4.0)**: Library for reading and manipulating PDF files in Python.
- **[CSV23](https://pypi.org/project/csv23/) (0.3.4)**: Python 2/3 compatible CSV library for handling CSV files with proper Unicode support.

### Utilities
- **[Tenacity](https://tenacity.readthedocs.io/) (9.0.0)**: General-purpose retrying library to simplify the task of adding retry behavior to just about anything.

Each package is carefully selected to provide robust functionality while maintaining high performance and reliability. Regular updates are performed to ensure security and feature compatibility. When dealing with specific functionality, developers should use these prescribed packages to maintain consistency across the codebase:
- For HTTP requests: Use HTTPX or AIOHTTP
- For date/time operations: Use Python-DateUtil and PyTZ
- For retry logic: Use Tenacity
- For scheduling: Use APScheduler
- For document handling:
  - Word documents: Use Python-Docx
  - PDF files: Use Python-PDF
  - CSV files: Use CSV23

## Project Structure

project-root/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── sprints.py
│   │   │   │   ├── metrics.py
│   │   │   │   ├── auth.py
│   │   │   │   └── reports.py
│   │   │   └── dependencies.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── task.py
│   │   │   ├── sprint.py
│   │   │   ├── report.py
│   │   │   └── metrics.py
│   │   ├── services/
│   │   │   ├── monday_service.py
│   │   │   ├── slack_service.py
│   │   │   └── scheduler_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── monday_helpers.py
│   │       └── slack_formatters.py
│   ├── README.md
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml



## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Redis
- PostgreSQL
- Docker (optional)

### Local Setup Without Docker

1. **Create and activate virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install package in development mode**
```bash
# This ensures Python can find the app module
pip install -e .
```

4. **Set up environment variables**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your configuration
# Required variables:
OPENAI_API_KEY=your_openai_key
MONDAY_API_KEY=your_monday_key
SLACK_BOT_TOKEN=your_slack_token
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

5. **Initialize database**
```bash
# Apply migrations
alembic upgrade head
```

6. **Start the application**
```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Setup

1. **Build and start services**
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

2. **Initialize database in Docker**
```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

3. **Useful Docker commands**
```bash
# Stop services
docker-compose down

# Rebuild specific service
docker-compose up -d --build backend

# View service logs
docker-compose logs -f backend

# Access service shell
docker-compose exec backend bash
```

### Development Commands

```bash
# Run tests
pytest

# Run linting
flake8 app
black app

# Generate migrations
alembic revision --autogenerate -m "migration message"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Monitoring

1. **Access API Documentation**
```
http://localhost:8000/docs  # Swagger UI
http://localhost:8000/redoc # ReDoc
```

2. **Metrics and Health**
```
http://localhost:8000/metrics    # Prometheus metrics
http://localhost:8000/health     # Health check
```

### Troubleshooting

1. **Database Connection Issues**
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database (warning: destroys data)
docker-compose down -v postgres
docker-compose up -d postgres
```

2. **Redis Connection Issues**
```bash
# Check Redis status
docker-compose ps redis

# View Redis logs
docker-compose logs redis

# Access Redis CLI
docker-compose exec redis redis-cli
```

3. **Common Issues**

- **Port conflicts**: Check if ports 8000, 5432, or 6379 are already in use
```bash
# Windows
netstat -ano | findstr "8000"
# Unix/MacOS
lsof -i :8000
```

- **Permission issues**: Ensure proper file permissions
```bash
# Unix/MacOS
chmod -R 755 .
```

- **Environment variables**: Verify all required variables are set
```bash
# Check environment
docker-compose exec backend env
```
