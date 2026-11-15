@echo off
cd /d "%~dp0"
python src\qa_workspace.py --open
if errorlevel 1 pause
