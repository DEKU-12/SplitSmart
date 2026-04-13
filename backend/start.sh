#!/bin/bash
# Start the SplitSmart Python backend
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

echo "Starting SplitSmart backend on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
