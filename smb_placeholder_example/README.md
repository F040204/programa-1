# SMB Server File Structure Placeholder

This directory contains placeholder files that demonstrate the expected structure of files on the SMB server for later setup.

## SMB Server Configuration

- **Server**: 172.16.11.107
- **Share**: pond
- **Base Path**: incoming/Orexplore

## Expected File Structure

```
incoming/Orexplore/
├── {hole_id}/
│   └── batch-{to}/
│       └── depth.txt
```

### Example Structure

```
incoming/Orexplore/
├── DDH-001/
│   ├── batch-100.5/
│   │   └── depth.txt
│   ├── batch-200.8/
│   │   └── depth.txt
│   └── batch-300.2/
│       └── depth.txt
├── DDH-002/
│   ├── batch-150.0/
│   │   └── depth.txt
│   └── batch-250.5/
│       └── depth.txt
└── DDH-003/
    └── batch-180.3/
        └── depth.txt
```

## File Format

### depth.txt

The `depth.txt` file contains depth information for the scanned core samples.

**Format**: Plain text file with depth readings, one per line or in a structured format.

**Example content**:
```
from_depth: 0.0
to_depth: 100.5
scan_date: 2026-01-14T10:30:00Z
quality: good
machine: OREX-01
```

## Directory Naming Convention

- **{hole_id}**: Identifier for the drill hole (e.g., DDH-001, DDH-002)
- **batch-{to}**: Batch directory named with the "to" depth value (e.g., batch-100.5, batch-200.8)

## Notes

- The structure follows the pattern: `{hole_id}/batch-{to}/depth.txt`
- Each batch directory contains a single `depth.txt` file
- The `to` value in the directory name represents the final depth of the batch
- Multiple batches can exist for the same hole_id
