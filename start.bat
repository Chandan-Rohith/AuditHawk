@echo off
echo Booting AuditHawk Pipeline...

:: 1. Start the Backend in a new window
start "AuditHawk Backend (Django)" cmd /k "cd backend && call .venv\Scripts\activate && python manage.py runserver"

:: 2. Start the Frontend in a new window
start "AuditHawk Frontend (Flask)" cmd /k "cd frontend_flask && python app.py"

echo Servers are booting up!