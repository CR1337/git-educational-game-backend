#!/bin/bash

python3 initialize.py
python3 orchestrator.py --daemon &
uvicorn api:app --host 0.0.0.0 --port 8000
