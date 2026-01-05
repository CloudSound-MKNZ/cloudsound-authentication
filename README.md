# Authentication Service

Handles JWT token generation, validation, and user session management.

## Features

- JWT token generation
- Token validation
- Token refresh
- Session management

## Development

```bash
cd backend/authentication
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8006
```

