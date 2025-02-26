from functools import wraps
from flask import redirect, request, session, url_for
from config.user import User


def validate_session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user_id from URL parameters or session
        user_id = request.args.get('user_id') or session.get('user_id')

        if not user_id:
            # No user_id found, redirect to main app login
            return redirect('https://toolminesai.in/login')

        # Validate user against shared database
        user = User.get_user_by_email(user_id)
        if not user:
            # User not found in database, redirect to main app login
            return redirect('https://toolminesai.in/login')

        # Store user data in session
        session['user_id'] = user.email
        session['name'] = user.name
        session['is_admin'] = user.is_admin

        return f(*args, **kwargs)

    return decorated_function