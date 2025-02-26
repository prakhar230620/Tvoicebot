from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO
from flask_cors import CORS
from voicebot.voicebot import setup_voicebot_routes
from config.user import User
from config.database import db
from functools import wraps
from utils.auth_middleware import validate_session
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '14701c4d1e765347259951b561146a45'

# Configure CORS properly for production
CORS(app, resources={
    r"/*": {
        "origins": ["*"],  # In production, replace with your actual domain
        "supports_credentials": True
    }
})

# Initialize socketio with CORS settings
socketio = SocketIO(app, cors_allowed_origins="*")  # In production, replace with your actual domain


def validate_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.args.get('user_id')
        if not user_id:
            return redirect('http://localhost:5000/login')

        user = User.get_user_by_email(user_id)
        if not user:
            return redirect('http://localhost:5000/login')

        session['user_id'] = user.email
        session['name'] = user.name
        session['is_admin'] = user.is_admin

        return f(*args, **kwargs)

    return decorated_function

# Setup routes
setup_voicebot_routes(app, socketio)
# For local development
if __name__ == '__main__':
    app.run(debug=False,port=8081)