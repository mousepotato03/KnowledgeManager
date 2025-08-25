#!/usr/bin/env python3
"""
Silent GUI Launcher for RAG Knowledge Indexing
Launches the GUI without showing console window
"""

import subprocess
import sys
import os
from pathlib import Path

# Hide console window on Windows
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes
    
    # Hide the console window
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

# Change to the correct directory
current_dir = Path(__file__).parent
os.chdir(current_dir)

# Import and run the GUI
try:
    from rag_gui import main
    main()
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", f"Failed to start RAG Uploader:\n{str(e)}")
    root.destroy()
    sys.exit(1)