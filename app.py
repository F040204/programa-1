from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, timezone
from functools import wraps
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Importar db desde models y inicializar con app
from models import db, User, Batch, Operation, ScanData
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'

from smb_utils import SMBDataRetriever
from validation import DataValidator
from cache_utils import batches_cache, smb_cache


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
# BATCH MANAGEMENT ROUTES
# ============================================================================

@app.route('/')
@login_required
def index():
    """Página principal con resumen de batches"""
    # Try to get from cache
    cached_stats = batches_cache.get('dashboard_stats')
    if cached_stats:
        return render_template('index.html', **cached_stats)
    
    total_batches = Batch.query.count()
    pending_batches = Batch.query.filter_by(status='pending').count()
    validated_batches = Batch.query.filter_by(status='validated').count()
    discrepancy_batches = Batch.query.filter_by(status='discrepancy').count()
    
    recent_batches = Batch.query.order_by(Batch.created_at.desc()).limit(10).all()
    
    # Calculate total scanned meters
    from sqlalchemy import func
    total_meters = db.session.query(
        func.sum(Batch.to_depth - Batch.from_depth)
    ).filter(Batch.status.in_(['validated', 'discrepancy'])).scalar() or 0.0
    
    stats = {
        'total_batches': total_batches,
        'pending_batches': pending_batches,
        'validated_batches': validated_batches,
        'discrepancy_batches': discrepancy_batches,
        'recent_batches': recent_batches,
        'total_meters': round(total_meters, 2)
    }
    
    # Cache the stats
    batches_cache.set('dashboard_stats', stats)
    
    return render_template('index.html', **stats)


