from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Importar db desde models y inicializar con app
from models import db, Operation, ScanData
db.init_app(app)

from smb_utils import SMBDataRetriever
from validation import DataValidator


@app.route('/')
def index():
    """Página principal con resumen de operaciones"""
    total_operations = Operation.query.count()
    pending_operations = Operation.query.filter_by(status='pending').count()
    validated_operations = Operation.query.filter_by(status='validated').count()
    discrepancy_operations = Operation.query.filter_by(status='discrepancy').count()
    
    recent_operations = Operation.query.order_by(Operation.created_at.desc()).limit(10).all()
    
    return render_template('index.html',
                         total_operations=total_operations,
                         pending_operations=pending_operations,
                         validated_operations=validated_operations,
                         discrepancy_operations=discrepancy_operations,
                         recent_operations=recent_operations)


@app.route('/operations')
def operations_list():
    """Lista todas las operaciones con paginación"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', None)
    
    query = Operation.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    operations = query.order_by(Operation.created_at.desc()).paginate(
        page=page, per_page=app.config['OPERATIONS_PER_PAGE'], error_out=False
    )
    
    return render_template('operations.html', operations=operations, status_filter=status_filter)


@app.route('/operation/new', methods=['GET', 'POST'])
def new_operation():
    """Crear una nueva operación manualmente"""
    if request.method == 'POST':
        try:
            operation = Operation(
                core_id=request.form['core_id'],
                machine_id=request.form['machine_id'],
                operator_name=request.form['operator_name'],
                scan_date=datetime.strptime(request.form['scan_date'], '%Y-%m-%d'),
                depth_from=float(request.form['depth_from']),
                depth_to=float(request.form['depth_to']),
                notes=request.form.get('notes', '')
            )
            db.session.add(operation)
            db.session.commit()
            
            flash('Operación creada exitosamente', 'success')
            return redirect(url_for('operation_detail', operation_id=operation.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear operación: {str(e)}', 'error')
    
    return render_template('new_operation.html')


@app.route('/operation/<int:operation_id>')
def operation_detail(operation_id):
    """Ver detalles de una operación específica"""
    operation = Operation.query.get_or_404(operation_id)
    scan_data = ScanData.query.filter_by(operation_id=operation_id).all()
    
    return render_template('operation_detail.html', operation=operation, scan_data=scan_data)


@app.route('/operation/<int:operation_id>/validate', methods=['POST'])
def validate_operation(operation_id):
    """Validar una operación contra datos del servidor SMB"""
    operation = Operation.query.get_or_404(operation_id)
    
    try:
        # Recuperar datos del servidor SMB
        smb_retriever = SMBDataRetriever(app.config)
        smb_data = smb_retriever.get_operation_data(operation.core_id, operation.machine_id)
        
        # Guardar datos SMB si existen
        if smb_data:
            for data in smb_data:
                scan = ScanData(
                    operation_id=operation.id,
                    source='smb',
                    file_path=data.get('file_path', ''),
                    depth_from=data.get('depth_from', 0.0),
                    depth_to=data.get('depth_to', 0.0),
                    scan_quality=data.get('quality', 'unknown'),
                    file_size=data.get('file_size', 0),
                    scan_metadata=str(data.get('metadata', {}))
                )
                db.session.add(scan)
        
        # Validar datos
        validator = DataValidator()
        validation_result = validator.validate_operation(operation, smb_data)
        
        # Actualizar estado de la operación
        operation.validation_notes = validation_result['message']
        if validation_result['has_discrepancies']:
            operation.status = 'discrepancy'
            flash('Validación completada: Se encontraron discrepancias', 'warning')
        else:
            operation.status = 'validated'
            flash('Validación exitosa: Los datos son consistentes', 'success')
        
        operation.validated_at = datetime.utcnow()
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error durante la validación: {str(e)}', 'error')
    
    return redirect(url_for('operation_detail', operation_id=operation_id))


@app.route('/operation/<int:operation_id>/edit', methods=['GET', 'POST'])
def edit_operation(operation_id):
    """Editar una operación existente"""
    operation = Operation.query.get_or_404(operation_id)
    
    if request.method == 'POST':
        try:
            operation.core_id = request.form['core_id']
            operation.machine_id = request.form['machine_id']
            operation.operator_name = request.form['operator_name']
            operation.scan_date = datetime.strptime(request.form['scan_date'], '%Y-%m-%d')
            operation.depth_from = float(request.form['depth_from'])
            operation.depth_to = float(request.form['depth_to'])
            operation.notes = request.form.get('notes', '')
            operation.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Operación actualizada exitosamente', 'success')
            return redirect(url_for('operation_detail', operation_id=operation_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar operación: {str(e)}', 'error')
    
    return render_template('edit_operation.html', operation=operation)


@app.route('/operation/<int:operation_id>/delete', methods=['POST'])
def delete_operation(operation_id):
    """Eliminar una operación"""
    operation = Operation.query.get_or_404(operation_id)
    
    try:
        db.session.delete(operation)
        db.session.commit()
        flash('Operación eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar operación: {str(e)}', 'error')
    
    return redirect(url_for('operations_list'))


@app.route('/api/operations')
def api_operations():
    """API para obtener operaciones en formato JSON"""
    operations = Operation.query.order_by(Operation.created_at.desc()).all()
    return jsonify([op.to_dict() for op in operations])


@app.route('/api/operation/<int:operation_id>')
def api_operation_detail(operation_id):
    """API para obtener detalles de una operación"""
    operation = Operation.query.get_or_404(operation_id)
    return jsonify(operation.to_dict())


@app.route('/sync-smb', methods=['GET', 'POST'])
def sync_smb():
    """Sincronizar datos desde el servidor SMB"""
    if request.method == 'POST':
        try:
            smb_retriever = SMBDataRetriever(app.config)
            results = smb_retriever.scan_for_new_operations()
            
            new_operations = 0
            for result in results:
                # Verificar si ya existe una operación con este core_id
                existing = Operation.query.filter_by(
                    core_id=result['core_id'],
                    machine_id=result['machine_id']
                ).first()
                
                if not existing:
                    operation = Operation(
                        core_id=result['core_id'],
                        machine_id=result['machine_id'],
                        operator_name='Auto-detected',
                        scan_date=result.get('scan_date', datetime.utcnow()),
                        depth_from=result.get('depth_from', 0.0),
                        depth_to=result.get('depth_to', 0.0),
                        notes='Detectado automáticamente desde servidor SMB',
                        status='pending'
                    )
                    db.session.add(operation)
                    new_operations += 1
            
            db.session.commit()
            flash(f'Sincronización completada: {new_operations} nuevas operaciones detectadas', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error durante la sincronización: {str(e)}', 'error')
        
        return redirect(url_for('index'))
    
    return render_template('sync_smb.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard con estadísticas y gráficos"""
    from sqlalchemy import func
    
    # Estadísticas por estado
    stats = {
        'pending': Operation.query.filter_by(status='pending').count(),
        'validated': Operation.query.filter_by(status='validated').count(),
        'discrepancy': Operation.query.filter_by(status='discrepancy').count()
    }
    
    # Operaciones por máquina
    operations_by_machine = db.session.query(
        Operation.machine_id,
        func.count(Operation.id)
    ).group_by(Operation.machine_id).all()
    
    return render_template('dashboard.html', stats=stats, operations_by_machine=operations_by_machine)


# Inicializar la base de datos
def init_db():
    """Inicializar la base de datos"""
    with app.app_context():
        db.create_all()
        print("Base de datos inicializada")


if __name__ == '__main__':
    # Crear las tablas si no existen
    with app.app_context():
        db.create_all()
    
    # Ejecutar la aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)
