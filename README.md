# Visor de Imágenes SMB

Sistema web para visualización de imágenes JPG almacenadas en carpetas SMB (Server Message Block).

## 🆕 Características Principales

### 🔐 Sistema de Autenticación
- Login/Logout seguro con contraseñas hasheadas
- Sesiones persistentes con tiempo de expiración (24 horas)
- Rate limiting (máximo 5 intentos fallidos, bloqueo de 5 minutos)
- Creación de usuarios por administradores
- Usuario por defecto: `admin` / `admin` (debe cambiarse en producción)

### 🖼️ Visor de Imágenes
- Exploración automática de carpetas SMB en busca de archivos JPG
- Visualización de lista completa de imágenes encontradas
- Búsqueda y filtrado por nombre de archivo, máquina o core
- Vista previa de imágenes sin salir de la página
- Panel de dos columnas:
  - Izquierda: Lista navegable de imágenes
  - Derecha: Visualización de imagen seleccionada
- Scroll independiente en ambos paneles
- Botón de actualización para refrescar la lista de imágenes

### 🔗 Integración SMB
- Conexión automática a servidor SMB
- Exploración recursiva de carpetas (Machine/Core/Images)
- Indicador visual del estado de conexión
- Cache de 30 segundos para optimizar rendimiento

### 🏥 Health Check
- Endpoint `/health` que proporciona:
  - Estado general del sistema
  - Estado de la base de datos
  - Estado de conexión SMB
  - Timestamp de verificación
  - Formato JSON para integración con herramientas de monitoreo

## Descripción

Visor de Imágenes SMB es una aplicación web desarrollada en Python con Flask que permite:

- **Autenticación segura**: Sistema de login con control de acceso
- **Exploración de imágenes**: Búsqueda automática de archivos JPG en servidor SMB
- **Visualización**: Ver imágenes directamente en el navegador
- **Búsqueda**: Filtrar imágenes por diferentes criterios
- **Gestión de usuarios**: Crear y administrar usuarios del sistema (solo administradores)

## Objetivo General

Proporcionar una plataforma centralizada y fácil de usar para visualizar imágenes JPG almacenadas en un servidor SMB, con navegación intuitiva y búsqueda eficiente.

## Requisitos

- Python 3.8 o superior
- Flask 3.0.0
- SQLAlchemy
- pysmb (para integración SMB)
- Acceso a servidor SMB

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
Crear archivo `.env` en la raíz del proyecto basado en `.env.example`:
```bash
cp .env.example .env
```

**IMPORTANTE:** Para uso en producción, cambie las credenciales por defecto. Nunca use las credenciales de ejemplo en un entorno de producción.

O crear manualmente con el siguiente contenido:
```env
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///images.db

# Configuración SMB (requerido)
SMB_SERVER_NAME=servidor-smb
SMB_SERVER_IP=172.16.11.107
SMB_SHARE_NAME=pond
SMB_USERNAME=orexplore
SMB_PASSWORD=en6Eith0aphi
SMB_DOMAIN=WORKGROUP

# Ruta base para escaneo (opcional, por defecto '/')
# Para escanear solo dentro de una carpeta específica:
# .jpg files should be two folders deep after pond/incoming/Orexplore/
SMB_BASE_SCAN_PATH=/incoming/Orexplore
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

### Visualizar imágenes

1. Después del login, serás redirigido automáticamente al visor de imágenes
2. La lista de imágenes JPG se carga automáticamente desde el servidor SMB
3. Usar la barra de búsqueda para filtrar imágenes
4. Hacer clic en cualquier imagen de la lista para visualizarla
5. Usar el scroll para navegar por más imágenes mientras se visualiza una

### Actualizar lista de imágenes

- Hacer clic en el botón "Actualizar Lista" para refrescar las imágenes del servidor SMB

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
  "timestamp": "2026-01-19T15:54:00Z",
  "database": {
    "status": "healthy",
    "user_count": 2
  },
  "smb": {
    "status": "healthy",
    "images_found": 42
  }
}
```

## Estructura del Proyecto

```
programa-1/
├── app.py                  # Aplicación principal Flask
├── config.py              # Configuración
├── models.py              # Modelo de base de datos (User)
├── smb_utils.py           # Utilidades para servidor SMB
├── cache_utils.py         # Sistema de caché thread-safe
├── requirements.txt       # Dependencias
├── .gitignore            # Archivos ignorados por git
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── login.html
│   ├── image_viewer.html
│   ├── create_user.html
│   └── users_list.html
└── static/              # Archivos estáticos
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## API REST

La aplicación incluye endpoints API:

- `GET /health` - Estado del sistema
- `GET /api/image/<path>` - Obtener imagen desde SMB
- `POST /api/refresh-images` - Refrescar lista de imágenes
- `POST /api/cache/invalidate` - Invalidar caché
- `GET /api/cache/stats` - Estadísticas de caché

## Configuración del Servidor SMB

Para habilitar la integración con servidor SMB:

1. Configurar las variables de entorno en `.env`
2. Asegurar conectividad de red con el servidor
3. Verificar permisos de lectura en el compartido
4. **(Opcional)** Configurar `SMB_BASE_SCAN_PATH` para escanear desde una carpeta específica dentro del share. Por defecto (`/`), escanea desde la raíz del share.
   
   Ejemplos de configuración:
   - `SMB_BASE_SCAN_PATH=/` - Escanea desde la raíz del share (por defecto)
   - `SMB_BASE_SCAN_PATH=/incoming/Orexplore` - Escanea solo dentro de la carpeta incoming/Orexplore
   - `SMB_BASE_SCAN_PATH=/data/production` - Escanea solo dentro de data/production

5. El sistema escanea recursivamente toda la estructura de carpetas en busca de archivos JPG. Soporta cualquier profundidad y organización de directorios:
   ```
   /share_name/
   ├── Orexplore/
   │   ├── Oux-Plore_Test/
   │   │   ├── Batch-1/
   │   │   │   ├── image1.jpg
   │   │   │   └── image2.jpg
   │   │   └── Batch-2/
   │   │       └── scan.jpg
   │   └── SampleA/
   │       └── batch-1/
   │           └── test.jpg
   └── MACHINE-02/
       └── CORE-003/
           └── image4.jpg
   ```
   
   El escáner recursivo encuentra automáticamente todos los archivos JPG sin importar la estructura de carpetas.

## Desarrollo

### Ejecutar en modo desarrollo

```bash
export FLASK_ENV=development
python app.py
```

### Estructura de base de datos

La base de datos se crea automáticamente al iniciar la aplicación. Para recrearla:

```bash
rm images.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Seguridad

- Las contraseñas se almacenan hasheadas usando Werkzeug
- Rate limiting en el login (5 intentos, bloqueo de 5 minutos)
- Sesiones con expiración de 24 horas
- Autenticación requerida para todas las páginas excepto login
- Control de acceso basado en roles (admin/usuario)

## Licencia

Este proyecto es de código abierto.

## Contacto

Para soporte y consultas, contactar al equipo de desarrollo.
