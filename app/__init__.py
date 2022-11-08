from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'SRKyycK9I35J1qzxPbKleSdDc4PreDlP'

    return app