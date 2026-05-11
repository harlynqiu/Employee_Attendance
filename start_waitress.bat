@echo off

cd /d C:\Users\harly\Documents\Employee_Attendance

call venv\Scripts\activate.bat

python -m waitress --listen=0.0.0.0:8000 EmployeeAttendance.wsgi:application