# SMB Connection Test Script

## Overview

The `test_smb_connection.py` script is a diagnostic tool designed to test SMB (Server Message Block) server connectivity and folder access for the Visor de Imágenes SMB application.

## Purpose

This script helps verify that:
- The SMB server is accessible from your network
- Credentials are valid
- The configured share and paths exist
- JPG files can be scanned and retrieved

## Prerequisites

1. Python 3.8 or higher
2. Required dependencies (install with `pip install -r requirements.txt`)
3. Configured `.env` file with SMB connection details

## Usage

### Basic Usage

Run the test script from the project root directory:

```bash
python test_smb_connection.py
```

or make it executable and run directly:

```bash
chmod +x test_smb_connection.py
./test_smb_connection.py
```

### What It Tests

The script performs 5 comprehensive tests:

1. **Initialize SMB Data Retriever**: Validates that the SMB utility can be instantiated with the configuration
2. **Connect to SMB Server**: Tests network connectivity and authentication to the SMB server
3. **Access SMB Share and Verify Folder Depth**: Verifies access to the configured share, lists folders/files, and explicitly checks folder access up to 3 levels deep from the base path
4. **Scan for JPG Images**: Performs a recursive scan for JPG files in the configured path, with depth analysis showing how many levels deep the scan reaches
5. **Test Image Retrieval**: Attempts to retrieve an actual image file to verify read permissions

### Output

The script provides detailed, color-coded output:
- ✓ Success messages for passed tests
- ✗ Error messages for failed tests
- ℹ Informational messages and troubleshooting tips

### Example Output

```
======================================================================
  SMB Connection and Folder Access Test
======================================================================
Test started at: 2026-01-21 14:45:00

--- Configuration ---
  SMB_SERVER_NAME: servidor-smb
  SMB_SERVER_IP: 172.16.11.107
  SMB_SHARE_NAME: pond
  SMB_USERNAME: orexplore
  SMB_PASSWORD: ***
  SMB_DOMAIN: WORKGROUP
  SMB_BASE_SCAN_PATH: /incoming/Orexplore

--- Test 1: Initialize SMB Data Retriever ---
✓ SMB Data Retriever initialized successfully

--- Test 2: Connect to SMB Server ---
✓ Successfully connected to SMB server at 172.16.11.107

--- Test 3: Access SMB Share and Verify Folder Depth ---
ℹ Attempting to list contents of: pond/incoming/Orexplore
✓ Successfully accessed share 'pond'
ℹ Found 5 folders and 12 files at base level

Verifying folder access at multiple depths:
    ✓ Depth 1: /incoming/Orexplore/Machine-01
    ✓ Depth 2: /incoming/Orexplore/Machine-01/batch-1.0
    ✓ Depth 3: /incoming/Orexplore/Machine-01/batch-1.0/sample-1
✓ Verified folder access up to 3 levels deep

--- Test 4: Scan for JPG Images ---
ℹ Starting recursive JPG scan...
✓ Found 42 JPG files

Folder depth analysis (relative to /incoming/Orexplore):
  Maximum folder depth scanned: 3 levels
    Depth 1: 5 files
    Depth 2: 15 files
    Depth 3: 22 files
✓ Confirmed: Scanning checks folders at least 3 levels deep (found files at depth 3)
...
```

## Configuration

The script uses configuration from two sources:

1. **config.py**: Python configuration class
2. **.env file**: Environment variables (recommended for production)

### Required Environment Variables

```env
SMB_SERVER_NAME=servidor-smb
SMB_SERVER_IP=172.16.11.107
SMB_SHARE_NAME=pond
SMB_USERNAME=orexplore
SMB_PASSWORD=your-password
SMB_DOMAIN=WORKGROUP
SMB_BASE_SCAN_PATH=/incoming/Orexplore
```

See `.env.example` for a template.

## Troubleshooting

### Connection Timeout

If you see a timeout error:
- Verify the SMB server IP address is correct
- Check network connectivity: `ping 172.16.11.107`
- Ensure firewall allows SMB traffic (ports 139/445)
- Confirm the SMB server is running

### Authentication Failed

If authentication fails:
- Verify username and password are correct
- Check the domain/workgroup name
- Ensure the user has permissions on the share

### Share Not Found

If the share cannot be accessed:
- Verify the share name is spelled correctly
- Confirm the share exists on the server
- Check user permissions for the share

### No JPG Files Found

If no JPG files are detected:
- Verify JPG files exist in the configured path
- Check the `SMB_BASE_SCAN_PATH` configuration
- Ensure files have `.jpg` extension (case-insensitive)

## Exit Codes

- `0`: All tests passed successfully
- `1`: One or more tests failed or an error occurred

## Integration

This test can be integrated into:
- CI/CD pipelines for deployment validation
- Health check scripts
- Automated monitoring systems
- Pre-deployment verification

Example in a shell script:
```bash
#!/bin/bash
if python test_smb_connection.py; then
    echo "SMB connection verified, proceeding with deployment"
else
    echo "SMB connection failed, aborting deployment"
    exit 1
fi
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Contact the development team

## Related Files

- `smb_utils.py`: SMB utility functions and classes
- `config.py`: Application configuration
- `.env.example`: Environment configuration template
- `README.md`: Main application documentation
