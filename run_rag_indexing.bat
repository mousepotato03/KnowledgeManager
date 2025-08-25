@echo off
REM Windows batch script for RAG indexing
REM Usage: run_rag_indexing.bat [command] [arguments]

setlocal enabledelayedexpansion

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
if not exist "venv\Lib\site-packages\supabase" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check for .env file
if not exist ".env" (
    echo Warning: .env file not found
    echo Please create .env file with required environment variables:
    echo   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
    echo   SUPABASE_SERVICE_ROLE_KEY=your_service_key  
    echo   GOOGLE_API_KEY=your_google_ai_key
    pause
)

REM Run the indexing script with all arguments
python run_rag_indexing.py %*

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Script completed with errors. Press any key to exit.
    pause >nul
)

REM Deactivate virtual environment
deactivate