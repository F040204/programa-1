from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, timezone
from functools import wraps
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Importar db desde models y inicializar con app
from models import db, User
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'

from smb_utils import SMBDataRetriever
from cache_utils import smb_cache


def utcnow():
    """Get current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Se requieren privilegios de administrador.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with rate limiting"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Check if account is locked
            if user.is_locked():
                remaining_time = (user.locked_until - utcnow()).total_seconds()
                flash(f'Cuenta bloqueada. Intente nuevamente en {int(remaining_time)} segundos.', 'error')
                return render_template('login.html')
            
            # Check password
            if user.check_password(password):
                # Reset failed attempts on successful login
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login = utcnow()
                db.session.commit()
                
                # Set session to be permanent with 24-hour expiration
                session.permanent = True
                login_user(user, remember=True)
                
                flash('Inicio de sesión exitoso.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account if max attempts reached
                if user.failed_login_attempts >= app.config['MAX_LOGIN_ATTEMPTS']:
                    user.locked_until = utcnow() + timedelta(seconds=app.config['LOCKOUT_DURATION'])
                    db.session.commit()
                    flash(f'Cuenta bloqueada por {app.config["LOCKOUT_DURATION"]//60} minutos debido a múltiples intentos fallidos.', 'error')
                else:
                    db.session.commit()
                    remaining = app.config['MAX_LOGIN_ATTEMPTS'] - user.failed_login_attempts
                    flash(f'Usuario o contraseña incorrectos. Intentos restantes: {remaining}', 'error')
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('login'))


@app.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create new user (admin only)"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'error')
            return render_template('create_user.html')
        
        # Create new user
        user = User(username=username, is_admin=is_admin)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {username} creado exitosamente.', 'success')
        return redirect(url_for('users_list'))
    
    return render_template('create_user.html')


@app.route('/users')
@admin_required
def users_list():
    """List all users (admin only)"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users_list.html', users=users)


# ============================================================================
# IMAGE VIEWER - MAIN FUNCTIONALITY
# ============================================================================

@app.route('/')
@login_required
def index():
    """Redirect to image viewer"""
    return redirect(url_for('image_viewer'))


@app.route('/image-viewer')
@login_required
def image_viewer():
    """Page to view PNG images from SMB folders"""
    # Try to get cached image list
    image_list = smb_cache.get('png_image_list')
    smb_connection_status = smb_cache.get('smb_status')
    
    if image_list is None:
        try:
            smb_retriever = SMBDataRetriever(app.config)
            image_list = smb_retriever.scan_for_png_images()
            smb_connection_status = {
                'connected': True,
                'images_found': len(image_list),
                'last_check': utcnow().isoformat()
            }
        except Exception as e:
            image_list = []
            smb_connection_status = {
                'connected': False,
                'error': str(e),
                'last_check': utcnow().isoformat()
            }
        
        # Cache the data
        smb_cache.set('png_image_list', image_list)
        smb_cache.set('smb_status', smb_connection_status)
    
    return render_template('image_viewer.html',
                         images=image_list,
                         smb_status=smb_connection_status)


@app.route('/api/image/<path:image_path>')
@login_required
def get_image(image_path):
    """Serve an image from SMB"""
    try:
        smb_retriever = SMBDataRetriever(app.config)
        image_data = smb_retriever.get_image_file(image_path)
        
        if image_data:
            return send_file(
                image_data,
                mimetype='image/png',
                as_attachment=False,
                download_name=os.path.basename(image_path)
            )
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh-images', methods=['POST'])
@login_required
def refresh_images():
    """Refresh the image list from SMB"""
    try:
        smb_retriever = SMBDataRetriever(app.config)
        image_list = smb_retriever.scan_for_png_images()
        
        # Update cache
        smb_cache.set('png_image_list', image_list)
        smb_cache.set('smb_status', {
            'connected': True,
            'images_found': len(image_list),
            'last_check': utcnow().isoformat()
        })
        
        return jsonify({
            'success': True,
            'images_found': len(image_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

@app.route('/api/cache/invalidate', methods=['POST'])
@login_required
def invalidate_cache():
    """Invalidate cache manually"""
    smb_cache.invalidate()
    
    return jsonify({
        'success': True,
        'message': 'Cache invalidated successfully'
    })


@app.route('/api/cache/stats')
@login_required
def cache_stats():
    """Get cache statistics"""
    return jsonify({
        'smb_cache': smb_cache.get_stats()
    })


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': utcnow().isoformat(),
        'database': {},
        'smb': {}
    }
    
    try:
        # Check database
        user_count = User.query.count()
        health_status['database'] = {
            'status': 'healthy',
            'user_count': user_count
        }
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['database'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Check SMB connection
    smb_status_data = smb_cache.get('smb_status')
    if smb_status_data is None:
        try:
            smb_retriever = SMBDataRetriever(app.config)
            connected = smb_retriever.connect()
            if connected:
                images = smb_retriever.scan_for_png_images()
                images_found = len(images)
            else:
                images_found = 0
            smb_retriever.disconnect()
            
            health_status['smb'] = {
                'status': 'healthy' if connected else 'disconnected',
                'images_found': images_found
            }
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['smb'] = {
                'status': 'error',
                'error': str(e)
            }
    else:
        health_status['smb'] = smb_status_data
    
    return jsonify(health_status)


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_db():
    """Inicializar la base de datos"""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if no users exist
        if User.query.count() == 0:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')  # Default password - should be changed
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created (username: admin, password: admin)")
        
        print("Base de datos inicializada")


if __name__ == '__main__':
    # Crear las tablas si no existen
    with app.app_context():
        db.create_all()
        
        # Create default admin user if no users exist
        if User.query.count() == 0:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created (username: admin, password: admin)")
    
    # Ejecutar la aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)
