#!/bin/zsh
# One command to run the app: sets up the Python environment on first run, then starts the API and opens the browser.
set -e
cd "$(dirname "$0")/ai-stack"
[ -x .venv/bin/uvicorn ] || ./setup.sh
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created ai-stack/.env. Add ANTHROPIC_API_KEY to it for live suggestions; without it the board still loads."
fi
(sleep 3 && open http://localhost:8000) &
exec .venv/bin/uvicorn server:app --port 8000
