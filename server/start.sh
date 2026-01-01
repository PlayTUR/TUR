#!/bin/bash
cd "$(dirname "$0")"

# Simply activate existing venv and run
# Use the root project venv
source ../venv/bin/activate
python3 main.py
