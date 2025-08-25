#!/bin/bash
# Linux/macOS shell script for RAG indexing
# Usage: ./run_rag_indexing.sh [command] [arguments]

set -e  # Exit on error

# Change to script directory
cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FlowGenius RAG Indexing Pipeline${NC}"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.8+ and ensure it's accessible as 'python3'"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.8+ is required (found $python_version)${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
fi

# Install dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/supabase/__init__.py" ] && [ ! -f "venv/lib/python*/site-packages/supabase.py" ]; then
    echo -e "${YELLOW}📚 Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies${NC}"
        exit 1
    fi
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo -e "${YELLOW}Please create .env file with required environment variables:${NC}"
    echo "  NEXT_PUBLIC_SUPABASE_URL=your_supabase_url"
    echo "  SUPABASE_SERVICE_ROLE_KEY=your_service_key"
    echo "  GOOGLE_API_KEY=your_google_ai_key"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the indexing script with all arguments
echo -e "${GREEN}🎯 Running RAG indexing...${NC}"
python3 run_rag_indexing.py "$@"
exit_code=$?

# Cleanup
deactivate

if [ $exit_code -ne 0 ]; then
    echo -e "${RED}❌ Script completed with errors (exit code: $exit_code)${NC}"
    exit $exit_code
else
    echo -e "${GREEN}✅ Script completed successfully${NC}"
fi