#!/bin/bash
# Sync Environment Variables Script
# This script keeps .env and .env.env.backup in sync

set -e

PROJECT_ROOT="/Users/prashanthvanama/projects/mini-llm-assistant"
ENV_FILE="$PROJECT_ROOT/.env"
BACKUP_FILE="$PROJECT_ROOT/.env.env.backup"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║            Environment Variable Sync Script                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if files exist
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "⚠️  Warning: .env.env.backup not found, creating from .env"
    cp "$ENV_FILE" "$BACKUP_FILE"
fi

# Extract API keys
MAIN_KEY=$(grep "^OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2 || echo "")
BACKUP_KEY=$(grep "^OPENAI_API_KEY=" "$BACKUP_FILE" | grep -v "^#" | head -1 | cut -d'=' -f2 || echo "")

echo "📋 Current API Keys:"
echo "   .env:              ${MAIN_KEY:0:20}...${MAIN_KEY: -10}"
echo "   .env.env.backup:   ${BACKUP_KEY:0:20}...${BACKUP_KEY: -10}"
echo ""

# Determine which is newer
MAIN_MODIFIED=$(stat -f "%m" "$ENV_FILE" 2>/dev/null || stat -c "%Y" "$ENV_FILE" 2>/dev/null)
BACKUP_MODIFIED=$(stat -f "%m" "$BACKUP_FILE" 2>/dev/null || stat -c "%Y" "$BACKUP_FILE" 2>/dev/null)

if [ "$MAIN_KEY" = "$BACKUP_KEY" ]; then
    echo "✅ API keys are already in sync!"
    exit 0
fi

# Ask user which one to use
echo "🔄 API keys are different. Which one do you want to use?"
echo ""
echo "   1. Use .env key (${MAIN_KEY:0:20}...)"
echo "   2. Use .env.env.backup key (${BACKUP_KEY:0:20}...)"
echo "   3. Enter new key manually"
echo "   4. Cancel"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        # Use .env key everywhere
        NEW_KEY="$MAIN_KEY"
        echo "📝 Using .env key..."
        ;;
    2)
        # Use backup key everywhere
        NEW_KEY="$BACKUP_KEY"
        echo "📝 Using .env.env.backup key..."
        ;;
    3)
        # Manual entry
        read -p "Enter new OpenAI API key: " NEW_KEY
        echo "📝 Using manually entered key..."
        ;;
    4)
        echo "❌ Cancelled"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Validate key format
if [[ ! "$NEW_KEY" =~ ^sk-proj- ]]; then
    echo "⚠️  Warning: API key doesn't start with 'sk-proj-'"
    read -p "Continue anyway? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ Cancelled"
        exit 0
    fi
fi

# Update both files
echo ""
echo "🔄 Updating environment files..."

# Update .env
if grep -q "^OPENAI_API_KEY=" "$ENV_FILE"; then
    sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$NEW_KEY|" "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
    echo "   ✅ Updated .env"
else
    echo "OPENAI_API_KEY=$NEW_KEY" >> "$ENV_FILE"
    echo "   ✅ Added to .env"
fi

# Update .env.env.backup (update first non-commented OPENAI_API_KEY)
if grep -q "^OPENAI_API_KEY=" "$BACKUP_FILE"; then
    sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$NEW_KEY|" "$BACKUP_FILE"
    rm -f "${BACKUP_FILE}.bak"
    echo "   ✅ Updated .env.env.backup"
else
    echo "OPENAI_API_KEY=$NEW_KEY" >> "$BACKUP_FILE"
    echo "   ✅ Added to .env.env.backup"
fi

echo ""
echo "✅ Sync complete! API key is now consistent across all files."
echo ""
echo "🔄 Restarting backend to apply changes..."

# Restart backend
if pgrep -f "uvicorn.*app:app" > /dev/null; then
    pkill -f "uvicorn.*app:app"
    sleep 2
    echo "   ✅ Backend stopped"
fi

cd "$PROJECT_ROOT/backend"
source "$PROJECT_ROOT/venv/bin/activate"
nohup python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000 > "$PROJECT_ROOT/backend.log" 2>&1 &
sleep 3

echo "   ✅ Backend restarted"
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     ✅ ALL DONE! ✅                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "New API Key: ${NEW_KEY:0:20}...${NEW_KEY: -10}"
echo "Applied to: .env, .env.env.backup, backend"
echo ""

