# app.py
import os
from flaskr import *
from flask import send_from_directory

app = create_app()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(threaded=True, port=5000)
