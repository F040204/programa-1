import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///operations.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración SMB Server
    SMB_SERVER_NAME = os.environ.get('SMB_SERVER_NAME', 'servidor-smb')
    SMB_SERVER_IP = os.environ.get('SMB_SERVER_IP', '192.168.1.100')
    SMB_SHARE_NAME = os.environ.get('SMB_SHARE_NAME', 'orexplore_data')
    SMB_USERNAME = os.environ.get('SMB_USERNAME', '')
    SMB_PASSWORD = os.environ.get('SMB_PASSWORD', '')
    SMB_DOMAIN = os.environ.get('SMB_DOMAIN', 'WORKGROUP')
    
    # Configuración de la aplicación
    OPERATIONS_PER_PAGE = 20
