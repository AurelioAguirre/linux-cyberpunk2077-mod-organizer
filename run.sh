#!/bin/bash
set -e

if [ ! -d "myenv" ]; then
    echo "Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

myenv/bin/python src/main.py
