@echo off

cd /d %~dp0

call venv\Scripts\activate

waitress-serve --listen=0.0.0.0:8000 EmployeeAttendance.wsgi:application

pause