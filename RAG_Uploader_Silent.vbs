Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
currentDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the script directory and run Python GUI silently
objShell.CurrentDirectory = currentDir
objShell.Run "python src\rag_gui_silent.py", 0, False