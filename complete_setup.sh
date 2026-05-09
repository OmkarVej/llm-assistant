#!/bin/bash

# ============================================================================
# COMPLETE THE SETUP - Final Steps
# ============================================================================

set -e

echo "============================================================================"
echo "🎯 COMPLETING YOUR SETUP"
echo "============================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")"

echo "✅ Issues Fixed:"
echo "  • Jira URL corrected (removed /jira/)"
echo "  • Authentication working"
echo "  • 17 projects accessible"
echo "  • Product dashboard CSV upload fixed"
echo "  • All dependencies installed"
echo ""

echo -e "${YELLOW}⚠️  FINAL STEP NEEDED${NC}"
echo "--------------------------------------------------------------------"
echo "You need to add Jira project keys to your .env file"
echo ""

echo "Your available project keys:"
echo ""
echo "  Software Projects:"
echo "    • ANG  - A2Z Next Gen"
echo "    • AZ   - A2Z Sync App"
echo "    • MDP  - A2Z Product Discovery Board"
echo ""
echo "  Service Desk Projects:"
echo "    • OPS  - DevOps"
echo "    • IT   - Information Technology"
echo "    • SECOPS - CyberSecurity Operations"
echo ""
echo "  Business Projects:"
echo "    • CS   - Client Services"
echo "    • CLIEN - Client Success Management"
echo "    • FIN  - Finance"
echo "    • GRC  - Governance, Risk, and Compliance"
echo ""

echo "--------------------------------------------------------------------"
echo "Choose an option:"
echo "--------------------------------------------------------------------"
echo ""
echo "1) Load ALL projects (recommended for first time)"
echo "2) Load SOFTWARE projects only (ANG, AZ, MDP)"
echo "3) Load KEY projects (ANG, AZ, OPS)"
echo "4) I'll edit .env manually"
echo ""

read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        PROJECT_KEYS="ANG,MDP,AZ,CS,CLIEN,SECOPS,OPS,FIN,GRC,IT"
        echo -e "${GREEN}✅ Will load ALL projects${NC}"
        ;;
    2)
        PROJECT_KEYS="ANG,AZ,MDP"
        echo -e "${GREEN}✅ Will load SOFTWARE projects${NC}"
        ;;
    3)
        PROJECT_KEYS="ANG,AZ,OPS"
        echo -e "${GREEN}✅ Will load KEY projects${NC}"
        ;;
    4)
        echo -e "${BLUE}ℹ️  Please edit .env file manually${NC}"
        echo "   Add this line:"
        echo "   JIRA_PROJECTS=YOUR,PROJECT,KEYS"
        echo ""
        echo "   Then run: python load_jira.py"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Update .env file
echo ""
echo "Updating .env file..."

# Check if JIRA_PROJECTS line exists
if grep -q "^JIRA_PROJECTS=" .env; then
    # Update existing line
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^JIRA_PROJECTS=.*/JIRA_PROJECTS=$PROJECT_KEYS/" .env
    else
        # Linux
        sed -i "s/^JIRA_PROJECTS=.*/JIRA_PROJECTS=$PROJECT_KEYS/" .env
    fi
    echo -e "${GREEN}✅ Updated JIRA_PROJECTS in .env${NC}"
elif grep -q "^# JIRA_PROJECTS=" .env; then
    # Uncomment and update
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^# JIRA_PROJECTS=.*/JIRA_PROJECTS=$PROJECT_KEYS/" .env
    else
        sed -i "s/^# JIRA_PROJECTS=.*/JIRA_PROJECTS=$PROJECT_KEYS/" .env
    fi
    echo -e "${GREEN}✅ Added JIRA_PROJECTS to .env${NC}"
else
    # Add new line
    echo "JIRA_PROJECTS=$PROJECT_KEYS" >> .env
    echo -e "${GREEN}✅ Added JIRA_PROJECTS to .env${NC}"
fi

echo ""
echo "--------------------------------------------------------------------"
echo "📋 Ready to load Jira issues"
echo "--------------------------------------------------------------------"
echo ""

read -p "Load Jira issues now? (y/n): " load_now

if [[ "$load_now" == "y" || "$load_now" == "Y" ]]; then
    echo ""
    echo "============================================================================"
    echo "📥 LOADING JIRA ISSUES"
    echo "============================================================================"
    echo ""
    
    source venv/bin/activate
    python load_jira.py
    
    echo ""
    echo "============================================================================"
    echo "🎉 SUCCESS!"
    echo "============================================================================"
    echo ""
    echo "✅ Jira issues loaded into knowledge base"
    echo ""
    echo "📋 What's Next:"
    echo ""
    echo "1️⃣  Start the application:"
    echo "   ./run_all.sh"
    echo ""
    echo "2️⃣  Access your applications:"
    echo "   • Frontend: http://localhost:5173"
    echo "   • Backend:  http://localhost:8000"
    echo "   • Product Dashboard: open product_dashboard_fixed.html"
    echo ""
    echo "3️⃣  Ask questions about your Jira issues:"
    echo "   • 'What are the latest issues in project ANG?'"
    echo "   • 'Show me all high priority bugs'"
    echo "   • 'What has been worked on recently?'"
    echo ""
    echo "============================================================================"
    echo ""
else
    echo ""
    echo -e "${YELLOW}ℹ️  When you're ready, run:${NC}"
    echo "   python load_jira.py"
    echo ""
    echo "   Then start the application:"
    echo "   ./run_all.sh"
    echo ""
fi

