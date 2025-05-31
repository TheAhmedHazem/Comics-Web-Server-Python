#!/usr/bin/env python3
"""
Bandwidth monitoring module for the Python Comic Server.

This module provides real-time bandwidth monitoring and statistics collection
for file transfers, meeting requirements FR3.1 through FR3.5.

Author: Comic Server Project
Date: May 31, 2025
Version: 1.0.0
Requirements: Python 3.7+
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class BandwidthMonitor:
    """
    Thread-safe bandwidth monitoring class for tracking data transfer statistics.
    
    This class tracks bytes transferred, transfer rates, and provides real-time
    statistics as required by the functional requirements FR3.1-FR3.5.
    """
    
    def __init__(self, update_interval: float = 1.0):
        """
        Initialize the bandwidth monitor.
        
        Args:
            update_interval (float): Seconds between bandwidth calculations
        """
        self.update_interval = update_interval
        
        # Thread safety lock for all operations
        self._lock = threading.Lock()
        
        # Cumulative statistics
        self.total_bytes_transferred = 0
        self.total_files_served = 0
        self.server_start_time = time.time()
        
        # Current transfer tracking
        self.active_transfers = {}  # transfer_id -> transfer_info
        self.transfer_history = []  # List of completed transfers
        
        # Real-time bandwidth calculation
        self.current_transfer_rate = 0.0  # Bytes per second
        self.peak_transfer_rate = 0.0
        self.last_calculation_time = time.time()
        self.bytes_in_last_interval = 0
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def start_monitoring(self):
        """
        Start the background monitoring thread for real-time statistics.
        
        This method starts a daemon thread that continuously calculates
        transfer rates and updates statistics.
        """
        with self._lock:
            if not self.monitoring_active:
                self.monitoring_active = True
                self.monitoring_thread = threading.Thread(
                    target=self._monitoring_loop,
                    daemon=True,
                    name="BandwidthMonitor"
                )
                self.monitoring_thread.start()
                print("Bandwidth monitoring started")
    
    def stop_monitoring(self):
        """
        Stop the background monitoring thread and print final statistics.
        """
        with self._lock:
            if self.monitoring_active:
                self.monitoring_active = False
                
        # Wait for monitoring thread to finish
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
            
        # Print final statistics as required by FR3.5
        self.print_final_statistics()
    
    def register_transfer(self, transfer_id: str, filename: str, file_size: int) -> None:
        """
        Register a new file transfer for monitoring.
        
        Args:
            transfer_id (str): Unique identifier for this transfer
            filename (str): Name of the file being transferred
            file_size (int): Total size of the file in bytes
        """
        with self._lock:
            transfer_info = {
                'filename': filename,
                'file_size': file_size,
                'bytes_transferred': 0,
                'start_time': time.time(),
                'last_update': time.time(),
                'transfer_rate': 0.0
            }
            self.active_transfers[transfer_id] = transfer_info
            print(f"Started transfer: {filename} ({self._format_bytes(file_size)})")
    
    def update_transfer(self, transfer_id: str, bytes_chunk: int) -> None:
        """
        Update the progress of an active transfer.
        
        Args:
            transfer_id (str): Unique identifier for the transfer
            bytes_chunk (int): Number of bytes transferred in this chunk
        """
        with self._lock:
            if transfer_id in self.active_transfers:
                transfer = self.active_transfers[transfer_id]
                transfer['bytes_transferred'] += bytes_chunk
                transfer['last_update'] = time.time()
                
                # Calculate individual transfer rate
                duration = transfer['last_update'] - transfer['start_time']
                if duration > 0:
                    transfer['transfer_rate'] = transfer['bytes_transferred'] / duration
                
                # Update global statistics
                self.total_bytes_transferred += bytes_chunk
                self.bytes_in_last_interval += bytes_chunk
    
    def complete_transfer(self, transfer_id: str, success: bool = True) -> None:
        """
        Mark a transfer as completed and move it to history.
        
        Args:
            transfer_id (str): Unique identifier for the transfer
            success (bool): Whether the transfer completed successfully
        """
        with self._lock:
            if transfer_id in self.active_transfers:
                transfer = self.active_transfers.pop(transfer_id)
                transfer['end_time'] = time.time()
                transfer['success'] = success
                transfer['duration'] = transfer['end_time'] - transfer['start_time']
                
                # Calculate final transfer statistics
                if transfer['duration'] > 0:
                    transfer['average_rate'] = transfer['bytes_transferred'] / transfer['duration']
                else:
                    transfer['average_rate'] = 0.0
                
                self.transfer_history.append(transfer)
                
                if success:
                    self.total_files_served += 1
                    print(f"Completed transfer: {transfer['filename']} "
                          f"({self._format_bytes(transfer['bytes_transferred'])} "
                          f"in {transfer['duration']:.1f}s, "
                          f"avg: {self._format_rate(transfer['average_rate'])})")
                else:
                    print(f"Failed transfer: {transfer['filename']}")
    
    def get_current_statistics(self) -> Dict:
        """
        Get current bandwidth and transfer statistics.
        
        Returns:
            Dict: Dictionary containing current statistics
        """
        with self._lock:
            uptime = time.time() - self.server_start_time
            
            # Calculate overall average rate
            overall_rate = self.total_bytes_transferred / uptime if uptime > 0 else 0.0
            
            stats = {
                'total_bytes_transferred': self.total_bytes_transferred,
                'total_files_served': self.total_files_served,
                'active_transfers': len(self.active_transfers),
                'current_transfer_rate': self.current_transfer_rate,
                'peak_transfer_rate': self.peak_transfer_rate,
                'overall_average_rate': overall_rate,
                'uptime_seconds': uptime,
                'uptime_formatted': self._format_duration(uptime)
            }
            
            return stats
    
    def print_current_statistics(self) -> None:
        """
        Print current statistics to console for real-time monitoring.
        """
        stats = self.get_current_statistics()
        
        print(f"\n{'='*50}")
        print(f"Comic Server - Real-time Statistics")
        print(f"{'='*50}")
        print(f"Uptime: {stats['uptime_formatted']}")
        print(f"Total Data Transferred: {self._format_bytes(stats['total_bytes_transferred'])}")
        print(f"Files Served: {stats['total_files_served']}")
        print(f"Active Transfers: {stats['active_transfers']}")
        print(f"Current Rate: {self._format_rate(stats['current_transfer_rate'])}")
        print(f"Peak Rate: {self._format_rate(stats['peak_transfer_rate'])}")
        print(f"Average Rate: {self._format_rate(stats['overall_average_rate'])}")
        print(f"{'='*50}")
        
        # Show active transfer details
        with self._lock:
            if self.active_transfers:
                print("Active Transfers:")
                for transfer_id, transfer in self.active_transfers.items():
                    progress = (transfer['bytes_transferred'] / transfer['file_size']) * 100
                    print(f"  • {transfer['filename']}: {progress:.1f}% "
                          f"({self._format_rate(transfer['transfer_rate'])})")
                print(f"{'='*50}")
    
    def print_final_statistics(self) -> None:
        """
        Print comprehensive final statistics when server shuts down.
        
        This method satisfies requirement FR3.5 for displaying cumulative
        bandwidth usage on server shutdown.
        """
        stats = self.get_current_statistics()
        
        print(f"\n{'='*60}")
        print(f"Comic Server - Final Statistics Summary")
        print(f"{'='*60}")
        print(f"Server Runtime: {stats['uptime_formatted']}")
        print(f"Total Data Transferred: {self._format_bytes(stats['total_bytes_transferred'])}")
        print(f"Total Files Served: {stats['total_files_served']}")
        print(f"Peak Transfer Rate: {self._format_rate(stats['peak_transfer_rate'])}")
        print(f"Overall Average Rate: {self._format_rate(stats['overall_average_rate'])}")
        
        # Transfer history summary
        if self.transfer_history:
            successful_transfers = [t for t in self.transfer_history if t.get('success', False)]
            if successful_transfers:
                avg_file_size = sum(t['file_size'] for t in successful_transfers) / len(successful_transfers)
                avg_duration = sum(t['duration'] for t in successful_transfers) / len(successful_transfers)
                
                print(f"\nTransfer Summary:")
                print(f"  Successful Transfers: {len(successful_transfers)}")
                print(f"  Failed Transfers: {len(self.transfer_history) - len(successful_transfers)}")
                print(f"  Average File Size: {self._format_bytes(avg_file_size)}")
                print(f"  Average Transfer Time: {avg_duration:.1f} seconds")
        
        print(f"{'='*60}")
        print("Thank you for using Python Comic Server!")
        print(f"{'='*60}")
    
    def _monitoring_loop(self) -> None:
        """
        Background monitoring loop for calculating real-time transfer rates.
        
        This method runs in a separate thread and continuously updates
        transfer rate calculations.
        """
        while self.monitoring_active:
            try:
                time.sleep(self.update_interval)
                
                with self._lock:
                    current_time = time.time()
                    time_diff = current_time - self.last_calculation_time
                    
                    if time_diff > 0:
                        # Calculate current transfer rate
                        self.current_transfer_rate = self.bytes_in_last_interval / time_diff
                        
                        # Update peak rate if necessary
                        if self.current_transfer_rate > self.peak_transfer_rate:
                            self.peak_transfer_rate = self.current_transfer_rate
                        
                        # Reset for next interval
                        self.bytes_in_last_interval = 0
                        self.last_calculation_time = current_time
                        
            except Exception as e:
                print(f"Error in bandwidth monitoring: {e}")
                
    @staticmethod
    def _format_bytes(bytes_value: float) -> str:
        """
        Format bytes into human-readable format.
        
        Args:
            bytes_value (float): Number of bytes
            
        Returns:
            str: Formatted string with appropriate unit
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    @staticmethod
    def _format_rate(bytes_per_second: float) -> str:
        """
        Format transfer rate into human-readable format.
        
        Args:
            bytes_per_second (float): Transfer rate in bytes per second
            
        Returns:
            str: Formatted string with rate in MB/s and Mbps
        """
        if bytes_per_second == 0:
            return "0 B/s (0 Mbps)"
            
        # Convert to MB/s
        mb_per_second = bytes_per_second / (1024 * 1024)
        
        # Convert to Mbps (Megabits per second)
        mbps = (bytes_per_second * 8) / (1000 * 1000)
        
        return f"{mb_per_second:.2f} MB/s ({mbps:.1f} Mbps)"
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Format duration into human-readable format.
        
        Args:
            seconds (float): Duration in seconds
            
        Returns:
            str: Formatted duration string
        """
        duration = timedelta(seconds=int(seconds))
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


# Global bandwidth monitor instance
# This can be imported and used throughout the application
bandwidth_monitor = BandwidthMonitor()
