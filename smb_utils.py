from smb.SMBConnection import SMBConnection
from datetime import datetime
import tempfile
import os
import io
import re


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
    
    def scan_for_png_images(self):
        """
        Escanear el servidor SMB en busca de archivos PNG de forma recursiva
        Filtra solo imágenes dentro de carpetas batch-xxx.xx/sample-N
        
        Returns:
            Lista de diccionarios con información de archivos PNG encontrados
        """
        png_files = []
        
        try:
            if not self.connect():
                return png_files
            
            # Escanear recursivamente desde la raíz
            png_files = self._scan_directory_recursive('/', png_files)
            
            # Filtrar solo imágenes que están en batch-xxx.xx/sample-N
            filtered_files = self._filter_batch_sample_images(png_files)
        
        except Exception as e:
            print(f"Error escaneando servidor SMB para PNG: {str(e)}")
            filtered_files = []
        finally:
            self.disconnect()
        
        return filtered_files
    
    def _scan_directory_recursive(self, path, png_files):
        """
        Escanear un directorio de forma recursiva en busca de archivos PNG
        
        Args:
            path: Ruta del directorio a escanear
            png_files: Lista acumulativa de archivos PNG encontrados
            
        Returns:
            Lista actualizada de archivos PNG
        """
        try:
            # Listar contenido del directorio
            items = self.connection.listPath(
                self.config['SMB_SHARE_NAME'],
                path
            )
            
            for item in items:
                # Saltar referencias de directorio actual y padre
                if item.filename in ['.', '..']:
                    continue
                
                # Construir ruta completa
                if path.endswith('/'):
                    item_path = f"{path}{item.filename}"
                else:
                    item_path = f"{path}/{item.filename}"
                
                if item.isDirectory:
                    # Si es un directorio, escanear recursivamente
                    png_files = self._scan_directory_recursive(item_path, png_files)
                elif item.filename.lower().endswith('.png'):
                    # Si es un archivo PNG, agregarlo a la lista
                    # Extraer información de la ruta para organización
                    path_parts = item_path.strip('/').split('/')
                    
                    png_info = {
                        'filename': item.filename,
                        'full_path': item_path,
                        'file_size': item.file_size,
                        'create_time': datetime.fromtimestamp(item.create_time).isoformat(),
                        'last_write_time': datetime.fromtimestamp(item.last_write_time).isoformat(),
                        'folder_path': '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/',
                        'path_parts': path_parts
                    }
                    
                    # Agregar información de organización jerárquica
                    if len(path_parts) >= 2:
                        png_info['machine_id'] = path_parts[0]
                        png_info['core_id'] = path_parts[1]
                    else:
                        png_info['machine_id'] = path_parts[0] if path_parts else ''
                        png_info['core_id'] = ''
                    
                    png_files.append(png_info)
        
        except Exception as e:
            print(f"Error escaneando directorio {path}: {str(e)}")
        
        return png_files
    
    def _filter_batch_sample_images(self, png_files):
        """
        Filtrar y enriquecer imágenes PNG con información de batch y sample
        Ahora incluye PNGs de cualquier carpeta, no solo batch-xxx.xx/sample-N
        
        Args:
            png_files: Lista de diccionarios con información de PNG
            
        Returns:
            Lista filtrada y enriquecida con información de batch y sample
        """
        filtered = []
        
        # Patrón para detectar batch-xxx.xx (números con punto decimal opcional)
        batch_pattern = re.compile(r'batch-(\d+(?:\.\d+)?)', re.IGNORECASE)
        # Patrón para detectar sample-N (cualquier número, no solo 1-4)
        sample_pattern = re.compile(r'sample-(\d+)', re.IGNORECASE)
        
        for png in png_files:
            path_parts = png.get('path_parts', [])
            
            # Buscar batch-xxx.xx y sample-N en la ruta
            batch_value = None
            sample_value = None
            hole_name = None  # El folder padre antes de batch
            
            for i, part in enumerate(path_parts):
                batch_match = batch_pattern.search(part)
                if batch_match:
                    batch_value = batch_match.group(1)
                    # El folder anterior al batch es el "hole" o core
                    if i > 0:
                        hole_name = path_parts[i - 1]
                
                sample_match = sample_pattern.search(part)
                if sample_match:
                    sample_value = sample_match.group(1)
            
            # Incluir el PNG independientemente de si tiene batch o sample
            # Construir display_name según lo que tengamos disponible
            if batch_value and sample_value:
                # Caso ideal: tiene batch y sample
                png['batch'] = batch_value
                png['sample'] = sample_value
                png['hole_name'] = hole_name or png.get('core_id', 'Unknown')
                png['display_name'] = f"batch-{batch_value} sample {sample_value}"
            elif batch_value:
                # Solo tiene batch
                png['batch'] = batch_value
                png['sample'] = 'N/A'
                png['hole_name'] = hole_name or png.get('core_id', 'Unknown')
                png['display_name'] = f"batch-{batch_value}"
            elif sample_value:
                # Solo tiene sample
                png['batch'] = 'N/A'
                png['sample'] = sample_value
                png['hole_name'] = png.get('core_id', 'Unknown')
                png['display_name'] = f"sample {sample_value}"
            else:
                # No tiene ni batch ni sample, usar información de carpeta
                png['batch'] = 'N/A'
                png['sample'] = 'N/A'
                png['hole_name'] = png.get('core_id', 'Unknown')
                # Usar el nombre de la carpeta padre como display_name
                parent_folder = path_parts[-2] if len(path_parts) >= 2 else 'Root'
                filename = png.get('filename', 'Unknown')
                png['display_name'] = f"{parent_folder}/{filename}"
            
            filtered.append(png)
        
        # Ordenar por hole_name, batch, sample
        def sort_key(x):
            # Manejar batch que puede ser 'N/A'
            batch_val = x.get('batch', 'N/A')
            if batch_val == 'N/A':
                batch_num = float('inf')  # Los N/A van al final
            else:
                try:
                    batch_num = float(batch_val)
                except (ValueError, TypeError):
                    batch_num = float('inf')
            
            # Manejar sample que puede ser 'N/A'
            sample_val = x.get('sample', 'N/A')
            if sample_val == 'N/A':
                sample_num = float('inf')  # Los N/A van al final
            else:
                try:
                    sample_num = int(sample_val)
                except (ValueError, TypeError):
                    sample_num = float('inf')
            
            return (x.get('hole_name', ''), batch_num, sample_num)
        
        filtered.sort(key=sort_key)
        
        return filtered
    
    def get_image_file(self, file_path):
        """
        Obtener un archivo de imagen del servidor SMB
        
        Args:
            file_path: Ruta completa del archivo en el servidor SMB
            
        Returns:
            BytesIO object con el contenido del archivo o None si hay error
        """
        try:
            if not self.connect():
                return None
            
            # Crear buffer en memoria para el archivo
            file_obj = io.BytesIO()
            
            # Descargar archivo del servidor SMB
            self.connection.retrieveFile(
                self.config['SMB_SHARE_NAME'],
                file_path,
                file_obj
            )
            
            # Resetear el puntero al inicio del buffer
            file_obj.seek(0)
            
            return file_obj
        
        except Exception as e:
            print(f"Error obteniendo imagen {file_path}: {str(e)}")
            return None
        finally:
            self.disconnect()
