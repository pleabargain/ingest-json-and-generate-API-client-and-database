# Project Structure for JSON Log Processing System

## Required Files

```
/json_log_processor/
├── requirements.txt         # Project dependencies
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pydantic.py     # Pydantic models for JSON validation
│   │   └── database.py     # SQLAlchemy ORM models
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py   # Database connection handling
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py    # API route definitions
│   └── utils/
│       ├── __init__.py
│       └── json_parser.py  # JSON processing utilities
└── tests/
    ├── __init__.py
    ├── test_api.py
    └── test_parser.py

## Dependencies Required

- FastAPI
- Pydantic
- SQLAlchemy
- uvicorn
- pytest (for testing)
- python-dotenv (for configuration)

## Database Schema (Initial Design)

### LogEntry Table
- id: UUID (primary key)
- model: String
- input: Text
- output: JSON
- response_time_seconds: Float
- timestamp: DateTime
- created_at: DateTime

## API Endpoints (Initial Plan)

- POST /logs - Create new log entry
- GET /logs - List all logs
- GET /logs/{id} - Get specific log
- GET /logs/model/{model_name} - Filter logs by model
- GET /logs/stats - Get usage statistics