@app.route('/batches')
@login_required
def batches_list():
    """Lista todos los batches con paginación"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    
    query = Batch.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    batches = query.order_by(Batch.batch_number.desc()).paginate(
        page=page, per_page=app.config['BATCHES_PER_PAGE'], error_out=False
    )
    
    return render_template('batches.html', batches=batches, status_filter=status_filter)


@app.route('/batch/new', methods=['GET', 'POST'])
@login_required
def new_batch():
    """Crear un nuevo batch con validación en tiempo real"""
    if request.method == 'POST':
        try:
            # Get next batch number
            max_batch = db.session.query(db.func.max(Batch.batch_number)).scalar() or 0
            next_batch_number = max_batch + 1
            
            from_depth = float(request.form['from_depth'])
            to_depth = float(request.form['to_depth'])
            
            # Real-time validation
            if from_depth >= to_depth:
                flash('Error: La profundidad inicial debe ser menor que la final.', 'error')
                return render_template('new_batch.html')
            
            batch = Batch(
                batch_number=next_batch_number,
                hole_id=request.form['hole_id'],
                from_depth=from_depth,
                to_depth=to_depth,
                machine=request.form['machine'],
                comments=request.form.get('comments', ''),
                created_by=current_user.id
            )
            db.session.add(batch)
            db.session.commit()
            
            # Invalidate cache
            batches_cache.invalidate()
            
            flash('Batch creado exitosamente', 'success')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear batch: {str(e)}', 'error')
    
    return render_template('new_batch.html')


@app.route('/batch/<int:batch_id>')
@login_required
def batch_detail(batch_id):
    """Ver detalles de un batch específico"""
    batch = Batch.query.get_or_404(batch_id)
    scan_data = ScanData.query.filter_by(batch_id=batch_id).all()
    
    return render_template('batch_detail.html', batch=batch, scan_data=scan_data)


@app.route('/batch/<int:batch_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_batch(batch_id):
    """Editar un batch existente"""
    batch = Batch.query.get_or_404(batch_id)
    
    if request.method == 'POST':
        try:
            from_depth = float(request.form['from_depth'])
            to_depth = float(request.form['to_depth'])
            
            # Validation
            if from_depth >= to_depth:
                flash('Error: La profundidad inicial debe ser menor que la final.', 'error')
                return render_template('edit_batch.html', batch=batch)
            
            batch.hole_id = request.form['hole_id']
            batch.from_depth = from_depth
            batch.to_depth = to_depth
            batch.machine = request.form['machine']
            batch.comments = request.form.get('comments', '')
            batch.updated_at = utcnow()
            
            db.session.commit()
            
            # Invalidate cache
            batches_cache.invalidate()
            
            flash('Batch actualizado exitosamente', 'success')
            return redirect(url_for('batch_detail', batch_id=batch_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar batch: {str(e)}', 'error')
    
    return render_template('edit_batch.html', batch=batch)


@app.route('/batch/<int:batch_id>/delete', methods=['POST'])
@login_required
def delete_batch(batch_id):
    """Eliminar un batch con renumeración automática"""
    batch = Batch.query.get_or_404(batch_id)
    batch_num = batch.batch_number
    
    try:
        db.session.delete(batch)
        
        # Renumber all batches with higher numbers
        higher_batches = Batch.query.filter(Batch.batch_number > batch_num).all()
        for b in higher_batches:
            b.batch_number -= 1
        
        db.session.commit()
        
        # Invalidate cache
        batches_cache.invalidate()
        
        flash('Batch eliminado exitosamente y batches renumerados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar batch: {str(e)}', 'error')
    
    return redirect(url_for('batches_list'))


# ============================================================================
# STATUS CHECKER
# ============================================================================

@app.route('/status-checker')
@login_required
def status_checker():
    """Status checker page with two-section comparison"""
    page = request.args.get('page', 1, type=int)
    per_page = 30
    
    # Get operator data (batches)
    batches = Batch.query.order_by(Batch.batch_number.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Try to get SMB data from cache
    smb_connection_status = smb_cache.get('smb_status')
    smb_batches_data = smb_cache.get('smb_batches_data')
    
    if smb_batches_data is None:
        # Get SMB data
        try:
            smb_retriever = SMBDataRetriever(app.config)
            smb_operations = smb_retriever.scan_for_new_operations()
            smb_batches_data = smb_operations
            smb_connection_status = {
                'connected': True,
                'batches_found': len(smb_operations),
                'last_check': utcnow().isoformat()
            }
        except Exception as e:
            smb_batches_data = []
            smb_connection_status = {
                'connected': False,
                'error': str(e),
                'last_check': utcnow().isoformat()
            }
        
        # Cache the data
        smb_cache.set('smb_status', smb_connection_status)
        smb_cache.set('smb_batches_data', smb_batches_data)
    
    # Compare data and find discrepancies
    discrepancies = []
    for batch in batches.items:
        # Find matching SMB data
        matching_smb = None
        for smb_data in smb_batches_data:
            if (smb_data.get('core_id') == batch.hole_id and 
                smb_data.get('machine_id') == batch.machine):
                matching_smb = smb_data
                break
        
        if matching_smb:
            # Check for discrepancies
            has_discrepancy = False
            if abs(matching_smb.get('depth_from', 0) - batch.from_depth) > 0.1:
                has_discrepancy = True
            if abs(matching_smb.get('depth_to', 0) - batch.to_depth) > 0.1:
                has_discrepancy = True
            
            if has_discrepancy:
                discrepancies.append({
                    'batch': batch,
                    'smb_data': matching_smb
                })
    
    return render_template('status_checker.html', 
                         batches=batches,
                         smb_batches_data=smb_batches_data,
                         smb_connection_status=smb_connection_status,
                         discrepancies=discrepancies)


@app.route('/api/smb-status')
@login_required
def smb_status():
    """API endpoint for SMB connection status (polled every 30 seconds)"""
    status = smb_cache.get('smb_status')
    if status is None:
        try:
            smb_retriever = SMBDataRetriever(app.config)
            connected = smb_retriever.connect()
            smb_retriever.disconnect()
            
            status = {
                'connected': connected,
                'last_check': utcnow().isoformat()
            }
        except Exception as e:
            status = {
                'connected': False,
                'error': str(e),
                'last_check': utcnow().isoformat()
            }
        
        smb_cache.set('smb_status', status)
    
    return jsonify(status)


# ============================================================================
# STATISTICS & VISUALIZATION
# ============================================================================

@app.route('/statistics')
@login_required
def statistics():
    """Statistics page with daily and monthly charts"""
    from sqlalchemy import func
    
    # Total scanned meters
    total_meters = db.session.query(
        func.sum(Batch.to_depth - Batch.from_depth)
    ).filter(Batch.status.in_(['validated', 'discrepancy'])).scalar() or 0.0
    
    # Daily progress (by hour for today)
    today = utcnow().date()
    daily_data = db.session.query(
        func.strftime('%H', Batch.created_at).label('hour'),
        func.sum(Batch.to_depth - Batch.from_depth).label('meters')
    ).filter(
        func.date(Batch.created_at) == today
    ).group_by('hour').all()
    
    # Monthly progress (last 30 days)
    thirty_days_ago = utcnow() - timedelta(days=30)
    monthly_data = db.session.query(
        func.date(Batch.created_at).label('date'),
        func.sum(Batch.to_depth - Batch.from_depth).label('meters')
    ).filter(
        Batch.created_at >= thirty_days_ago
    ).group_by('date').all()
    
    return render_template('statistics.html',
                         total_meters=round(total_meters, 2),
                         daily_data=daily_data,
                         monthly_data=monthly_data)


# ============================================================================
# EXTERNAL INTEGRATIONS
# ============================================================================

@app.route('/telemetry')
@login_required
def telemetry():
    """Telemetry page with configurable URL"""
    telemetry_url = app.config['TELEMETRY_URL']
    return render_template('telemetry.html', telemetry_url=telemetry_url)


@app.route('/minerals')
@login_required
def minerals():
    """Redirect to minerals page"""
    return redirect(app.config['MINERALS_URL'])


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
        batch_count = Batch.query.count()
        health_status['database'] = {
            'status': 'healthy',
            'batch_count': batch_count
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
                operations = smb_retriever.scan_for_new_operations()
                batches_found = len(operations)
            else:
                batches_found = 0
            smb_retriever.disconnect()
            
            health_status['smb'] = {
                'status': 'healthy' if connected else 'disconnected',
                'batches_found': batches_found
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
# CACHE MANAGEMENT
# ============================================================================

@app.route('/api/cache/invalidate', methods=['POST'])
@login_required
def invalidate_cache():
    """Invalidate cache manually"""
    cache_type = request.json.get('type', 'all')
    
    if cache_type == 'batches' or cache_type == 'all':
        batches_cache.invalidate()
    
    if cache_type == 'smb' or cache_type == 'all':
        smb_cache.invalidate()
    
    return jsonify({
        'success': True,
        'message': f'Cache {cache_type} invalidated successfully'
    })


@app.route('/api/cache/stats')
@login_required
def cache_stats():
    """Get cache statistics"""
    return jsonify({
        'batches_cache': batches_cache.get_stats(),
        'smb_cache': smb_cache.get_stats()
    })


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/batches')
@login_required
def api_batches():
    """API para obtener batches en formato JSON"""
    batches = Batch.query.order_by(Batch.batch_number.desc()).all()
    return jsonify([batch.to_dict() for batch in batches])


@app.route('/api/batch/<int:batch_id>')
@login_required
def api_batch_detail(batch_id):
    """API para obtener detalles de un batch"""
    batch = Batch.query.get_or_404(batch_id)
    return jsonify(batch.to_dict())


# ============================================================================
# LEGACY ROUTES (for backward compatibility)
# ============================================================================

@app.route('/operations')
@login_required
def operations_list():
    """Legacy route - redirect to batches"""
    return redirect(url_for('batches_list'))


@app.route('/operation/new')
@login_required
def new_operation():
    """Legacy route - redirect to new batch"""
    return redirect(url_for('new_batch'))


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
