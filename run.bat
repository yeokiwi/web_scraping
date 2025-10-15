@echo off

REM Install Flask if not already installed
python -m pip install flask --quiet
python -m pip install flask-cors --quiet

REM Run the Markdown-only Flask server
start "" "http://127.0.0.1:5000"
python law_fetcher.py

