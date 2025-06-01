@echo off
echo Starting Windows Service Manager GUI...
REM This uses the Python Launcher for Windows ('py'), which is generally preferred.
REM It should find an installed Python version.
REM The -u flag is for unbuffered Python output.
py -u python_gui/app_tk.py

REM Check if Python command itself failed or if script exited with error.
if errorlevel 1 (
    echo.
    echo The GUI application encountered an error, could not start, or Python (via 'py' launcher) was not found.
    pause
)
