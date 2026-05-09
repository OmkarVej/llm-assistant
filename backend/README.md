Backend for A2Z Assistant (FastAPI)

Usage:
  cd backend
  python -m uvicorn app:app --reload --port 8000

Endpoints:
  GET /health
  POST /chat  { "prompt": "...", "use_local": false }
