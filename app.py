# app.py
import os
from flaskr import *
from flask import send_from_directory, g


app = create_app()

if __name__ == '__main__':
    app.run(threaded=True, port=5000)
