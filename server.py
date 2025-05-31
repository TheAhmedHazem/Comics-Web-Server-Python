#!/usr/bin/env python3
"""
Python Comic Server - Main server application.

A local HTTP server for serving CBZ and CBR comic book files to mobile devices
over a local WiFi network. Features bandwidth monitoring, large file support,
and optimized streaming for comic reader applications.

Author: Comic Server Project
Date: May 31, 2025
Version: 1.0.0
Requirements: Python 3.7+

Usage:
    python server.py [--port PORT] [--dir DIRECTORY]
    
Example:
    python server.py --port 8080 --dir "C:\\My Comics"
"""

import sys
import signal
import argparse
import threading
from http.server import ThreadingHTTPServer
from datetime import datetime

# Import our custom modules
from config import config
from bandwidth_monitor import bandwidth_monitor
from comic_handler import ComicRequestHandler


class ComicServer:
    """
    Main comic server class that orchestrates all components.
    
    This class handles server initialization, startup, shutdown, and
    coordinates between the HTTP server, bandwidth monitor, and
    configuration management.
    """
    
    def __init__(self, port=None, comic_dir=None, host=None):
        """
        Initialize the comic server with optional configuration overrides.
        
        Args:
            port (int, optional): Server port override
            comic_dir (str, optional): Comic directory override
            host (str, optional): Host address override
        """
        # Update configuration with any provided overrides
        if port:
            config.port = port
        if comic_dir:
            config.comic_dir = comic_dir
        if host:
            config.host = host
            
        # Re-validate comic directory after potential changes
        config._validate_comic_directory()
        
        # Initialize server components
        self.httpd = None
        self.server_thread = None
        self.running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("Python Comic Server initialized")
    
    def start(self):
        """
        Start the HTTP server and bandwidth monitoring.
        
        This method implements the server startup requirements including
        network binding, thread initialization, and user feedback as
        specified in FR4.1, FR4.2, FR4.3, and FR6.1.
        """
        try:
            print("\n" + "="*60)
            print("Starting Python Comic Server...")
            print("="*60)
            
            # Print configuration information
            config.print_configuration()
            
            # Create HTTP server with threading support for concurrent requests
            server_address = config.get_server_address()
            self.httpd = ThreadingHTTPServer(server_address, ComicRequestHandler)
            
            # Configure server for better performance
            self.httpd.allow_reuse_address = True
            self.httpd.timeout = config.CONNECTION_TIMEOUT
            
            # Start bandwidth monitoring
            bandwidth_monitor.start_monitoring()
            
            # Start server in a separate thread to allow for clean shutdown
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=False,
                name="HTTPServer"
            )
            
            self.running = True
            self.server_thread.start()
            
            # Display connection information for users
            self._display_connection_info()
            
            # Display initial status
            self._display_server_status()
            
            print("\nServer is running! Press Ctrl+C to stop.")
            print("="*60)
            
            # Keep main thread alive and handle status updates
            self._monitor_server()
            
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"\nError: Port {config.port} is already in use.")
                print("Please try a different port or stop the conflicting service.")
                sys.exit(1)
            else:
                print(f"\nNetwork error: {e}")
                sys.exit(1)
        except Exception as e:
            print(f"\nFailed to start server: {e}")
            sys.exit(1)
    
    def stop(self):
        """
        Gracefully stop the server and clean up resources.
        
        This method implements graceful shutdown as required by FR6.4
        and displays final statistics as required by FR3.5.
        """
        if not self.running:
            return
            
        print("\n" + "="*60)
        print("Shutting down Python Comic Server...")
        print("="*60)
        
        self.running = False
        
        # Stop the HTTP server
        if self.httpd:
            print("Stopping HTTP server...")
            self.httpd.shutdown()
            self.httpd.server_close()
        
        # Wait for server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            print("Waiting for server thread to finish...")
            self.server_thread.join(timeout=5.0)
        
        # Stop bandwidth monitoring and display final statistics
        print("Stopping bandwidth monitoring...")
        bandwidth_monitor.stop_monitoring()
        
        print("\nServer shutdown complete.")
    
    def _run_server(self):
        """
        Run the HTTP server in a separate thread.
        
        This method handles the main server loop and catches any
        exceptions that might occur during server operation.
        """
        try:
            print(f"HTTP server thread started")
            self.httpd.serve_forever()
        except Exception as e:
            if self.running:  # Only log errors if we're supposed to be running
                print(f"Server error: {e}")
        finally:
            print("HTTP server thread stopped")
    
    def _monitor_server(self):
        """
        Monitor server status and provide periodic updates.
        
        This method runs in the main thread and provides real-time
        monitoring information as required by FR3.4 and FR6.1.
        """
        import time
        
        last_status_time = time.time()
        status_interval = 30.0  # Show status every 30 seconds
        
        try:
            while self.running:
                time.sleep(1.0)
                
                current_time = time.time()
                
                # Show periodic status updates
                if current_time - last_status_time >= status_interval:
                    self._display_server_status()
                    last_status_time = current_time
                    
        except KeyboardInterrupt:
            # This will be handled by the signal handler
            pass
    
    def _display_connection_info(self):
        """
        Display connection information for client setup.
        
        This method implements FR4.3 and FR6.3 requirements for displaying
        connection information that users need to configure their mobile apps.
        """
        print("\n" + "="*60)
        print("CONNECTION INFORMATION")
        print("="*60)
        print(f"Server URL: {config.get_connection_url()}")
        print(f"Local IP: {config.get_local_ip()}")
        print(f"Port: {config.port}")
        print("\nFor iPhone/iPad comic apps:")
        print(f"1. Connect your device to the same WiFi network")
        print(f"2. In your comic app's server settings, enter:")
        print(f"   Server: {config.get_local_ip()}")
        print(f"   Port: {config.port}")
        print(f"   or use full URL: {config.get_connection_url()}")
        print(f"3. Browse available comics in your app")
        print("="*60)
    
    def _display_server_status(self):
        """
        Display current server status and statistics.
        
        This method provides real-time status information as required
        by FR6.1 and FR6.2.
        """
        stats = bandwidth_monitor.get_current_statistics()
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Server Status:")
        print(f"  Uptime: {stats['uptime_formatted']}")
        print(f"  Data transferred: {bandwidth_monitor._format_bytes(stats['total_bytes_transferred'])}")
        print(f"  Files served: {stats['total_files_served']}")
        print(f"  Active transfers: {stats['active_transfers']}")
        print(f"  Current rate: {bandwidth_monitor._format_rate(stats['current_transfer_rate'])}")
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals for graceful termination.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        print(f"\nReceived signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Python Comic Server - Serve CBZ/CBR files to mobile devices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python server.py                          # Use default settings
  python server.py --port 8080              # Use custom port
  python server.py --dir "C:\\My Comics"     # Use custom directory
  python server.py --port 9000 --dir ./comics --host 192.168.1.100
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=None,
        help=f'Server port (default: {config.DEFAULT_PORT})'
    )
    
    parser.add_argument(
        '--dir', '-d',
        type=str,
        default=None,
        help=f'Comic files directory (default: {config.DEFAULT_COMIC_DIR})'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help=f'Host address to bind to (default: {config.DEFAULT_HOST})'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Python Comic Server 1.0.0'
    )
    
    return parser.parse_args()


def check_python_version():
    """
    Check if Python version meets requirements.
    
    This function implements TR1.1 requirement for Python 3.7+.
    """
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)


def main():
    """
    Main entry point for the application.
    
    This function handles command line argument parsing, server initialization,
    and startup according to the requirements.
    """
    # Check Python version compatibility
    check_python_version()
    
    # Display startup banner
    print("Python Comic Server v1.0.0")
    print("Serving CBZ/CBR files to mobile devices")
    print(f"Python {sys.version}")
    print("-" * 50)
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Create and start the server
        server = ComicServer(
            port=args.port,
            comic_dir=args.dir,
            host=args.host
        )
        
        server.start()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
