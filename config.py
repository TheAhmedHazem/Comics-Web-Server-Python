#!/usr/bin/env python3
"""
Configuration module for the Python Comic Server.

This module contains all configurable parameters for the comic server including
network settings, file handling parameters, and security configurations.

Author: Comic Server Project
Date: May 31, 2025
Version: 1.0.0
Requirements: Python 3.7+
"""

import os
import socket


class ServerConfig:
    """
    Central configuration class containing all server settings.
    
    This class provides default values for all configurable parameters
    and methods to validate and retrieve configuration values.
    """
    
    # Network Configuration
    DEFAULT_PORT = 8000
    DEFAULT_HOST = "0.0.0.0"  # Bind to all network interfaces
    MAX_CONCURRENT_CONNECTIONS = 10
    
    # File Handling Configuration
    CHUNK_SIZE = 8192  # 8KB chunks for streaming as per NFR1.2
    SUPPORTED_EXTENSIONS = [".cbz", ".cbr"]  # Comic book archive formats
    DEFAULT_COMIC_DIR = "comics"  # Default directory for comic files
    
    # Performance Configuration
    MAX_FILE_SIZE = 3 * 1024 * 1024 * 1024  # 3GB maximum file size
    CONNECTION_TIMEOUT = 30  # Seconds
    
    # Security Configuration
    ENABLE_DIRECTORY_TRAVERSAL_PROTECTION = True
    ENABLE_REQUEST_VALIDATION = True
    LOCAL_NETWORK_ONLY = True
    
    # Monitoring Configuration
    ENABLE_BANDWIDTH_MONITORING = True
    STATS_UPDATE_INTERVAL = 1.0  # Seconds between bandwidth updates
    
    def __init__(self, comic_dir=None, port=None, host=None):
        """
        Initialize server configuration with optional overrides.
        
        Args:
            comic_dir (str, optional): Path to comic files directory
            port (int, optional): Server port number
            host (str, optional): Host address to bind to
        """
        self.comic_dir = comic_dir or self.DEFAULT_COMIC_DIR
        self.port = port or self.DEFAULT_PORT
        self.host = host or self.DEFAULT_HOST
        
        # Validate and normalize the comic directory path
        self._validate_comic_directory()
        
    def _validate_comic_directory(self):
        """
        Validate and create the comic directory if it doesn't exist.
        
        Raises:
            OSError: If directory cannot be created or accessed
        """
        try:
            # Convert to absolute path for security
            self.comic_dir = os.path.abspath(self.comic_dir)
            
            # Create directory if it doesn't exist
            if not os.path.exists(self.comic_dir):
                os.makedirs(self.comic_dir)
                print(f"Created comic directory: {self.comic_dir}")
            
            # Verify directory is accessible
            if not os.path.isdir(self.comic_dir):
                raise OSError(f"Comic directory is not a valid directory: {self.comic_dir}")
                
            if not os.access(self.comic_dir, os.R_OK):
                raise OSError(f"Comic directory is not readable: {self.comic_dir}")
                
        except Exception as e:
            raise OSError(f"Failed to validate comic directory: {e}")
    
    def get_server_address(self):
        """
        Get the complete server address tuple.
        
        Returns:
            tuple: (host, port) tuple for server binding
        """
        return (self.host, self.port)
    
    def get_local_ip(self):
        """
        Attempt to determine the local IP address for client connection instructions.
        
        Returns:
            str: Local IP address or fallback message
        """
        try:
            # Create a socket connection to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to a remote address (doesn't actually send data)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception:
            # Fallback to localhost if unable to determine IP
            return "localhost"
    
    def get_connection_url(self):
        """
        Generate the full connection URL for clients.
        
        Returns:
            str: Complete HTTP URL for client connections
        """
        local_ip = self.get_local_ip()
        return f"http://{local_ip}:{self.port}"
    
    def is_supported_file(self, filename):
        """
        Check if a file has a supported comic book extension.
        
        Args:
            filename (str): Name of the file to check
            
        Returns:
            bool: True if file extension is supported, False otherwise
        """
        if not filename:
            return False
            
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in self.SUPPORTED_EXTENSIONS
    
    def validate_file_path(self, requested_path):
        """
        Validate that a requested file path is safe and within the comic directory.
        
        This method implements path traversal protection as required by NFR3.1.
        
        Args:
            requested_path (str): The file path requested by the client
            
        Returns:
            str: Validated absolute path or None if invalid
            
        Raises:
            ValueError: If path traversal attack is detected
        """
        if not requested_path:
            return None
            
        # Remove leading slashes and normalize path
        clean_path = requested_path.lstrip('/')
        
        # Join with comic directory and resolve to absolute path
        full_path = os.path.abspath(os.path.join(self.comic_dir, clean_path))
        
        # Ensure the resolved path is still within the comic directory
        if not full_path.startswith(self.comic_dir):
            raise ValueError(f"Path traversal attack detected: {requested_path}")
        
        # Check if file exists and is readable
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return full_path
            
        return None
    
    def print_configuration(self):
        """
        Print the current server configuration for debugging and user information.
        """
        print("=" * 60)
        print("Python Comic Server Configuration")
        print("=" * 60)
        print(f"Server Address: {self.host}:{self.port}")
        print(f"Connection URL: {self.get_connection_url()}")
        print(f"Comic Directory: {self.comic_dir}")
        print(f"Supported Extensions: {', '.join(self.SUPPORTED_EXTENSIONS)}")
        print(f"Chunk Size: {self.CHUNK_SIZE} bytes")
        print(f"Max File Size: {self.MAX_FILE_SIZE / (1024**3):.1f} GB")
        print(f"Max Connections: {self.MAX_CONCURRENT_CONNECTIONS}")
        print(f"Bandwidth Monitoring: {'Enabled' if self.ENABLE_BANDWIDTH_MONITORING else 'Disabled'}")
        print("=" * 60)


# Global configuration instance
# This can be imported and used throughout the application
config = ServerConfig()
