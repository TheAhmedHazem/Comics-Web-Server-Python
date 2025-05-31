#!/usr/bin/env python3
"""
Comic request handler module for the Python Comic Server.

This module implements the custom HTTP request handler class that serves
comic book files with bandwidth monitoring, range request support, and
security features as specified in the requirements.

Author: Comic Server Project
Date: May 31, 2025
Version: 1.0.0
Requirements: Python 3.7+
"""

import os
import re
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from datetime import datetime
import mimetypes
import uuid
from typing import Optional, Tuple

from config import config
from bandwidth_monitor import bandwidth_monitor


class ComicRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for serving comic book files.
    
    This class extends BaseHTTPRequestHandler to provide specialized
    functionality for comic file serving including:
    - CBZ/CBR file serving with range request support
    - Bandwidth monitoring integration
    - Security protections against path traversal
    - Directory listing with comic-only filtering
    - Mobile app compatibility headers
    """
    
    # Disable default HTTP server logging to use our custom logging
    def log_message(self, format, *args):
        """Override default logging to use our custom format."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_ip = self.client_address[0]
        print(f"[{timestamp}] {client_ip} - {format % args}")
    
    def handle(self):
        """
        Override handle method to provide better connection error handling.
        
        This method catches common connection errors that occur when mobile
        devices or browsers close connections abruptly, which is normal behavior.
        """
        try:
            super().handle()
        except ConnectionResetError:
            # This is normal when mobile browsers/apps close connections
            self.log_message("Connection reset by client (normal mobile behavior)")
        except BrokenPipeError:
            # This occurs when client closes connection during transfer
            self.log_message("Connection closed by client during transfer")
        except ConnectionAbortedError:
            # Connection was aborted by the client
            self.log_message("Connection aborted by client")
        except Exception as e:
            # Log other unexpected connection errors
            self.log_message(f"Connection error: {e}")
    
    def do_GET(self):
        """
        Handle HTTP GET requests.
        
        This method routes GET requests to appropriate handlers based on
        the requested path. Supports both file serving and directory listing.
        """
        try:
            # Parse and validate the requested path
            parsed_path = urllib.parse.urlparse(self.path)
            requested_path = urllib.parse.unquote(parsed_path.path)
            
            # Log the request
            self.log_message(f"GET {requested_path}")
            
            # Validate request for security (NFR3.2)
            if not self._validate_request(requested_path):
                self._send_error_response(400, "Bad Request", "Invalid request")
                return
            
            # Handle root path - show directory listing
            if requested_path == "/" or requested_path == "":
                self._serve_directory_listing()
                return
            
            # Handle file requests
            if requested_path.startswith("/"):
                self._serve_file(requested_path[1:])  # Remove leading slash
                return
            
            # Invalid path format
            self._send_error_response(400, "Bad Request", "Invalid path format")
            
        except Exception as e:
            self.log_message(f"Error handling GET request: {e}")
            self._send_error_response(500, "Internal Server Error", str(e))
    
    def do_HEAD(self):
        """
        Handle HTTP HEAD requests.
        
        HEAD requests are used by clients to get file information without
        downloading the actual content. Important for mobile apps.
        """
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            requested_path = urllib.parse.unquote(parsed_path.path)
            
            self.log_message(f"HEAD {requested_path}")
            
            if not self._validate_request(requested_path):
                self._send_error_response(400, "Bad Request", "Invalid request")
                return
            
            if requested_path == "/" or requested_path == "":
                self._send_directory_head()
                return
            
            if requested_path.startswith("/"):
                self._send_file_head(requested_path[1:])
                return
                
            self._send_error_response(400, "Bad Request", "Invalid path format")
            
        except Exception as e:
            self.log_message(f"Error handling HEAD request: {e}")
            self._send_error_response(500, "Internal Server Error", str(e))
    
    def _validate_request(self, path: str) -> bool:
        """
        Validate incoming request for security threats.
        
        This method implements request validation as required by NFR3.2
        to protect against malicious requests.
        
        Args:
            path (str): The requested path to validate
            
        Returns:
            bool: True if request is safe, False otherwise
        """
        # Check for obvious path traversal attempts
        if ".." in path or "~" in path:
            self.log_message(f"Blocked path traversal attempt: {path}")
            return False
        
        # Check for null bytes or control characters
        if any(ord(c) < 32 for c in path if c not in [' ', '\t']):
            self.log_message(f"Blocked request with control characters: {path}")
            return False
        
        # Check for excessively long paths
        if len(path) > 1024:
            self.log_message(f"Blocked excessively long path: {len(path)} characters")
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.\.', r'\/\.', r'\\', r'\x00', r'%00', r'%2e%2e', r'%5c'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                self.log_message(f"Blocked suspicious pattern in path: {path}")
                return False
        
        return True
    
    def _serve_directory_listing(self):
        """
        Serve a directory listing of available comic files.
        
        This method implements FR1.3 (directory listing functionality)
        and FR5.5 (filter and display only CBZ/CBR files).
        """
        try:
            # Get list of comic files in the directory
            comic_files = []
            
            for item in os.listdir(config.comic_dir):
                item_path = os.path.join(config.comic_dir, item)
                
                if os.path.isfile(item_path) and config.is_supported_file(item):
                    file_size = os.path.getsize(item_path)
                    comic_files.append({
                        'name': item,
                        'size': file_size,
                        'size_formatted': self._format_file_size(file_size),
                        'url': f"/{urllib.parse.quote(item)}"
                    })
            
            # Sort files by name
            comic_files.sort(key=lambda x: x['name'].lower())
            
            # Generate HTML response
            html_content = self._generate_directory_html(comic_files)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            self.wfile.write(html_content.encode('utf-8'))
            
            self.log_message(f"Served directory listing ({len(comic_files)} files)")
            
        except Exception as e:
            self.log_message(f"Error serving directory listing: {e}")
            self._send_error_response(500, "Internal Server Error", 
                                    "Unable to list directory contents")
    
    def _serve_file(self, filename: str):
        """
        Serve a comic book file with support for range requests.
        
        This method implements FR1.1, FR1.2, FR2.2 and handles large files
        efficiently using streaming as required by NFR1.1 and NFR1.2.
        
        Args:
            filename (str): Name of the file to serve
        """
        try:
            # Validate and get the full file path
            file_path = config.validate_file_path(filename)
            
            if not file_path:
                self._send_error_response(404, "Not Found", 
                                        f"File not found: {filename}")
                return
            
            # Check if it's a supported comic file
            if not config.is_supported_file(filename):
                self._send_error_response(400, "Bad Request", 
                                        "Unsupported file type")
                return
            
            # Get file information
            file_size = os.path.getsize(file_path)
            
            # Check for range requests (partial content)
            range_header = self.headers.get('Range')
            if range_header:
                self._serve_file_range(file_path, file_size, range_header, filename)
            else:
                self._serve_file_complete(file_path, file_size, filename)
                
        except ValueError as e:
            # Path traversal or other validation error
            self.log_message(f"Security violation: {e}")
            self._send_error_response(403, "Forbidden", "Access denied")
        except FileNotFoundError:
            self._send_error_response(404, "Not Found", f"File not found: {filename}")
        except PermissionError:
            self._send_error_response(403, "Forbidden", "Permission denied")
        except Exception as e:
            self.log_message(f"Error serving file {filename}: {e}")
            self._send_error_response(500, "Internal Server Error", str(e))
    
    def _serve_file_complete(self, file_path: str, file_size: int, filename: str):
        """
        Serve a complete file without range requests.
        
        Args:
            file_path (str): Full path to the file
            file_size (int): Size of the file in bytes
            filename (str): Original filename for logging
        """
        # Generate unique transfer ID for bandwidth monitoring
        transfer_id = str(uuid.uuid4())
        
        # Register transfer with bandwidth monitor
        bandwidth_monitor.register_transfer(transfer_id, filename, file_size)
        
        try:
            # Send response headers
            self.send_response(200)
            self._send_file_headers(file_size, filename)
            self.end_headers()
            
            # Stream file content in chunks
            with open(file_path, 'rb') as file:
                bytes_sent = 0
                
                while bytes_sent < file_size:
                    # Read chunk
                    chunk = file.read(config.CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    # Send chunk
                    self.wfile.write(chunk)
                    chunk_size = len(chunk)
                    bytes_sent += chunk_size
                      # Update bandwidth monitor
                    bandwidth_monitor.update_transfer(transfer_id, chunk_size)
            
            # Mark transfer as completed
            bandwidth_monitor.complete_transfer(transfer_id, success=True)
            
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            # Client disconnected during transfer - this is normal for mobile devices
            bandwidth_monitor.complete_transfer(transfer_id, success=False)
            self.log_message(f"Transfer interrupted by client disconnect: {filename}")
        except Exception as e:
            # Mark transfer as failed for other errors
            bandwidth_monitor.complete_transfer(transfer_id, success=False)
            self.log_message(f"Transfer failed: {filename} - {e}")
            raise e
    
    def _serve_file_range(self, file_path: str, file_size: int, 
                         range_header: str, filename: str):
        """
        Serve a file with range request support (HTTP 206 Partial Content).
        
        This method implements FR2.2 for resumable downloads and mobile app
        compatibility as required by FR2.5.
        
        Args:
            file_path (str): Full path to the file
            file_size (int): Total size of the file in bytes
            range_header (str): Range header from the request
            filename (str): Original filename for logging
        """
        # Parse range header
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not range_match:
            self._send_error_response(400, "Bad Request", "Invalid range header")
            return
        
        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        
        # Validate range
        if start >= file_size or end >= file_size or start > end:
            self.send_response(416)  # Range Not Satisfiable
            self.send_header('Content-Range', f'bytes */{file_size}')
            self.end_headers()
            return
        
        # Calculate content length for this range
        content_length = end - start + 1
        
        # Generate unique transfer ID for bandwidth monitoring
        transfer_id = str(uuid.uuid4())
        bandwidth_monitor.register_transfer(transfer_id, f"{filename} (partial)", content_length)
        
        try:
            # Send partial content response headers
            self.send_response(206)  # Partial Content
            self._send_file_headers(content_length, filename)
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            self.end_headers()
            
            # Stream the requested range
            with open(file_path, 'rb') as file:
                file.seek(start)
                bytes_sent = 0
                
                while bytes_sent < content_length:
                    # Calculate chunk size (don't exceed requested range)
                    chunk_size = min(config.CHUNK_SIZE, content_length - bytes_sent)
                    
                    # Read and send chunk
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    
                    self.wfile.write(chunk)
                    actual_chunk_size = len(chunk)
                    bytes_sent += actual_chunk_size
                      # Update bandwidth monitor
                    bandwidth_monitor.update_transfer(transfer_id, actual_chunk_size)
            
            # Mark transfer as completed
            bandwidth_monitor.complete_transfer(transfer_id, success=True)
            
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            # Client disconnected during range transfer - normal for mobile devices
            bandwidth_monitor.complete_transfer(transfer_id, success=False)
            self.log_message(f"Range transfer interrupted by client disconnect: {filename}")
        except Exception as e:
            # Mark transfer as failed for other errors
            bandwidth_monitor.complete_transfer(transfer_id, success=False)
            self.log_message(f"Range transfer failed: {filename} - {e}")
            raise e
    
    def _send_file_headers(self, content_length: int, filename: str):
        """
        Send appropriate HTTP headers for file responses.
        
        This method implements FR2.4 (proper MIME types) and FR2.5
        (Accept-Ranges header for mobile compatibility).
        
        Args:
            content_length (int): Size of the content being sent
            filename (str): Name of the file for MIME type detection
        """
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            # Default MIME types for comic archives
            if filename.lower().endswith('.cbz'):
                mime_type = 'application/zip'
            elif filename.lower().endswith('.cbr'):
                mime_type = 'application/x-rar-compressed'
            else:
                mime_type = 'application/octet-stream'
        
        # Send headers required for mobile app compatibility
        self.send_header('Content-Type', mime_type)
        self.send_header('Content-Length', str(content_length))
        self.send_header('Accept-Ranges', 'bytes')  # Required by FR2.5
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Cache-Control', 'public, max-age=3600')  # 1 hour cache
        
        # CORS headers for web client compatibility
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Range')
    
    def _send_directory_head(self):
        """Send HEAD response for directory listing."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
    
    def _send_file_head(self, filename: str):
        """
        Send HEAD response for a file.
        
        Args:
            filename (str): Name of the file
        """
        try:
            file_path = config.validate_file_path(filename)
            
            if not file_path or not config.is_supported_file(filename):
                self._send_error_response(404, "Not Found", "File not found")
                return
            
            file_size = os.path.getsize(file_path)
            
            self.send_response(200)
            self._send_file_headers(file_size, filename)
            self.end_headers()
            
        except Exception as e:
            self._send_error_response(404, "Not Found", "File not found")
    
    def _send_error_response(self, code: int, message: str, description: str):
        """
        Send a formatted error response.
        
        Args:
            code (int): HTTP status code
            message (str): HTTP status message
            description (str): Detailed error description
        """
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{code} {message}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ color: #d32f2f; }}
                .code {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1 class="error">{code} {message}</h1>
            <p>{description}</p>
            <hr>
            <p><em>Python Comic Server</em></p>
        </body>
        </html>
        """
        
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(error_html.encode('utf-8'))))
        self.end_headers()
        
        self.wfile.write(error_html.encode('utf-8'))
    
    def _generate_directory_html(self, comic_files: list) -> str:
        """
        Generate HTML for directory listing.
        
        Args:
            comic_files (list): List of comic file information dictionaries
            
        Returns:
            str: Generated HTML content
        """
        files_list = ""
        for file_info in comic_files:
            files_list += f"""
                <tr>
                    <td><a href="{file_info['url']}">{file_info['name']}</a></td>
                    <td class="size">{file_info['size_formatted']}</td>
                    <td><a href="{file_info['url']}" class="download">Download</a></td>
                </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Comic Server - File Listing</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 20px;
                    background: #f5f5f5;
                }}
                .container {{ 
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ 
                    color: #333;
                    border-bottom: 2px solid #007acc;
                    padding-bottom: 10px;
                }}
                .info {{ 
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                table {{ 
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{ 
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{ 
                    background: #f8f9fa;
                    font-weight: 600;
                }}
                tr:hover {{ background: #f8f9fa; }}
                a {{ 
                    color: #007acc;
                    text-decoration: none;
                }}
                a:hover {{ text-decoration: underline; }}
                .size {{ 
                    text-align: right;
                    font-family: monospace;
                }}
                .download {{ 
                    background: #007acc;
                    color: white !important;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                .download:hover {{ 
                    background: #005999;
                    text-decoration: none;
                }}
                .stats {{ 
                    margin-top: 20px;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📚 Python Comic Server</h1>
                
                <div class="info">
                    <strong>Server URL:</strong> {config.get_connection_url()}<br>
                    <strong>Comic Directory:</strong> {config.comic_dir}<br>
                    <strong>Available Files:</strong> {len(comic_files)}
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>📖 Comic File</th>
                            <th>📏 Size</th>
                            <th>⬇️ Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {files_list}
                    </tbody>
                </table>
                
                <div class="stats">
                    Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes (int): File size in bytes
            
        Returns:
            str: Formatted file size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
