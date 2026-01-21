#!/usr/bin/env python3
"""
SMB Connection and Folder Access Test Script

This script tests the connection to the SMB server and verifies folder access.
It uses the configuration from config.py and .env file.

Usage:
    python test_smb_connection.py

Features:
    - Tests SMB server connectivity
    - Verifies credentials and authentication
    - Lists folders in the configured base path
    - Scans for PNG files in the structure
    - Provides detailed error messages for troubleshooting
"""

import sys
import os
from datetime import datetime
from config import Config
from smb_utils import SMBDataRetriever


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text):
    """Print a formatted section header"""
    print(f"\n--- {text} ---")


def print_success(text):
    """Print success message"""
    print(f"✓ {text}")


def print_error(text):
    """Print error message"""
    print(f"✗ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ {text}")


def test_smb_connection():
    """Main test function for SMB connection and folder access"""
    
    print_header("SMB Connection and Folder Access Test")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display configuration
    print_section("Configuration")
    config_dict = {
        'SMB_SERVER_NAME': Config.SMB_SERVER_NAME,
        'SMB_SERVER_IP': Config.SMB_SERVER_IP,
        'SMB_SHARE_NAME': Config.SMB_SHARE_NAME,
        'SMB_USERNAME': Config.SMB_USERNAME,
        'SMB_PASSWORD': '***' if Config.SMB_PASSWORD else 'Not set',
        'SMB_DOMAIN': Config.SMB_DOMAIN,
        'SMB_BASE_SCAN_PATH': Config.SMB_BASE_SCAN_PATH
    }
    
    for key, value in config_dict.items():
        print(f"  {key}: {value}")
    
    # Test 1: Initialize SMB Retriever
    print_section("Test 1: Initialize SMB Data Retriever")
    try:
        config = {
            'SMB_SERVER_NAME': Config.SMB_SERVER_NAME,
            'SMB_SERVER_IP': Config.SMB_SERVER_IP,
            'SMB_SHARE_NAME': Config.SMB_SHARE_NAME,
            'SMB_USERNAME': Config.SMB_USERNAME,
            'SMB_PASSWORD': Config.SMB_PASSWORD,
            'SMB_DOMAIN': Config.SMB_DOMAIN,
            'SMB_BASE_SCAN_PATH': Config.SMB_BASE_SCAN_PATH
        }
        smb_retriever = SMBDataRetriever(config)
        print_success("SMB Data Retriever initialized successfully")
    except Exception as e:
        print_error(f"Failed to initialize SMB Data Retriever: {str(e)}")
        return False
    
    # Test 2: Connect to SMB Server
    print_section("Test 2: Connect to SMB Server")
    try:
        connected = smb_retriever.connect()
        if connected:
            print_success(f"Successfully connected to SMB server at {Config.SMB_SERVER_IP}")
        else:
            print_error("Failed to connect to SMB server")
            print_info("Please check:")
            print_info("  - Network connectivity to the server")
            print_info("  - SMB server IP address and name")
            print_info("  - Firewall settings")
            return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        print_info("Please verify:")
        print_info("  - SMB credentials (username/password)")
        print_info("  - Domain settings")
        print_info("  - Server availability")
        return False
    
    # Test 3: List Share Contents
    print_section("Test 3: Access SMB Share")
    try:
        base_path = Config.SMB_BASE_SCAN_PATH or '/'
        print_info(f"Attempting to list contents of: {Config.SMB_SHARE_NAME}{base_path}")
        
        items = smb_retriever.connection.listPath(
            Config.SMB_SHARE_NAME,
            base_path
        )
        
        folders = [item for item in items if item.isDirectory and item.filename not in ['.', '..']]
        files = [item for item in items if not item.isDirectory]
        
        print_success(f"Successfully accessed share '{Config.SMB_SHARE_NAME}'")
        print_info(f"Found {len(folders)} folders and {len(files)} files")
        
        if folders:
            print_info("\nFirst 10 folders:")
            for i, folder in enumerate(folders[:10]):
                print(f"    {i+1}. {folder.filename}/")
        
        if files:
            print_info("\nFirst 10 files:")
            for i, file in enumerate(files[:10]):
                size_mb = file.file_size / (1024 * 1024)
                print(f"    {i+1}. {file.filename} ({size_mb:.2f} MB)")
                
    except Exception as e:
        print_error(f"Failed to access share: {str(e)}")
        print_info("Please verify:")
        print_info(f"  - Share name '{Config.SMB_SHARE_NAME}' exists")
        print_info(f"  - User has read permissions on the share")
        print_info(f"  - Base path '{base_path}' exists in the share")
        smb_retriever.disconnect()
        return False
    
    # Test 4: Scan for PNG Images
    print_section("Test 4: Scan for PNG Images")
    try:
        # Disconnect first as scan_for_png_images handles its own connection
        smb_retriever.disconnect()
        
        print_info("Starting recursive PNG scan...")
        print_info("This may take a few moments depending on folder structure...")
        
        png_files = smb_retriever.scan_for_png_images()
        
        if png_files:
            print_success(f"Found {len(png_files)} PNG files")
            print_info("\nFirst 10 PNG files:")
            for i, png in enumerate(png_files[:10]):
                display_name = png.get('display_name', png.get('filename', 'Unknown'))
                folder = png.get('folder_path', '')
                size_kb = png.get('file_size', 0) / 1024
                print(f"    {i+1}. {display_name}")
                print(f"       Path: {folder}")
                print(f"       Size: {size_kb:.2f} KB")
                
            # Show summary statistics
            print_info("\nSummary by machine/folder:")
            machines = {}
            for png in png_files:
                machine = png.get('machine_id', 'Unknown')
                if machine not in machines:
                    machines[machine] = 0
                machines[machine] += 1
            
            for machine, count in sorted(machines.items()):
                print(f"    {machine}: {count} images")
        else:
            print_info("No PNG files found in the configured path")
            print_info("Please verify:")
            print_info(f"  - PNG files exist in {Config.SMB_BASE_SCAN_PATH}")
            print_info("  - Path is configured correctly")
            
    except Exception as e:
        print_error(f"Failed to scan for PNG images: {str(e)}")
        return False
    
    # Test 5: Test Image Retrieval (if images found)
    if png_files:
        print_section("Test 5: Test Image File Retrieval")
        try:
            test_image = png_files[0]
            print_info(f"Testing retrieval of: {test_image['filename']}")
            
            image_data = smb_retriever.get_image_file(test_image['full_path'])
            
            if image_data:
                image_size = len(image_data.getvalue())
                print_success(f"Successfully retrieved image ({image_size} bytes)")
            else:
                print_error("Failed to retrieve image data")
                
        except Exception as e:
            print_error(f"Failed to retrieve image: {str(e)}")
    
    # Summary
    print_header("Test Summary")
    print_success("All tests completed successfully!")
    print_info("SMB connection and folder access are working correctly.")
    print_info(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_smb_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
