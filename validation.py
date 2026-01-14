class DataValidator:
    """Clase para validar datos de operaciones contra datos del servidor SMB"""
    
    def __init__(self):
        self.tolerance = 0.1  # Tolerancia para comparación de profundidades (metros)
    
    def verify_data_exists(self, data, data_type="data"):
        """
        Verificar si los datos existen y son válidos
        
        Args:
            data: Datos a verificar (puede ser lista, dict, objeto, etc.)
            data_type: Tipo de datos para mensajes de error
            
        Returns:
            Diccionario con resultado de verificación:
            {
                'exists': bool,
                'valid': bool,
                'message': str,
                'count': int (si es lista)
            }
        """
        result = {
            'exists': False,
            'valid': False,
            'message': '',
            'count': 0
        }
        
        # Verificar si es None
        if data is None:
            result['message'] = f'{data_type} no existe (None)'
            return result
        
        # Verificar si es una lista
        if isinstance(data, list):
            result['exists'] = True
            result['count'] = len(data)
            if len(data) == 0:
                result['valid'] = False
                result['message'] = f'{data_type} existe pero está vacío'
            else:
                result['valid'] = True
                result['message'] = f'{data_type} existe y contiene {len(data)} elementos'
            return result
        
        # Verificar si es un diccionario
        if isinstance(data, dict):
            result['exists'] = True
            result['count'] = len(data)
            if len(data) == 0:
                result['valid'] = False
                result['message'] = f'{data_type} existe pero está vacío'
            else:
                result['valid'] = True
                result['message'] = f'{data_type} existe y contiene {len(data)} campos'
            return result
        
        # Para otros tipos de objetos
        result['exists'] = True
        result['valid'] = True
        result['message'] = f'{data_type} existe'
        
        return result
    
    def validate_batch(self, batch, smb_data):
        """
        Validar un batch contra datos del servidor SMB
        
        Args:
            batch: Objeto Batch de la base de datos
            smb_data: Datos recuperados del servidor SMB
            
        Returns:
            Diccionario con resultado de validación
        """
        result = {
            'has_discrepancies': False,
            'discrepancies': [],
            'message': '',
            'batch_id': batch.id if hasattr(batch, 'id') else None,
            'batch_number': batch.batch_number if hasattr(batch, 'batch_number') else None
        }
        
        # Verificar si hay datos SMB usando verify_data_exists
        smb_check = self.verify_data_exists(smb_data, 'Datos SMB')
        if not smb_check['valid']:
            result['has_discrepancies'] = True
            result['discrepancies'].append(smb_check['message'])
            result['message'] = 'No se encontraron datos correspondientes en el servidor SMB'
            return result
        
        # Si smb_data es un diccionario, convertirlo a lista
        if isinstance(smb_data, dict):
            smb_data = [smb_data]
        
        # Validar rangos de profundidad
        depth_matches = self._validate_depth_ranges_batch(batch, smb_data)
        if not depth_matches:
            result['has_discrepancies'] = True
            result['discrepancies'].append('Los rangos de profundidad no coinciden')
        
        # Construir mensaje
        if result['has_discrepancies']:
            result['message'] = 'Discrepancias encontradas: ' + '; '.join(result['discrepancies'])
        else:
            result['message'] = 'Validación exitosa: Los datos son consistentes'
        
        return result
    
    def _validate_depth_ranges_batch(self, batch, smb_data):
        """
        Validar que los rangos de profundidad coincidan para batches
        
        Args:
            batch: Objeto Batch
            smb_data: Lista de datos SMB
            
        Returns:
            True si los rangos coinciden dentro de la tolerancia
        """
        if not smb_data:
            return False
        
        # Para un batch, buscar el dato SMB correspondiente
        for smb in smb_data:
            smb_from = smb.get('depth_from', smb.get('from_depth', 0))
            smb_to = smb.get('depth_to', smb.get('to_depth', 0))
            
            # Si no se pudieron extraer profundidades, continuar
            if smb_from == 0 and smb_to == 0:
                continue
            
            # Comparar con tolerancia
            depth_from_match = abs(batch.from_depth - smb_from) <= self.tolerance
            depth_to_match = abs(batch.to_depth - smb_to) <= self.tolerance
            
            if depth_from_match and depth_to_match:
                return True
        
        return False
    
    def validate_operation(self, operation, smb_data):
        """
        Validar una operación contra datos del servidor SMB
        
        Args:
            operation: Objeto Operation de la base de datos
            smb_data: Lista de datos recuperados del servidor SMB
            
        Returns:
            Diccionario con resultado de validación
        """
        result = {
            'has_discrepancies': False,
            'discrepancies': [],
            'message': ''
        }
        
        # Verificar si hay datos SMB
        if not smb_data:
            result['has_discrepancies'] = True
            result['discrepancies'].append('No se encontraron datos en el servidor SMB')
            result['message'] = 'No se encontraron datos correspondientes en el servidor SMB'
            return result
        
        # Validar rangos de profundidad
        depth_matches = self._validate_depth_ranges(operation, smb_data)
        if not depth_matches:
            result['has_discrepancies'] = True
            result['discrepancies'].append('Los rangos de profundidad no coinciden')
        
        # Validar número de archivos esperados
        expected_files = self._calculate_expected_files(operation)
        actual_files = len(smb_data)
        
        if abs(expected_files - actual_files) > 1:  # Tolerancia de 1 archivo
            result['has_discrepancies'] = True
            result['discrepancies'].append(
                f'Número de archivos no coincide: esperados {expected_files}, encontrados {actual_files}'
            )
        
        # Construir mensaje
        if result['has_discrepancies']:
            result['message'] = 'Discrepancias encontradas: ' + '; '.join(result['discrepancies'])
        else:
            result['message'] = 'Validación exitosa: Los datos son consistentes'
        
        return result
    
    def _validate_depth_ranges(self, operation, smb_data):
        """
        Validar que los rangos de profundidad coincidan
        
        Args:
            operation: Objeto Operation
            smb_data: Lista de datos SMB
            
        Returns:
            True si los rangos coinciden dentro de la tolerancia
        """
        if not smb_data:
            return False
        
        # Calcular rango total de datos SMB
        smb_depth_from = min(d['depth_from'] for d in smb_data if d['depth_from'] > 0)
        smb_depth_to = max(d['depth_to'] for d in smb_data if d['depth_to'] > 0)
        
        # Si no se pudieron extraer profundidades, asumir válido
        if smb_depth_from == 0 and smb_depth_to == 0:
            return True
        
        # Comparar con tolerancia
        depth_from_match = abs(operation.depth_from - smb_depth_from) <= self.tolerance
        depth_to_match = abs(operation.depth_to - smb_depth_to) <= self.tolerance
        
        return depth_from_match and depth_to_match
    
    def _calculate_expected_files(self, operation):
        """
        Calcular número esperado de archivos basado en el rango de profundidad
        Asume aproximadamente 1 archivo por metro
        
        Args:
            operation: Objeto Operation
            
        Returns:
            Número esperado de archivos
        """
        depth_range = operation.depth_to - operation.depth_from
        return max(1, int(depth_range))
    
    def detect_anomalies(self, operations):
        """
        Detectar anomalías en un conjunto de operaciones
        
        Args:
            operations: Lista de objetos Operation
            
        Returns:
            Lista de anomalías detectadas
        """
        anomalies = []
        
        for operation in operations:
            # Verificar rangos de profundidad válidos
            if operation.depth_from >= operation.depth_to:
                anomalies.append({
                    'operation_id': operation.id,
                    'type': 'invalid_depth_range',
                    'message': f'Rango de profundidad inválido: {operation.depth_from} >= {operation.depth_to}'
                })
            
            # Verificar rangos extremos
            if operation.depth_to - operation.depth_from > 1000:
                anomalies.append({
                    'operation_id': operation.id,
                    'type': 'unusual_depth_range',
                    'message': f'Rango de profundidad inusualmente grande: {operation.depth_to - operation.depth_from}m'
                })
        
        return anomalies
