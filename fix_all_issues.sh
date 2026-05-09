#!/bin/bash

# ============================================================================
# FIX ALL ISSUES SCRIPT
# ============================================================================
# This script will fix common issues with the Mini LLM Assistant
#

set -e  # Exit on error

echo "============================================================================"
echo "🔧 FIXING MINI LLM ASSISTANT ISSUES"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Check Python
echo "1️⃣  Checking Python installation..."
echo "--------------------------------------------------------------------"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Step 2: Check/Create Virtual Environment
echo ""
echo "2️⃣  Checking virtual environment..."
echo "--------------------------------------------------------------------"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Step 3: Install/Update Dependencies
echo ""
echo "3️⃣  Installing/Updating dependencies..."
echo "--------------------------------------------------------------------"

# Check if requirements files exist
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${RED}❌ backend/requirements.txt not found${NC}"
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install main requirements
echo "Installing main dependencies..."
pip install -r requirements.txt

# Install backend requirements
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install python-dotenv if not present
echo "Installing python-dotenv..."
pip install python-dotenv requests

echo -e "${GREEN}✅ All dependencies installed${NC}"

# Step 4: Check .env file
echo ""
echo "4️⃣  Checking environment configuration..."
echo "--------------------------------------------------------------------"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your credentials${NC}"
        echo ""
        echo "Required values:"
        echo "  - JIRA_URL"
        echo "  - JIRA_USERNAME"
        echo "  - JIRA_API_TOKEN"
        echo ""
        echo "Run: python setup_jira_connection.py (for interactive setup)"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        echo "Creating basic .env file..."
        cat > .env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Jira Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECTS=

# Database Configuration
DB_TYPE=sqlite
DB_PATH=data/assistant.db
EOF
        echo -e "${GREEN}✅ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please edit it with your credentials${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check if Jira variables are set
    if grep -q "JIRA_URL=https://yourcompany.atlassian.net" .env; then
        echo -e "${YELLOW}⚠️  .env file has default values${NC}"
        echo "Please update with your actual Jira credentials"
    fi
fi

# Step 5: Check/Create directories
echo ""
echo "5️⃣  Checking directories..."
echo "--------------------------------------------------------------------"

# Create necessary directories
mkdir -p data
mkdir -p knowledge
mkdir -p checkpoints

echo -e "${GREEN}✅ All directories created${NC}"

# Step 6: Check database
echo ""
echo "6️⃣  Checking database..."
echo "--------------------------------------------------------------------"

if [ -f "data/assistant.db" ]; then
    echo -e "${GREEN}✅ Database exists${NC}"
else
    echo "Database will be created on first run"
fi

# Step 7: Make scripts executable
echo ""
echo "7️⃣  Setting up scripts..."
echo "--------------------------------------------------------------------"

chmod +x run_all.sh 2>/dev/null || true
chmod +x setup_jira_connection.py 2>/dev/null || true
chmod +x test_jira_connection.py 2>/dev/null || true
chmod +x load_jira.py 2>/dev/null || true
chmod +x load_confluence.py 2>/dev/null || true
chmod +x switch_to_sqlite.sh 2>/dev/null || true

echo -e "${GREEN}✅ Scripts are executable${NC}"

# Step 8: Check ports
echo ""
echo "8️⃣  Checking ports..."
echo "--------------------------------------------------------------------"

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use${NC}"
    echo "To kill the process:"
    echo "  lsof -ti:8000 | xargs kill -9"
else
    echo -e "${GREEN}✅ Port 8000 is available${NC}"
fi

# Check if port 5173 is in use
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 5173 is in use${NC}"
    echo "To kill the process:"
    echo "  lsof -ti:5173 | xargs kill -9"
else
    echo -e "${GREEN}✅ Port 5173 is available${NC}"
fi

# Summary
echo ""
echo "============================================================================"
echo "📊 SUMMARY"
echo "============================================================================"
echo ""

# Check if Jira is configured
if [ -f ".env" ]; then
    source .env
    if [ -n "$JIRA_URL" ] && [ "$JIRA_URL" != "https://yourcompany.atlassian.net" ]; then
        echo -e "${GREEN}✅ Environment configured${NC}"
        JIRA_CONFIGURED=true
    else
        echo -e "${YELLOW}⚠️  Jira not configured yet${NC}"
        JIRA_CONFIGURED=false
    fi
else
    echo -e "${YELLOW}⚠️  .env file missing${NC}"
    JIRA_CONFIGURED=false
fi

echo ""
echo "📋 Next Steps:"
echo ""

if [ "$JIRA_CONFIGURED" = false ]; then
    echo "1️⃣  Configure Jira (REQUIRED):"
    echo "   Interactive setup:  python setup_jira_connection.py"
    echo "   OR manually edit:   nano .env"
    echo ""
fi

echo "2️⃣  Test Jira connection:"
echo "   python test_jira_connection.py"
echo ""

echo "3️⃣  Load Jira data:"
echo "   python load_jira.py"
echo ""

echo "4️⃣  Start the application:"
echo "   ./run_all.sh"
echo ""

echo "5️⃣  Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   Product Dashboard: open product_dashboard_fixed.html"
echo ""

echo "💡 Tips:"
echo "  • Create Jira API token at: https://id.atlassian.com/manage-profile/security/api-tokens"
echo "  • Use the same token for both Jira and Confluence"
echo "  • Check JIRA_FIX_GUIDE.md for troubleshooting"
echo ""

echo "============================================================================"
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "============================================================================"
echo ""

