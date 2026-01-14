class DataValidator:
    """Clase para validar datos de operaciones contra datos del servidor SMB"""
    
    def __init__(self):
        self.tolerance = 0.1  # Tolerancia para comparación de profundidades (metros)
    
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
