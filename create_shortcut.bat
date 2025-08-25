@echo off
echo Creating RAG Uploader shortcut on desktop...

:: Convert icon to ICO format if needed
echo Converting icon...
python convert_icon.py

set "current_dir=%CD%"
set "desktop=%USERPROFILE%\Desktop"
set "shortcut_name=RAG Knowledge Uploader"

:: Create VBS script to create shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > temp_shortcut.vbs
echo sLinkFile = "%desktop%\%shortcut_name%.lnk" >> temp_shortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> temp_shortcut.vbs
echo oLink.TargetPath = "%current_dir%\RAG_Uploader_Silent.vbs" >> temp_shortcut.vbs
echo oLink.WorkingDirectory = "%current_dir%" >> temp_shortcut.vbs
echo oLink.Description = "FlowGenius RAG Knowledge Uploader (Silent Mode)" >> temp_shortcut.vbs
if exist "%current_dir%\icon.ico" (
    echo oLink.IconLocation = "%current_dir%\icon.ico" >> temp_shortcut.vbs
) else (
    echo oLink.IconLocation = "shell32.dll,45" >> temp_shortcut.vbs
)
echo oLink.Save >> temp_shortcut.vbs

:: Execute VBS script
cscript temp_shortcut.vbs >nul 2>&1

:: Clean up
del temp_shortcut.vbs

echo Desktop shortcut '%shortcut_name%' has been created!
echo You can now double-click the shortcut on desktop to run RAG Uploader.
echo.
pause