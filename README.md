# Portal de Operaciones (Scripting Batch)

Sistema web de gestión y monitoreo de operaciones de escaneo de núcleos de perforación (drill cores) para máquinas Orexplore.

## 🆕 Características Principales (v2.0)

### 🔐 Sistema de Autenticación Completo
- Login/Logout seguro con contraseñas hasheadas
- Sesiones persistentes con tiempo de expiración (24 horas)
- Rate limiting (máximo 5 intentos fallidos, bloqueo de 5 minutos)
- Creación de usuarios por administradores
- Usuario por defecto: `admin` / `admin` (debe cambiarse en producción)

### 📊 Gestión de Batches
- Registro de nuevos batches con validación en tiempo real
- Edición de batches existentes
- Eliminación con renumeración automática
- Paginación (30 items por página)
- Campos: Hole ID, From (m), To (m), Machine, Comentarios

### 🔍 Status Checker
- Comparación automática entre datos ingresados y datos del servidor SMB
- Tabla con dos secciones: "Ingresado en OP" y "Ingresado en Máquina"
- Resaltado visual de discrepancias en rojo
- Indicador de conexión SMB con actualización cada 30 segundos

### 📈 Visualización de Estadísticas
- Contador total de metros escaneados
- Gráfico de progreso diario (por hora)
- Gráfico de progreso mensual (últimos 30 días)
- Actualización automática

### 🔗 Integración con Sistemas Externos
- Página de telemetría (URL configurable)
- Enlace a minerales: http://172.16.11.155:8005/get_html

### 🏥 Health Check
- Endpoint `/health` que proporciona:
  - Estado general del sistema (healthy/degraded)
  - Estado de la base de datos (cantidad de batches)
  - Estado de conexión SMB
  - Timestamp de verificación
  - Formato JSON para integración con herramientas de monitoreo

### 🗄️ Sistema de Caché
- Caché automático de datos (TTL: 30 segundos)
- Thread-safe con locks
- Endpoint de invalidación: `POST /api/cache/invalidate`

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

### Método 1: Instalación Automática (Recomendado)

La forma más fácil de instalar y configurar la aplicación es usando el script de instalación automático:

1. Clonar el repositorio:
```bash
git clone https://github.com/F040204/programa-1.git
cd programa-1
```

2. Crear entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Ejecutar el script de instalación:
```bash
python setup.py
```

El script automáticamente:
- ✓ Verifica la versión de Python
- ✓ Instala todas las dependencias desde requirements.txt
- ✓ Crea los directorios necesarios
- ✓ Crea el archivo .env desde .env.example
- ✓ Inicializa la base de datos
- ✓ Crea el usuario administrador por defecto

### Método 2: Instalación Manual

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

### Primer acceso

1. Navegar a `http://localhost:5000`
2. Iniciar sesión con las credenciales por defecto:
   - **Usuario**: `admin`
   - **Contraseña**: `admin`
3. **IMPORTANTE**: Cambiar la contraseña del administrador después del primer acceso

### Crear un nuevo batch

1. Ir a "Nuevo Batch" en el menú
2. Completar el formulario:
   - **Hole ID**: Identificador del hoyo (ej: DDH-001)
   - **From (m)**: Profundidad inicial en metros
   - **To (m)**: Profundidad final en metros
   - **Machine**: Nombre de la máquina (ej: OREX-01)
   - **Comentarios**: Notas opcionales
3. Hacer clic en "Crear Batch"

### Verificar el estado con Status Checker

1. Ir a "Status Checker" en el menú
2. Ver la comparación entre datos ingresados y datos del servidor SMB
3. Las discrepancias se resaltan en rojo
4. El indicador de conexión SMB se actualiza cada 30 segundos

### Ver estadísticas

1. Ir a "Estadísticas" en el menú
2. Ver el total de metros escaneados
3. Analizar gráficos de progreso diario y mensual

### Crear nuevos usuarios (solo administradores)

1. Ir a "Usuarios" en el menú
2. Hacer clic en "Crear Nuevo Usuario"
3. Ingresar nombre de usuario y contraseña
4. Marcar "Usuario Administrador" si se requieren permisos de administración

### Monitorear la salud del sistema

Acceder al endpoint de health check:
```bash
curl http://localhost:5000/health
```

Respuesta ejemplo:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T19:11:09Z",
  "database": {
    "status": "healthy",
    "batch_count": 42
  },
  "smb": {
    "status": "healthy",
    "batches_found": 15
  }
}
```

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