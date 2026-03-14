"""
server.py
Minimal Flask server for the trial version.

Authentication (flask-login / auth.py) has been removed so the app runs
without any external service or .env configuration.
"""

from flask import Flask

server = Flask(__name__)
server.secret_key = "zambia-health-access-trial-2025"