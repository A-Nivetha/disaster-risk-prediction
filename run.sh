#!/usr/bin/env sh
# Starts the dashboard. First run creates .venv and installs requirements.txt; later runs start in seconds.
cd "$(dirname "$0")" || exit 1
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" || { echo "Python 3.11 or newer is required."; exit 1; }
[ -x .venv/bin/python ] || python3 -m venv .venv || exit 1
if [ ! -f .venv/.deps_installed ]; then
  .venv/bin/python -m pip install -r requirements.txt || exit 1
  touch .venv/.deps_installed
fi
export DISASTER_HISTORY_MODE=local
exec .venv/bin/python -m streamlit run dashboard/Home.py
