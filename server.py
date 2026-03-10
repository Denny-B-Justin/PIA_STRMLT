from flask import Flask
import os

server = Flask(__name__)
server.secret_key = os.getenv("SECRET_KEY")