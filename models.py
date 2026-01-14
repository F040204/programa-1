from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Operation(db.Model):
    """Modelo para operaciones de escaneo de núcleos de perforación"""
    __tablename__ = 'operations'
    
    id = db.Column(db.Integer, primary_key=True)
    core_id = db.Column(db.String(100), nullable=False, index=True)
    machine_id = db.Column(db.String(50), nullable=False, index=True)
    operator_name = db.Column(db.String(100), nullable=False)
    scan_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    depth_from = db.Column(db.Float, nullable=False)
    depth_to = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, validated, discrepancy
    validation_notes = db.Column(db.Text)
    validated_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    operation_id = db.Column(db.Integer, db.ForeignKey('operations.id'), nullable=False)
    source = db.Column(db.String(20), nullable=False)  # manual, smb
    file_path = db.Column(db.String(500))
    depth_from = db.Column(db.Float)
    depth_to = db.Column(db.Float)
    scan_quality = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    metadata = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
