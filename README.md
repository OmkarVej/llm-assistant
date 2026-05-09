A2Z Assistant — Full-stack prototype
-----------------------------------
This package contains:
  - backend/: FastAPI backend that can use the local mini-LLM or proxy to OpenAI
  - frontend/: Minimal React app (Vite) to demo the chat UI

Quick start:
  1) Start backend:
     cd backend
     python -m uvicorn app:app --reload --port 8000

  2) Start frontend:
     cd frontend
     npm install
     npm run dev

Environment:
  - To use OpenAI, set OPENAI_API_KEY in env or in configs/default.yaml
  - Local model: this backend expects the mini-llm project (trained checkpoint) to be available
    as a sibling folder (../checkpoints/model.pt) relative to backend/, or inside ../checkpoints

