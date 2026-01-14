from smb.SMBConnection import SMBConnection
from datetime import datetime
import tempfile
import os


class SMBDataRetriever:
    """
    Clase para recuperar datos del servidor SMB
    
    Estructura esperada en SMB:
    - Server: 172.16.11.107
    - Share: pond
    - Path: incoming/Orexplore/{hole_id}/batch-{to}/depth.txt
    
    Ejemplo:
        incoming/Orexplore/DDH-001/batch-100.5/depth.txt
        incoming/Orexplore/DDH-001/batch-200.8/depth.txt
    
    Ver smb_placeholder_example/ para ejemplos de estructura de archivos
    """
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.base_path = config.get('SMB_BASE_PATH', 'incoming/Orexplore')
    
    def connect(self):
        """Establecer conexión con el servidor SMB"""
        try:
            self.connection = SMBConnection(
                username=self.config['SMB_USERNAME'],
                password=self.config['SMB_PASSWORD'],
                my_name='portal-operaciones',
                remote_name=self.config['SMB_SERVER_NAME'],
                domain=self.config['SMB_DOMAIN'],
                use_ntlm_v2=True
            )
            
            # Conectar al servidor con timeout
            connected = self.connection.connect(
                self.config['SMB_SERVER_IP'],
                139,  # Puerto SMB
                timeout=5  # 5 segundos de timeout
            )
            
            return connected
        except Exception as e:
            print(f"Error al conectar con servidor SMB: {str(e)}")
            return False
    
    def disconnect(self):
        """Cerrar conexión con el servidor SMB"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_batch_data(self, hole_id, batch_to):
        """
        Obtener datos de un batch específico desde el servidor SMB
        
        Estructura esperada: {hole_id}/batch-{to}/depth.txt
        
        Args:
            hole_id: ID del hoyo de perforación (ej: DDH-001)
            batch_to: Profundidad final del batch (ej: 100.5)
            
        Returns:
            Diccionario con datos del batch o None si no se encuentra
        """
        try:
            if not self.connect():
                return None
            
            # Construir ruta al archivo depth.txt
            file_path = f"{self.base_path}/{hole_id}/batch-{batch_to}/depth.txt"
            
            # Leer el archivo depth.txt
            depth_data = self._read_depth_file(file_path)
            
            return depth_data
            
        except Exception as e:
            print(f"Error al obtener datos del batch {hole_id}/batch-{batch_to}: {str(e)}")
            return None
        finally:
            self.disconnect()
    
    def _read_depth_file(self, file_path):
        """
        Leer y parsear archivo depth.txt desde SMB
        
        Formato esperado del archivo:
            from_depth: 0.0
            to_depth: 100.5
            scan_date: 2026-01-14T10:30:00Z
            quality: good
            machine: OREX-01
        
        Args:
            file_path: Ruta al archivo depth.txt en el servidor SMB
            
        Returns:
            Diccionario con los datos parseados
        """
        try:
            # Crear archivo temporal para descargar
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Descargar archivo desde SMB
            with open(temp_path, 'wb') as file_obj:
                self.connection.retrieveFile(
                    self.config['SMB_SHARE_NAME'],
                    file_path,
                    file_obj
                )
            
            # Leer y parsear contenido
            data = {}
            with open(temp_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        data[key.strip()] = value.strip()
            
            # Eliminar archivo temporal
            os.unlink(temp_path)
            
            # Convertir valores numéricos
            if 'from_depth' in data:
                data['from_depth'] = float(data['from_depth'])
            if 'to_depth' in data:
                data['to_depth'] = float(data['to_depth'])
            
            return data
            
        except Exception as e:
            print(f"Error leyendo archivo {file_path}: {str(e)}")
            return {}
    
    def get_operation_data(self, hole_id, batch_to=None):
        """
        Obtener datos de batches para un hole_id específico
        
        Nueva estructura: {hole_id}/batch-{to}/depth.txt
        
        Args:
            hole_id: ID del hoyo de perforación (hole ID)
            batch_to: Profundidad final específica (opcional)
            
        Returns:
            Lista de diccionarios con datos encontrados
        """
        data = []
        
        try:
            if not self.connect():
                return data
            
            # Si se especifica un batch_to específico
            if batch_to is not None:
                batch_data = self.get_batch_data(hole_id, batch_to)
                if batch_data:
                    data.append(batch_data)
                return data
            
            # Construir ruta de búsqueda para el hole_id
            search_path = f"{self.base_path}/{hole_id}"
            
            # Listar todos los directorios batch-* para este hole_id
            try:
                batches = self.connection.listPath(
                    self.config['SMB_SHARE_NAME'],
                    search_path
                )
                
                for batch_dir in batches:
                    if batch_dir.isDirectory and batch_dir.filename.startswith('batch-'):
                        # Extraer el valor 'to' del nombre del directorio
                        batch_name = batch_dir.filename
                        batch_to_value = batch_name.replace('batch-', '')
                        
                        # Leer el archivo depth.txt de este batch
                        file_path = f"{search_path}/{batch_name}/depth.txt"
                        depth_data = self._read_depth_file(file_path)
                        
                        if depth_data:
                            depth_data['batch_to'] = batch_to_value
                            depth_data['hole_id'] = hole_id
                            depth_data['file_path'] = file_path
                            data.append(depth_data)
                            
            except Exception as e:
                # Si no se encuentra el path, retornar lista vacía
                print(f"No se encontraron datos para {search_path}: {str(e)}")
        
        except Exception as e:
            print(f"Error al obtener datos de operación: {str(e)}")
        finally:
            self.disconnect()
        
        return data
    
    def scan_for_new_operations(self):
        """
        Escanear el servidor SMB en busca de nuevas operaciones
        
        Nueva estructura: incoming/Orexplore/{hole_id}/batch-{to}/depth.txt
        
        Returns:
            Lista de operaciones detectadas
        """
        operations = []
        
        try:
            if not self.connect():
                return operations
            
            # Listar hole_ids (directorios de nivel superior en base_path)
            try:
                holes = self.connection.listPath(
                    self.config['SMB_SHARE_NAME'],
                    self.base_path
                )
                
                for hole in holes:
                    if hole.isDirectory and hole.filename not in ['.', '..']:
                        hole_id = hole.filename
                        
                        # Listar batches dentro de cada hole_id
                        try:
                            batches = self.connection.listPath(
                                self.config['SMB_SHARE_NAME'],
                                f"{self.base_path}/{hole_id}"
                            )
                            
                            for batch_dir in batches:
                                if batch_dir.isDirectory and batch_dir.filename.startswith('batch-'):
                                    batch_name = batch_dir.filename
                                    batch_to_value = batch_name.replace('batch-', '')
                                    
                                    # Leer el archivo depth.txt de este batch
                                    file_path = f"{self.base_path}/{hole_id}/{batch_name}/depth.txt"
                                    depth_data = self._read_depth_file(file_path)
                                    
                                    if depth_data:
                                        operations.append({
                                            'hole_id': hole_id,
                                            'core_id': hole_id,  # Mantener compatibilidad
                                            'batch_to': batch_to_value,
                                            'depth_from': depth_data.get('from_depth', 0.0),
                                            'depth_to': depth_data.get('to_depth', 0.0),
                                            'machine_id': depth_data.get('machine', 'unknown'),
                                            'machine': depth_data.get('machine', 'unknown'),
                                            'quality': depth_data.get('quality', 'good'),
                                            'scan_date': depth_data.get('scan_date', datetime.now().isoformat()),
                                            'file_path': file_path
                                        })
                        except Exception as e:
                            print(f"Error listando batches para hole {hole_id}: {str(e)}")
            except Exception as e:
                print(f"Error listando holes en {self.base_path}: {str(e)}")
        
        except Exception as e:
            print(f"Error escaneando servidor SMB: {str(e)}")
        finally:
            self.disconnect()
        
        return operations

