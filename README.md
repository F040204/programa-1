# Portal de Operaciones (Scripting Batch)

Sistema web de gestión y monitoreo de operaciones de escaneo de núcleos de perforación (drill cores) para máquinas Orexplore.

## Descripción

Portal de Operaciones es una aplicación web desarrollada en Python con Flask que permite:

- **Gestionar operaciones**: Crear, editar y eliminar registros de operaciones de escaneo
- **Monitoreo en tiempo real**: Visualizar el estado de todas las operaciones
- **Validación de datos**: Comparar datos ingresados manualmente con información del servidor SMB
- **Detección de discrepancias**: Identificar inconsistencias entre datos manuales y automáticos
- **Integración SMB**: Sincronización automática con servidor de archivos compartidos
- **Dashboard**: Estadísticas y reportes visuales

## Objetivo General

Proporcionar una plataforma centralizada para el registro, seguimiento y validación de operaciones de escaneo de núcleos de perforación, asegurando la integridad y consistencia de los datos entre lo ingresado por operadores y lo generado por las máquinas.

## Objetivos Específicos

### Trazabilidad Completa
- Registro detallado de cada batch escaneado
- Identificación de hoyo, máquina y profundidades
- Timestamp de cada operación

### Control de Calidad
- Validación automática de datos contra servidor SMB
- Detección visual de discrepancias (resaltado en rojo)
- Sistema de estados (correcto/incorrecto)

### Monitoreo en Tiempo Real
- Visualización de metros escaneados totales
- Gráficos de progreso diario y mensual
- Estado de conectividad del servidor

### Gestión Segura
- Sistema de autenticación de usuarios
- Control de sesiones
- Protección contra ataques (rate limiting, validación de entrada)

## Características

### Gestión de Operaciones
- Registro manual de operaciones de escaneo
- Información detallada: ID de núcleo, máquina, operador, fecha, profundidad
- Estados: Pendiente, Validado, Con Discrepancias
- Historial completo de operaciones

### Validación Automática
- Integración con servidor SMB para obtener datos de máquinas Orexplore
- Comparación automática de datos manuales vs. datos del servidor
- Detección de discrepancias en profundidades y archivos
- Notas de validación detalladas

### Interfaz Web
- Dashboard con estadísticas en tiempo real
- Filtros y búsqueda de operaciones
- Paginación de resultados
- Diseño responsive y moderno

## Requisitos

- Python 3.8 o superior
- Flask 3.0.0
- SQLAlchemy
- pysmb (para integración SMB)
- Acceso a servidor SMB (opcional)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/F040204/programa-1.git
cd programa-1
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear archivo `.env` en la raíz del proyecto:
```env
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///operations.db

# Configuración SMB (opcional)
SMB_SERVER_NAME=servidor-smb
SMB_SERVER_IP=192.168.1.100
SMB_SHARE_NAME=orexplore_data
SMB_USERNAME=usuario
SMB_PASSWORD=contraseña
SMB_DOMAIN=WORKGROUP
```

5. Inicializar la base de datos:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Uso

### Iniciar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Crear una nueva operación

1. Ir a "Nueva Operación"
2. Completar el formulario con los datos del escaneo
3. Guardar la operación

### Validar una operación

1. Abrir el detalle de una operación
2. Hacer clic en "Validar con SMB"
3. El sistema comparará los datos con el servidor SMB
4. Ver el resultado de la validación

### Sincronizar con servidor SMB

1. Ir a "Sincronizar SMB"
2. Iniciar sincronización
3. El sistema detectará automáticamente nuevas operaciones

## Estructura del Proyecto

```
programa-1/
├── app.py                  # Aplicación principal Flask
├── config.py              # Configuración
├── models.py              # Modelos de base de datos
├── smb_utils.py           # Utilidades para servidor SMB
├── validation.py          # Lógica de validación
├── requirements.txt       # Dependencias
├── .gitignore            # Archivos ignorados por git
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── operations.html
│   ├── operation_detail.html
│   ├── new_operation.html
│   ├── edit_operation.html
│   ├── dashboard.html
│   └── sync_smb.html
└── static/              # Archivos estáticos
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## API REST

La aplicación incluye endpoints API para integración:

- `GET /api/operations` - Lista todas las operaciones
- `GET /api/operation/<id>` - Detalle de una operación

## Modelos de Datos

### Operation
- `id`: Identificador único
- `core_id`: ID del núcleo de perforación
- `machine_id`: ID de la máquina Orexplore
- `operator_name`: Nombre del operador
- `scan_date`: Fecha del escaneo
- `depth_from`: Profundidad inicial (metros)
- `depth_to`: Profundidad final (metros)
- `status`: Estado (pending, validated, discrepancy)
- `notes`: Notas adicionales
- `validation_notes`: Resultado de validación
- `validated_at`: Fecha de validación

### ScanData
- `id`: Identificador único
- `operation_id`: Referencia a operación
- `source`: Fuente de datos (manual, smb)
- `file_path`: Ruta del archivo
- `depth_from`: Profundidad inicial
- `depth_to`: Profundidad final
- `scan_quality`: Calidad del escaneo
- `file_size`: Tamaño del archivo
- `metadata`: Metadatos adicionales

## Configuración del Servidor SMB

Para habilitar la integración con servidor SMB:

1. Configurar las variables de entorno en `.env`
2. Asegurar conectividad de red con el servidor
3. Verificar permisos de lectura en el compartido
4. La estructura esperada en SMB es:
   ```
   /share_name/
   ├── MACHINE-01/
   │   ├── CORE-001/
   │   │   ├── scan_file_1.dat
   │   │   └── scan_file_2.dat
   │   └── CORE-002/
   └── MACHINE-02/
   ```

## Desarrollo

### Ejecutar en modo desarrollo

```bash
export FLASK_ENV=development
python app.py
```

### Estructura de base de datos

La base de datos se crea automáticamente al iniciar la aplicación. Para recrearla:

```bash
rm operations.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Licencia

Este proyecto es de código abierto.

## Contacto

Para soporte y consultas, contactar al equipo de desarrollo.