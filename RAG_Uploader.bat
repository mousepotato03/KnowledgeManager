@echo off
title FlowGenius RAG Knowledge Uploader

:: Change to the script directory
cd /d "%~dp0"

:: Run the GUI
call scripts\run_rag_gui.bat

pause