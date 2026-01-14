# Data Verifier Documentation

## Overview

The Data Verifier is a comprehensive validation system that checks if data exists and validates batches against SMB server data.

## Features

### 1. Data Existence Verification

The `verify_data_exists()` method checks if data exists and is valid:

```python
from validation import DataValidator

validator = DataValidator()

# Check if data exists
result = validator.verify_data_exists(data, 'Data description')

# Result structure:
# {
#     'exists': bool,      # True if data is not None
#     'valid': bool,       # True if data exists and is not empty
#     'message': str,      # Descriptive message
#     'count': int         # Number of items (for lists/dicts)
# }
```

### 2. Batch Validation

The `validate_batch()` method validates a batch against SMB data:

```python
# Validate a batch
validation_result = validator.validate_batch(batch, smb_data)

# Result structure:
# {
#     'has_discrepancies': bool,
#     'discrepancies': list,      # List of discrepancy messages
#     'message': str,              # Summary message
#     'batch_id': int,
#     'batch_number': int
# }
```

### 3. API Endpoints

#### Verify a Specific Batch

```bash
GET /api/batch/<batch_id>/verify
```

Returns:
```json
{
    "batch_exists": true,
    "batch_verification": {...},
    "smb_data_exists": true,
    "smb_verification": {...},
    "validation_result": {...},
    "message": "Verificación completada"
}
```

#### Verify All Batches

```bash
GET /api/verify-all-batches
```

Returns:
```json
{
    "success": true,
    "message": "Verificación completada",
    "batch_verification": {...},
    "smb_verification": {...},
    "total_batches": 10,
    "batches_with_smb_data": 8,
    "batches_with_discrepancies": 2,
    "results": [...]
}
```

## Usage in Status Checker

The Status Checker page now includes:

1. **Verification Status Display**: Shows if SMB data exists and is valid
2. **"Verificar Todos" Button**: Verifies all batches at once and shows summary
3. **Enhanced Discrepancy Details**: Shows specific validation messages for each discrepancy

## Validation Rules

The validator checks for:

1. **Data Existence**: Verifies data is not None and not empty
2. **Depth Range Matching**: Compares depth values with 0.1m tolerance
3. **Machine and Hole ID Matching**: Ensures batch matches SMB data
4. **Detailed Error Messages**: Provides specific information about discrepancies

## Examples

### Example 1: Check if SMB data exists

```python
validator = DataValidator()
smb_data = get_smb_data()
verification = validator.verify_data_exists(smb_data, 'Datos SMB')

if verification['valid']:
    print(f"SMB data is valid: {verification['message']}")
else:
    print(f"SMB data issue: {verification['message']}")
```

### Example 2: Validate a batch

```python
validator = DataValidator()
batch = Batch.query.get(1)
smb_data = get_smb_data_for_batch(batch)

result = validator.validate_batch(batch, smb_data)

if result['has_discrepancies']:
    print(f"Discrepancies found: {result['message']}")
    for discrepancy in result['discrepancies']:
        print(f"  - {discrepancy}")
else:
    print("Batch validated successfully!")
```

### Example 3: Use API to verify batch

```javascript
// Verify a specific batch
fetch('/api/batch/1/verify')
    .then(response => response.json())
    .then(data => {
        if (data.smb_data_exists && data.validation_result) {
            if (data.validation_result.has_discrepancies) {
                console.log('Discrepancies:', data.validation_result.discrepancies);
            } else {
                console.log('Batch validated successfully');
            }
        }
    });

// Verify all batches
fetch('/api/verify-all-batches')
    .then(response => response.json())
    .then(data => {
        console.log(`Total: ${data.total_batches}`);
        console.log(`With discrepancies: ${data.batches_with_discrepancies}`);
    });
```

## Integration with Status Checker

The Status Checker page automatically uses the DataValidator:

1. When loading, it verifies SMB data exists
2. For each batch, it uses `validate_batch()` to check for discrepancies
3. Displays detailed validation results in the discrepancies section
4. Provides "Verificar Todos" button for on-demand verification

## Benefits

1. **Robust Error Handling**: Checks for null/empty data before processing
2. **Detailed Feedback**: Provides specific messages about what's wrong
3. **API Access**: Can be used programmatically via REST API
4. **User-Friendly**: Clear UI with verification status and buttons
5. **Comprehensive**: Validates both existence and correctness of data
