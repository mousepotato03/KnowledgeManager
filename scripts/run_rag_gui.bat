@echo off
echo Starting FlowGenius RAG Knowledge Uploader GUI...

:: Check if we're in the right directory
if not exist "src\rag_gui.py" (
    echo Error: rag_gui.py not found. Please run this script from the KnowledgeManager directory.
    pause
    exit /b 1
)

:: Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

:: Install/upgrade dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Warning: Some dependencies may not have been installed correctly.
    echo The GUI may still work if core dependencies are already installed.
    pause
)

:: Check for .env file
if not exist ".env" (
    echo Warning: .env file not found.
    echo Please create a .env file with the following variables:
    echo   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
    echo   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
    echo   GOOGLE_API_KEY=your_google_ai_key
    echo.
    echo Press any key to continue anyway, or Ctrl+C to exit and create .env file first.
    pause
)

:: Change to src directory and run GUI
cd src
echo Starting GUI...
python rag_gui.py

:: Return to original directory
cd ..

echo GUI application closed.
pause