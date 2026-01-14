#!/usr/bin/env python
"""
Setup script for Portal de Operaciones (Scripting Batch)

This script automates the installation and configuration of the application:
- Installs Python dependencies from requirements.txt
- Creates necessary directories
- Initializes the database with required tables
- Creates a default admin user
- Sets up environment configuration

Usage:
    python setup.py

Requirements:
    - Python 3.8 or higher
    - pip (Python package installer)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_header(message):
    """Print a formatted header message"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")


def print_success(message):
    """Print a success message"""
    print(f"✓ {message}")


def print_error(message):
    """Print an error message"""
    print(f"✗ ERROR: {message}")


def print_warning(message):
    """Print a warning message"""
    print(f"⚠ WARNING: {message}")


def print_info(message):
    """Print an info message"""
    print(f"ℹ {message}")


def check_python_version():
    """Verify Python version meets minimum requirements"""
    print_header("Checking Python Version")
    
    min_version = (3, 8)
    current_version = sys.version_info[:2]
    
    print_info(f"Current Python version: {sys.version.split()[0]}")
    print_info(f"Minimum required version: {'.'.join(map(str, min_version))}")
    
    if current_version < min_version:
        print_error(f"Python {'.'.join(map(str, min_version))} or higher is required")
        print_error(f"You are using Python {'.'.join(map(str, current_version))}")
        return False
    
    print_success("Python version check passed")
    return True


def check_pip():
    """Verify pip is installed"""
    print_header("Checking pip Installation")
    
    try:
        import pip
        print_info(f"pip version: {pip.__version__}")
        print_success("pip is installed")
        return True
    except ImportError:
        print_error("pip is not installed")
        print_info("Please install pip: https://pip.pypa.io/en/stable/installation/")
        return False


