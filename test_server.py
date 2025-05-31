#!/usr/bin/env python3
"""
Test script for the Python Comic Server.

This script creates test files and validates server functionality
to ensure all requirements are met. Uses only Python standard library.

Author: Comic Server Project
Date: May 31, 2025
Version: 1.0.0
"""

import os
import sys
import time
import urllib.request
import urllib.error
import zipfile
from pathlib import Path


def create_test_files():
    """Create test comic files for server validation."""
    print("Creating test comic files...")
    
    # Create a larger test CBZ file
    test_cbz_path = "comics/test_large.cbz"
    with zipfile.ZipFile(test_cbz_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Create a dummy image file content
        dummy_image = b"FAKE_COMIC_IMAGE_DATA" * 1000  # ~22KB
        for i in range(10):
            zipf.writestr(f"page_{i:03d}.jpg", dummy_image)
    
    print(f"Created {test_cbz_path} ({os.path.getsize(test_cbz_path)} bytes)")
    
    # Create a test CBR file (just rename a zip for testing)
    test_cbr_path = "comics/test_comic.cbr"
    with open(test_cbr_path, 'wb') as f:
        f.write(b"CBR_TEST_CONTENT" * 100)  # ~1.6KB
    
    print(f"Created {test_cbr_path} ({os.path.getsize(test_cbr_path)} bytes)")
    
    # Create a non-comic file to test filtering
    non_comic_path = "comics/readme.txt"
    with open(non_comic_path, 'w') as f:
        f.write("This is a text file that should not appear in comic listings.")
    
    print(f"Created {non_comic_path} (should be filtered out)")


def test_server_endpoints():
    """Test server endpoints and functionality using urllib."""
    base_url = "http://localhost:8000"
    
    print(f"\nTesting server at {base_url}...")
    
    try:
        # Test directory listing
        print("Testing directory listing...")
        with urllib.request.urlopen(base_url, timeout=5) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                print("✓ Directory listing works")
                if "test_large.cbz" in content and "test_comic.cbr" in content:
                    print("✓ Comic files are listed")
                if "readme.txt" not in content:
                    print("✓ Non-comic files are filtered out")
            else:
                print(f"✗ Directory listing failed: {response.status}")
        
        # Test file download
        print("\nTesting file download...")
        file_url = f"{base_url}/test_large.cbz"
        with urllib.request.urlopen(file_url, timeout=10) as response:
            if response.status == 200:
                content = response.read()
                print(f"✓ File download works ({len(content)} bytes)")
                if 'Accept-Ranges' in response.headers:
                    print("✓ Accept-Ranges header present for mobile compatibility")
            else:
                print(f"✗ File download failed: {response.status}")
        
        # Test range request
        print("\nTesting range request...")
        req = urllib.request.Request(file_url)
        req.add_header('Range', 'bytes=0-1023')
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 206:
                    content = response.read()
                    print(f"✓ Range request works (206 status, {len(content)} bytes)")
                else:
                    print(f"✗ Range request failed: {response.status}")
        except urllib.error.HTTPError as e:
            if e.code == 206:
                print(f"✓ Range request works (206 status)")
            else:
                print(f"✗ Range request failed: {e.code}")
        
        # Test 404 for non-existent file
        print("\nTesting 404 handling...")
        try:
            with urllib.request.urlopen(f"{base_url}/nonexistent.cbz", timeout=5) as response:
                print(f"✗ 404 handling failed: {response.status} (should be 404)")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("✓ 404 handling works")
            else:
                print(f"✗ 404 handling failed: {e.code}")
            
        # Test path traversal protection
        print("\nTesting security...")
        try:
            with urllib.request.urlopen(f"{base_url}/../server.py", timeout=5) as response:
                print(f"✗ Path traversal protection failed: {response.status}")
        except urllib.error.HTTPError as e:
            if e.code in [400, 403, 404]:
                print("✓ Path traversal protection works")
            else:
                print(f"✗ Path traversal protection failed: {e.code}")
    
    except urllib.error.URLError:
        print("✗ Server is not running. Please start the server first.")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False
    
    return True


def main():
    """Main test function."""
    print("Python Comic Server - Test Suite")
    print("=" * 50)
    
    # Create test files
    create_test_files()
    
    # Test server functionality
    if len(sys.argv) > 1 and sys.argv[1] == "--test-server":
        test_server_endpoints()
    else:
        print("\nTest files created. To test server endpoints, run:")
        print("python test_server.py --test-server")
        print("\n(Make sure the server is running first)")


if __name__ == "__main__":
    main()
