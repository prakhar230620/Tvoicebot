from datetime import datetime
from werkzeug.security import check_password_hash
from config.database import db

class User:
    def __init__(self, email, password=None, google_id=None, name=None, is_admin=None, created_at=None):
        self.email = email
        self.google_id = google_id
        self.name = name or 'Not provided'
        self.created_at = created_at or datetime.utcnow()
        self.is_admin = is_admin
        self._password = None
        
    def check_password(self, password):
        """Check password using Werkzeug's secure check"""
        if not self._password:
            return False
        return check_password_hash(self._password, password)

    @staticmethod
    def get_user_by_email(email):
        """Retrieve user from database by email"""
        user_data = db.users.find_one({'email': email})
        if user_data:
            user = User(
                email=user_data['email'],
                google_id=user_data.get('google_id'),
                name=user_data.get('name', 'Not provided'),
                is_admin=user_data.get('is_admin', False),
                created_at=user_data.get('created_at', datetime.utcnow())
            )
            user._password = user_data.get('password')
            return user
        return None

    @staticmethod
    def get_user_by_google_id(google_id):
        """Retrieve user from database by Google ID"""
        user_data = db.users.find_one({'google_id': google_id})
        if user_data:
            user = User(
                email=user_data['email'],
                google_id=google_id,
                name=user_data.get('name', 'Not provided'),
                is_admin=user_data.get('is_admin', False),
                created_at=user_data.get('created_at', datetime.utcnow())
            )
            user._password = user_data.get('password')
            return user
        return None