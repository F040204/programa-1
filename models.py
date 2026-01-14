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


class Batch(db.Model):
    """Modelo para batches de escaneo de núcleos de perforación"""
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.Integer, nullable=False, index=True)  # Auto-incremented batch number
    hole_id = db.Column(db.String(100), nullable=False, index=True)  # Hole ID
    from_depth = db.Column(db.Float, nullable=False)  # From (profundidad inicial)
    to_depth = db.Column(db.Float, nullable=False)  # To (profundidad final)
    machine = db.Column(db.String(50), nullable=False, index=True)  # Machine name
    comments = db.Column(db.Text)  # Optional comments
    status = db.Column(db.String(20), default='pending', index=True)  # pending, validated, discrepancy
    validation_notes = db.Column(db.Text)
    validated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relación con datos de escaneo
    scan_data = db.relationship('ScanData', backref='batch', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Batch {self.batch_number} - {self.hole_id}>'
    
    def to_dict(self):
        """Convertir a diccionario para API JSON"""
        return {
            'id': self.id,
            'batch_number': self.batch_number,
            'hole_id': self.hole_id,
            'from_depth': self.from_depth,
            'to_depth': self.to_depth,
            'machine': self.machine,
            'comments': self.comments,
            'status': self.status,
            'validation_notes': self.validation_notes,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Keep Operation model for backward compatibility
class Operation(db.Model):
    """Modelo para operaciones de escaneo de núcleos de perforación"""
    __tablename__ = 'operations'
    
    id = db.Column(db.Integer, primary_key=True)
    core_id = db.Column(db.String(100), nullable=False, index=True)
    machine_id = db.Column(db.String(50), nullable=False, index=True)
    operator_name = db.Column(db.String(100), nullable=False)
    scan_date = db.Column(db.DateTime, nullable=False, default=utcnow)
    depth_from = db.Column(db.Float, nullable=False)
    depth_to = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, validated, discrepancy
    validation_notes = db.Column(db.Text)
    validated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    
    # Relación con datos de escaneo
    scan_data = db.relationship('ScanData', backref='operation', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Operation {self.core_id} - {self.machine_id}>'
    
    def to_dict(self):
        """Convertir a diccionario para API JSON"""
        return {
            'id': self.id,
            'core_id': self.core_id,
            'machine_id': self.machine_id,
            'operator_name': self.operator_name,
            'scan_date': self.scan_date.isoformat() if self.scan_date else None,
            'depth_from': self.depth_from,
            'depth_to': self.depth_to,
            'notes': self.notes,
            'status': self.status,
            'validation_notes': self.validation_notes,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ScanData(db.Model):
    """Modelo para datos de escaneo desde servidor SMB"""
    __tablename__ = 'scan_data'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_id = db.Column(db.Integer, db.ForeignKey('operations.id'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    source = db.Column(db.String(20), nullable=False)  # manual, smb
    file_path = db.Column(db.String(500))
    depth_from = db.Column(db.Float)
    depth_to = db.Column(db.Float)
    scan_quality = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    scan_metadata = db.Column(db.Text)  # Renamed from metadata to avoid conflict
    created_at = db.Column(db.DateTime, default=utcnow)
    
    def __repr__(self):
        return f'<ScanData {self.id} - {self.source}>'
    
    def to_dict(self):
        """Convertir a diccionario para API JSON"""
        return {
            'id': self.id,
            'operation_id': self.operation_id,
            'source': self.source,
            'file_path': self.file_path,
            'depth_from': self.depth_from,
            'depth_to': self.depth_to,
            'scan_quality': self.scan_quality,
            'file_size': self.file_size,
            'metadata': self.scan_metadata,  # Keep the same key in JSON output
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