def install_dependencies():
    """Install Python packages from requirements.txt"""
    print_header("Installing Python Dependencies")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"requirements.txt not found at {requirements_file}")
        return False
    
    print_info(f"Reading dependencies from: {requirements_file}")
    
    try:
        # Read requirements to show what will be installed
        with open(requirements_file, 'r') as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print_info(f"Found {len(packages)} packages to install:")
        for pkg in packages:
            print(f"  - {pkg}")
        
        # Install packages
        print_info("\nInstalling packages (this may take a few minutes)...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_error("Failed to install dependencies")
            print(result.stderr)
            return False
        
        print_success("All dependencies installed successfully")
        return True
        
    except Exception as e:
        print_error(f"Error installing dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories for the application"""
    print_header("Creating Directory Structure")
    
    base_dir = Path(__file__).parent
    
    # Define required directories
    directories = [
        base_dir / "static",
        base_dir / "static" / "css",
        base_dir / "static" / "js",
        base_dir / "templates",
        base_dir / "instance",  # For SQLite database and other instance-specific files
    ]
    
    for directory in directories:
        if directory.exists():
            print_info(f"Directory already exists: {directory.relative_to(base_dir)}")
        else:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print_success(f"Created directory: {directory.relative_to(base_dir)}")
            except Exception as e:
                print_error(f"Failed to create directory {directory}: {e}")
                return False
    
    print_success("Directory structure verified")
    return True


def setup_environment():
    """Create .env file from .env.example if it doesn't exist"""
    print_header("Setting Up Environment Configuration")
    
    base_dir = Path(__file__).parent
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    
    if env_file.exists():
        print_info(f".env file already exists at: {env_file}")
        print_warning("Review your .env file to ensure all settings are correct")
        return True
    
    if not env_example.exists():
        print_warning(f".env.example not found, creating minimal .env file")
        
        # Create a minimal .env file
        minimal_env = """# Configuración de la aplicación
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///operations.db

# Configuración del servidor SMB (opcional)
SMB_SERVER_NAME=servidor-smb
SMB_SERVER_IP=192.168.1.100
SMB_SHARE_NAME=orexplore_data
SMB_USERNAME=usuario
SMB_PASSWORD=contraseña
SMB_DOMAIN=WORKGROUP

# URLs externas configurables
TELEMETRY_URL=http://example.com/telemetry
MINERALS_URL=http://172.16.11.155:8005/get_html
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(minimal_env)
            print_success(f"Created .env file at: {env_file}")
        except Exception as e:
            print_error(f"Failed to create .env file: {e}")
            return False
    else:
        # Copy from example
        try:
            shutil.copy2(env_example, env_file)
            print_success(f"Created .env from .env.example")
        except Exception as e:
            print_error(f"Failed to copy .env.example to .env: {e}")
            return False
    
    print_warning("IMPORTANT: Review and update the .env file with your configuration")
    print_info(f"Edit: {env_file}")
    return True


def initialize_database():
    """Initialize the database and create default admin user"""
    print_header("Initializing Database")
    
    try:
        # Import after dependencies are installed
        # Use a subprocess to run the database initialization in a fresh Python environment
        init_script = """
import sys
sys.path.insert(0, '.')
from app import app, db
from models import User

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print('CREATED_ADMIN')
    else:
        print('ADMIN_EXISTS')
"""
        
        print_info("Creating database tables...")
        result = subprocess.run(
            [sys.executable, "-c", init_script],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print_error(f"Failed to initialize database: {result.stderr}")
            return False
        
        output = result.stdout.strip()
        print_success("Database tables created successfully")
        
        if 'CREATED_ADMIN' in output:
            print_success("Default admin user created")
            print_warning("Default credentials - Username: admin, Password: admin")
            print_warning("IMPORTANT: Change the admin password after first login!")
        elif 'ADMIN_EXISTS' in output:
            print_info("Default admin user already exists")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        return False


def verify_installation():
    """Verify the installation is complete"""
    print_header("Verifying Installation")
    
    base_dir = Path(__file__).parent
    
    # Check for required files
    required_files = [
        "app.py",
        "config.py",
        "models.py",
        "requirements.txt",
        ".env"
    ]
    
    all_files_present = True
    for filename in required_files:
        file_path = base_dir / filename
        if file_path.exists():
            print_success(f"Found: {filename}")
        else:
            print_error(f"Missing: {filename}")
            all_files_present = False
    
    # Check for database
    db_path = base_dir / "operations.db"
    db_path_instance = base_dir / "instance" / "operations.db"
    if db_path.exists():
        print_success(f"Database created: {db_path.name}")
    elif db_path_instance.exists():
        print_success(f"Database created: instance/{db_path_instance.name}")
    else:
        print_warning("Database file not found (will be created on first run)")
    
    # Try to import main modules using subprocess to ensure fresh environment
    print_info("Verifying Python packages...")
    verify_script = """
try:
    import flask
    import flask_sqlalchemy
    import flask_login
    import smb  # pysmb installs as 'smb'
    import dotenv
    print('SUCCESS')
except ImportError as e:
    print(f'IMPORT_ERROR:{e}')
"""
    
    result = subprocess.run(
        [sys.executable, "-c", verify_script],
        capture_output=True,
        text=True
    )
    
    if 'SUCCESS' in result.stdout:
        print_success("All required Python packages are importable")
    else:
        print_error(f"Some packages cannot be imported: {result.stdout.strip()}")
        all_files_present = False
    
    return all_files_present


def print_next_steps():
    """Print instructions for next steps"""
    print_header("Installation Complete!")
    
    print("Next steps to run the application:\n")
    
    print("1. Review and configure your .env file:")
    print("   - Set a strong SECRET_KEY")
    print("   - Configure SMB server settings if needed")
    print("   - Update external URLs as needed\n")
    
    print("2. Start the application:")
    print("   python app.py\n")
    
    print("3. Access the application:")
    print("   Open your browser and go to: http://localhost:5000\n")
    
    print("4. Login with default credentials:")
    print("   Username: admin")
    print("   Password: admin")
    print("   ⚠ IMPORTANT: Change this password immediately!\n")
    
    print("5. For development mode:")
    print("   export FLASK_ENV=development  # Linux/Mac")
    print("   set FLASK_ENV=development     # Windows")
    print("   python app.py\n")
    
    print("For more information, see README.md")
    print("=" * 70 + "\n")


def main():
    """Main setup function"""
    print("\n" + "=" * 70)
    print("  Portal de Operaciones - Setup Script")
    print("  Sistema de gestión de operaciones de escaneo")
    print("=" * 70 + "\n")
    
    # Run setup steps
    steps = [
        ("Python Version Check", check_python_version),
        ("pip Check", check_pip),
        ("Install Dependencies", install_dependencies),
        ("Create Directories", create_directories),
        ("Setup Environment", setup_environment),
        ("Initialize Database", initialize_database),
        ("Verify Installation", verify_installation),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print_error(f"Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    # Summary
    print_header("Setup Summary")
    
    if failed_steps:
        print_error(f"Setup completed with {len(failed_steps)} error(s)")
        print("\nFailed steps:")
        for step in failed_steps:
            print(f"  ✗ {step}")
        print("\nPlease fix the errors and run setup.py again")
        return 1
    else:
        print_success("All setup steps completed successfully!")
        print_next_steps()
        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
