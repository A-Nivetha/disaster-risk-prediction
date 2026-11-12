@echo off
rem Starts the dashboard. First run creates .venv and installs requirements.txt (slow, needs internet).
rem Later runs skip the install and start in seconds.
cd /d "%~dp0"

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" || (
  echo Python 3.11 or newer was not found on PATH. Install it from python.org, then run this file again.
  pause & exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating .venv ...
  python -m venv .venv || (pause & exit /b 1)
)

if not exist ".venv\.deps_installed" (
  echo Installing requirements. This takes several minutes the first time only.
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || (pause & exit /b 1)
  echo ok> ".venv\.deps_installed"
)

set "DISASTER_HISTORY_MODE=local"
".venv\Scripts\python.exe" -m streamlit run dashboard\Home.py
pause
