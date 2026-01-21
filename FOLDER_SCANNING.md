# SMB Folder Scanning - Technical Documentation

## Overview
This document explains how the application scans folders on the SMB server to ensure all JPG images are discovered.

## Scanning Mechanism

### 1. Base Configuration
The scan path is now configurable via the `SMB_BASE_SCAN_PATH` environment variable:

```bash
# Scan from root of SMB share (default)
SMB_BASE_SCAN_PATH=/

# Scan only within incoming/Orexplore folder
SMB_BASE_SCAN_PATH=/incoming/Orexplore
```

### 2. Recursive Scanning Algorithm
The `scan_for_jpg_images()` function in `smb_utils.py` performs a depth-first recursive scan:

1. **Starts** at the configured base path (default: `/`)
2. **Lists** all items in the current directory
3. **For each directory found**: Recursively scans that directory
4. **For each JPG file found**: Adds it to the results with full metadata
5. **Continues** until all directories have been explored

### 3. Path Normalization
Input paths are normalized to ensure consistency:
- Ensures path starts with `/`
- Removes trailing `/` (except for root path)
- Examples:
  - `incoming/Orexplore` → `/incoming/Orexplore`
  - `/data/` → `/data`
  - `/` → `/` (unchanged)

### 4. Logging
Comprehensive logging tracks the scanning process:
- **INFO level**: Start/end of scan, file counts
- **DEBUG level**: Each directory being scanned, file counts per directory
- **WARNING level**: Errors accessing specific directories (continues scanning)
- **ERROR level**: Critical errors (connection failures)

## Ensuring All Folders Are Checked

### Current Implementation Guarantees:
1. ✅ **Complete Recursion**: Every subdirectory is visited
2. ✅ **No Path Filtering**: No folders are excluded based on name
3. ✅ **Error Tolerance**: If one folder fails, scanning continues
4. ✅ **Depth Independence**: Supports any folder depth

### Verification
To verify all folders are being scanned:
1. Check application logs for DEBUG messages showing directory paths
2. Use the health check endpoint: `GET /health` 
3. Review the `images_found` count
4. Use the cache stats endpoint: `GET /api/cache/stats`

## Cache Behavior
- **TTL**: 30 seconds (configurable via `CACHE_TTL`)
- **Effect**: Automatic re-scan every 30 seconds when cache expires
- **Manual Refresh**: Available via "Actualizar Lista" button or `/api/refresh-images` endpoint

## Troubleshooting

### If images are not found:
1. **Check SMB connection**: Verify credentials and network access
2. **Verify base path**: Ensure `SMB_BASE_SCAN_PATH` points to the correct folder
3. **Check permissions**: User must have read access to all folders
4. **Review logs**: Look for warning/error messages about specific paths
5. **Validate file extensions**: Only `.jpg` files (case-insensitive) are detected

### Common Configuration Issues:
- ❌ **Wrong share name**: `SMB_SHARE_NAME` must match the actual SMB share
- ❌ **Incorrect base path**: Path must exist within the share
- ❌ **Permission denied**: SMB user needs read access to all subdirectories
- ❌ **Network issues**: Firewall blocking SMB ports (139, 445)

## Example Folder Structures

### Structure 1: Root scanning (default)
```
/share_name/
├── incoming/
│   └── Orexplore/
│       ├── Machine-01/
│       │   └── batch-1.0/
│       │       └── sample-1/
│       │           └── image.jpg  ← Found
│       └── Machine-02/
│           └── test.jpg           ← Found
└── archive/
    └── old_image.jpg              ← Found
```
Configuration: `SMB_BASE_SCAN_PATH=/`

### Structure 2: Targeted scanning
```
/share_name/
├── incoming/
│   └── Orexplore/
│       ├── Machine-01/
│       │   └── image.jpg         ← Found
│       └── Machine-02/
│           └── test.jpg          ← Found
└── archive/
    └── old_image.jpg             ← NOT scanned
```
Configuration: `SMB_BASE_SCAN_PATH=/incoming/Orexplore`

## Performance Considerations
- **Initial scan** may take time for large folder structures
- **Caching** prevents repeated scans within 30 seconds
- **Recursive depth** has no artificial limit
- **Network latency** affects scan speed

## Security Notes
- SMB credentials stored in environment variables
- Passwords should be strong and rotated regularly
- Read-only access recommended for SMB user
- Logs may contain file paths but not file contents
