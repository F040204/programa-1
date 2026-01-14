from smb.SMBConnection import SMBConnection
from datetime import datetime
import tempfile
import os


class SMBDataRetriever:
    """Clase para recuperar datos del servidor SMB"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
    
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
            
            # Conectar al servidor
            connected = self.connection.connect(
                self.config['SMB_SERVER_IP'],
                139  # Puerto SMB
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
    
    def get_operation_data(self, core_id, machine_id):
        """
        Obtener datos de una operación específica desde el servidor SMB
        
        Args:
            core_id: ID del núcleo de perforación
            machine_id: ID de la máquina Orexplore
            
        Returns:
            Lista de diccionarios con datos encontrados
        """
        data = []
        
        try:
            if not self.connect():
                return data
            
            # Construir ruta de búsqueda
            search_path = f"{machine_id}/{core_id}"
            
            # Listar archivos en el share
            try:
                files = self.connection.listPath(
                    self.config['SMB_SHARE_NAME'],
                    search_path
                )
                
                for file_info in files:
                    if file_info.filename not in ['.', '..'] and not file_info.isDirectory:
                        data.append({
                            'file_path': f"{search_path}/{file_info.filename}",
                            'file_size': file_info.file_size,
                            'depth_from': self._extract_depth_from_filename(file_info.filename, 'from'),
                            'depth_to': self._extract_depth_from_filename(file_info.filename, 'to'),
                            'quality': 'good',  # Valor por defecto
                            'metadata': {
                                'create_time': datetime.fromtimestamp(file_info.create_time).isoformat(),
                                'last_write_time': datetime.fromtimestamp(file_info.last_write_time).isoformat()
                            }
                        })
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
        
        Returns:
            Lista de operaciones detectadas
        """
        operations = []
        
        try:
            if not self.connect():
                return operations
            
            # Listar máquinas (directorios de nivel superior)
            machines = self.connection.listPath(
                self.config['SMB_SHARE_NAME'],
                '/'
            )
            
            for machine in machines:
                if machine.isDirectory and machine.filename not in ['.', '..']:
                    machine_id = machine.filename
                    
                    # Listar núcleos dentro de cada máquina
                    try:
                        cores = self.connection.listPath(
                            self.config['SMB_SHARE_NAME'],
                            f"/{machine_id}/"
                        )
                        
                        for core in cores:
                            if core.isDirectory and core.filename not in ['.', '..']:
                                core_id = core.filename
                                
                                operations.append({
                                    'core_id': core_id,
                                    'machine_id': machine_id,
                                    'scan_date': datetime.fromtimestamp(core.create_time),
                                    'depth_from': 0.0,
                                    'depth_to': 0.0
                                })
                    except Exception as e:
                        print(f"Error listando cores para máquina {machine_id}: {str(e)}")
        
        except Exception as e:
            print(f"Error escaneando servidor SMB: {str(e)}")
        finally:
            self.disconnect()
        
        return operations
    
    def _extract_depth_from_filename(self, filename, field):
        """
        Extraer información de profundidad del nombre del archivo
        Asume formato: core_from_X_to_Y.ext o similar
        
        Args:
            filename: Nombre del archivo
            field: 'from' o 'to'
            
        Returns:
            Valor de profundidad o 0.0 si no se puede extraer
        """
        try:
            parts = filename.lower().split('_')
            if field == 'from' and 'from' in parts:
                idx = parts.index('from')
                if idx + 1 < len(parts):
                    return float(parts[idx + 1])
            elif field == 'to' and 'to' in parts:
                idx = parts.index('to')
                if idx + 1 < len(parts):
                    return float(parts[idx + 1].split('.')[0])
        except:
            pass
        
        return 0.0
