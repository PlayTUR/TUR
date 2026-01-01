#!/bin/bash
cd "$(dirname "$0")"

# Simply activate existing venv and run
source .venv/bin/activate
python3 main.py
