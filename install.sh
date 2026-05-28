#!/bin/bash
set -e

if ! command -v python3.12 &>/dev/null; then
    echo "Python 3.12 is required but was not found."
    echo "Please install Python 3.12 using your distribution's package manager and try again."
    exit 1
fi

echo "Creating virtual environment with Python 3.12..."
python3.12 -m venv myenv

echo "Installing dependencies..."
myenv/bin/pip install --upgrade pip -q
myenv/bin/pip install -r requirements.txt

echo ""
echo "Done. Run the app with: ./run.sh"
