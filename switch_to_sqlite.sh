#!/bin/bash

echo "================================================"
echo "🔄 Switching to SQLite Database"
echo "================================================"

cd /Users/prashanthvanama/projects/mini-llm-assistant/backend

# Backup current database.py
if [ -f "database.py" ]; then
    cp database.py database_mysql.py.backup
    echo "✅ Backed up MySQL database.py to database_mysql.py.backup"
fi

# Replace with SQLite version
cp database_sqlite.py database.py
echo "✅ Switched to SQLite database"

echo ""
echo "================================================"
echo "✅ Database switched to SQLite!"
echo "================================================"
echo ""
echo "SQLite database will be created at:"
echo "  /Users/prashanthvanama/projects/mini-llm-assistant/data/assistant.db"
echo ""
echo "Restart your backend server:"
echo "  cd /Users/prashanthvanama/projects/mini-llm-assistant"
echo "  lsof -ti:8000 | xargs kill -9"
echo "  ./run_all.sh"
echo ""

