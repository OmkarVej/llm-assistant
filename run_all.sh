#!/bin/bash
echo 'Start backend:'
(cd backend && python -m uvicorn app:app --reload --port 8000) &

echo 'Start frontend (run separately if you prefer):'
echo 'cd frontend && npm install && npm run dev'
