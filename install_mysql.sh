#!/bin/bash

echo "================================================"
echo "🗄️  MySQL Installation and Setup"
echo "================================================"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo ""
echo "Step 1: Installing MySQL via Homebrew..."
brew install mysql

echo ""
echo "Step 2: Starting MySQL service..."
brew services start mysql

echo ""
echo "Step 3: Waiting for MySQL to start..."
sleep 8

echo ""
echo "Step 4: Creating database 'client_0000000002'..."
mysql -uroot -e "CREATE DATABASE IF NOT EXISTS client_0000000002 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>&1

echo ""
echo "Step 5: Verifying database creation..."
mysql -uroot -e "SHOW DATABASES LIKE 'client_0000000002';" 2>&1

echo ""
echo "Step 6: Testing connection..."
mysql -uroot -e "SELECT 'Database connection successful!' as Status;" 2>&1

echo ""
echo "================================================"
echo "✅ MySQL setup complete!"
echo "================================================"
echo ""
echo "Database: client_0000000002"
echo "Username: root"
echo "Password: (none - default)"
echo ""
echo "To secure your MySQL installation, run:"
echo "  mysql_secure_installation"
echo ""
echo "Now restart your backend server:"
echo "  cd /Users/prashanthvanama/projects/mini-llm-assistant"
echo "  ./run_all.sh"
echo ""

