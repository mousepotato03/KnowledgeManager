#!/usr/bin/env python3
"""
Test drag and drop functionality
"""

import tkinter as tk
from pathlib import Path

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
    print("tkinterdnd2 is available")
except ImportError:
    DND_AVAILABLE = False
    print("tkinterdnd2 is NOT available")

def test_basic_gui():
    """Test basic drag and drop GUI"""
    if DND_AVAILABLE:
        try:
            root = TkinterDnD.Tk()
            print("TkinterDnD.Tk() created successfully")
        except:
            root = tk.Tk()
            print("Fallback to regular tk.Tk()")
    else:
        root = tk.Tk()
        print("Using regular tk.Tk()")
    
    root.title("Drag and Drop Test")
    root.geometry("400x200")
    
    # Create drag and drop frame
    dnd_frame = tk.Frame(root, height=100, bg='#f0f0f0', relief='groove', bd=2)
    dnd_frame.pack(fill='both', expand=True, padx=20, pady=20)
    dnd_frame.pack_propagate(False)
    
    # Create label
    dnd_label = tk.Label(
        dnd_frame, 
        text="Drop files here\n(Test)",
        bg='#f0f0f0',
        fg='#666666',
        font=('Arial', 12),
        justify=tk.CENTER
    )
    dnd_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    def on_file_drop(event):
        """Handle file drop event"""
        try:
            files = root.tk.splitlist(event.data)
            if files:
                file_path = files[0]
                dnd_label.config(
                    text=f"File dropped:\n{Path(file_path).name}",
                    fg='#008000'
                )
                print(f"File dropped: {file_path}")
        except Exception as e:
            print(f"Error handling file drop: {e}")
    
    def on_drag_enter(event):
        """Handle drag enter"""
        dnd_frame.config(bg='#e6f3ff', relief='solid')
        dnd_label.config(bg='#e6f3ff', text="Drop file here", fg='#0066cc')
        print("Drag enter")
    
    def on_drag_leave(event):
        """Handle drag leave"""
        dnd_frame.config(bg='#f0f0f0', relief='groove')
        dnd_label.config(bg='#f0f0f0', text="Drop files here\n(Test)", fg='#666666')
        print("Drag leave")
    
    # Enable drag and drop if available
    if DND_AVAILABLE:
        try:
            dnd_frame.drop_target_register(DND_FILES)
            dnd_frame.dnd_bind('<<Drop>>', on_file_drop)
            dnd_frame.dnd_bind('<<DragEnter>>', on_drag_enter)
            dnd_frame.dnd_bind('<<DragLeave>>', on_drag_leave)
            print("Drag and drop events bound successfully")
        except Exception as e:
            print(f"Failed to bind drag and drop events: {e}")
    else:
        dnd_label.config(text="Drag and drop not available\n(tkinterdnd2 not installed)")
    
    # Close button
    close_btn = tk.Button(root, text="Close", command=root.quit)
    close_btn.pack(pady=10)
    
    print("Starting GUI test...")
    print("   - Drag files to the window to test")
    print("   - Click 'Close' button to exit")
    
    try:
        root.mainloop()
        print("GUI test completed successfully")
    except Exception as e:
        print(f"GUI test failed: {e}")
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    test_basic_gui()