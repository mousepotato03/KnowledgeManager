#!/bin/bash

echo "Starting FlowGenius RAG Knowledge Uploader GUI..."

# Check if we're in the right directory
if [ ! -f "src/rag_gui.py" ]; then
    echo "Error: rag_gui.py not found. Please run this script from the KnowledgeManager directory."
    read -p "Press any key to continue..."
    exit 1
fi

# Check for Python installation
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python is not installed or not in PATH."
        echo "Please install Python and try again."
        read -p "Press any key to continue..."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Using Python command: $PYTHON_CMD"

# Install/upgrade dependencies
echo "Installing/updating dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Warning: Some dependencies may not have been installed correctly."
    echo "The GUI may still work if core dependencies are already installed."
    read -p "Press any key to continue..."
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found."
    echo "Please create a .env file with the following variables:"
    echo "  NEXT_PUBLIC_SUPABASE_URL=your_supabase_url"
    echo "  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key"
    echo "  GOOGLE_API_KEY=your_google_ai_key"
    echo ""
    echo "Press any key to continue anyway, or Ctrl+C to exit and create .env file first."
    read -p ""
fi

# Change to src directory and run GUI
cd src
echo "Starting GUI..."
$PYTHON_CMD rag_gui.py

# Return to original directory
cd ..

echo "GUI application closed."
read -p "Press any key to continue..."