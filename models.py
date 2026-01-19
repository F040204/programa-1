from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


def utcnow():
    """Get current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Modelo para usuarios del sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if account is locked due to failed attempts"""
        if self.locked_until and self.locked_until > utcnow():
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

