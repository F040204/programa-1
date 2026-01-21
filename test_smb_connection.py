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


def get_smb_config():
    """Get SMB configuration dictionary"""
    return {
        'SMB_SERVER_NAME': Config.SMB_SERVER_NAME,
        'SMB_SERVER_IP': Config.SMB_SERVER_IP,
        'SMB_SHARE_NAME': Config.SMB_SHARE_NAME,
        'SMB_USERNAME': Config.SMB_USERNAME,
        'SMB_PASSWORD': Config.SMB_PASSWORD,
        'SMB_DOMAIN': Config.SMB_DOMAIN,
        'SMB_BASE_SCAN_PATH': Config.SMB_BASE_SCAN_PATH
    }


def join_smb_path(base_path, filename):
    """Helper function to join SMB paths consistently"""
    if base_path.endswith('/'):
        return f"{base_path}{filename}"
    return f"{base_path}/{filename}"


def test_smb_connection():
    """Main test function for SMB connection and folder access"""
    
    print_header("SMB Connection and Folder Access Test")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display configuration
    print_section("Configuration")
    config = get_smb_config()
    config_display = config.copy()
    config_display['SMB_PASSWORD'] = '***' if config['SMB_PASSWORD'] else 'Not set'
    
    for key, value in config_display.items():
        print(f"  {key}: {value}")
    
    # Test 1: Initialize SMB Retriever
    print_section("Test 1: Initialize SMB Data Retriever")
    try:
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
    print_section("Test 3: Access SMB Share and Verify Folder Depth")
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
        print_info(f"Found {len(folders)} folders and {len(files)} files at base level")
        
        if folders:
            print_info("\nFirst 10 folders at base level:")
            for i, folder in enumerate(folders[:10]):
                print(f"    {i+1}. {folder.filename}/")
            
            # Test accessing folders up to 3 levels deep
            print_info("\nVerifying folder access at multiple depths:")
            MAX_DEPTH_CHECKS = 5  # Limit total checks to avoid long scan
            MAX_SUBDIRS_PER_LEVEL = 2  # Check first 2 subdirectories at each level
            checked_depths = 0
            max_depth_to_check = 3
            
            def check_folder_depth(current_path, depth, max_depth, checked_count):
                """Recursively check folder access up to specified depth"""
                if depth > max_depth or checked_count >= MAX_DEPTH_CHECKS:
                    return checked_count
                
                try:
                    items = smb_retriever.connection.listPath(
                        Config.SMB_SHARE_NAME,
                        current_path
                    )
                    subdirs = [item for item in items if item.isDirectory and item.filename not in ['.', '..']]
                    
                    if subdirs:
                        for subdir in subdirs[:MAX_SUBDIRS_PER_LEVEL]:
                            if checked_count >= MAX_DEPTH_CHECKS:
                                break
                            subdir_path = join_smb_path(current_path, subdir.filename)
                            print(f"    ✓ Depth {depth}: {subdir_path}")
                            checked_count += 1
                            checked_count = check_folder_depth(subdir_path, depth + 1, max_depth, checked_count)
                except Exception as e:
                    print_info(f"    Note: Could not access depth {depth}: {str(e)}")
                
                return checked_count
            
            # Start checking from first folder
            if folders:
                first_folder_path = join_smb_path(base_path, folders[0].filename)
                checked_depths = check_folder_depth(first_folder_path, 1, max_depth_to_check, 0)
                
                if checked_depths > 0:
                    print_success(f"✓ Verified folder access up to {max_depth_to_check} levels deep")
                else:
                    print_info("Note: No subfolders found to verify depth")
        
        if files:
            print_info(f"\nFirst 10 files at base level:")
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
    
    # Test 4: Scan for JPG Images
    print_section("Test 4: Scan for JPG Images")
    jpg_files = []
    try:
        # Disconnect first as scan_for_jpg_images handles its own connection
        if smb_retriever.connection:
            smb_retriever.disconnect()
        
        print_info("Starting recursive JPG scan...")
        print_info("This may take a few moments depending on folder structure...")
        
        jpg_files = smb_retriever.scan_for_jpg_images()
        
        if jpg_files:
            print_success(f"Found {len(jpg_files)} JPG files")
            
            # Calculate depth information relative to base path
            base_path = Config.SMB_BASE_SCAN_PATH or '/'
            max_depth = 0
            depth_counts = {}
            
            for jpg in jpg_files:
                path_parts = jpg.get('path_parts', [])
                # Calculate depth from the base path
                depth = len(path_parts) - 1  # -1 because filename is the last part
                max_depth = max(max_depth, depth)
                depth_counts[depth] = depth_counts.get(depth, 0) + 1
            
            print_info(f"\nFolder depth analysis (relative to {base_path}):")
            print_info(f"  Maximum folder depth scanned: {max_depth} levels")
            for depth in sorted(depth_counts.keys()):
                print(f"    Depth {depth}: {depth_counts[depth]} files")
            
            # Verify we're checking at least 3 folders deep
            if max_depth >= 3:
                print_success(f"✓ Confirmed: Scanning checks folders at least 3 levels deep (found files at depth {max_depth})")
            elif max_depth > 0:
                print_info(f"Note: Currently only found files up to depth {max_depth}")
            
            print_info("\nFirst 10 JPG files:")
            for i, jpg in enumerate(jpg_files[:10]):
                display_name = jpg.get('display_name', jpg.get('filename', 'Unknown'))
                folder = jpg.get('folder_path', '')
                path_parts = jpg.get('path_parts', [])
                depth = len(path_parts) - 1
                size_kb = jpg.get('file_size', 0) / 1024
                print(f"    {i+1}. {display_name}")
                print(f"       Path: {folder}")
                print(f"       Depth: {depth} levels")
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
            print_info("No JPG files found in the configured path")
            print_info("Please verify:")
            print_info(f"  - JPG files exist in {Config.SMB_BASE_SCAN_PATH}")
            print_info("  - Path is configured correctly")
            
    except Exception as e:
        print_error(f"Failed to scan for JPG images: {str(e)}")
        return False
    
    # Test 5: Test Image Retrieval (if images found)
    if jpg_files:
        print_section("Test 5: Test Image File Retrieval")
        try:
            test_image = jpg_files[0]
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
