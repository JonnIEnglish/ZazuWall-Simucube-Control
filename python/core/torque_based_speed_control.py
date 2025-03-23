#!/usr/bin/env python3
"""
Torque-Based Speed Control

This module combines IONI driver initialization, continuous torque monitoring,
and motor speed control based on torque thresholds.

The system:
1. Initializes the IONI driver
2. Continuously monitors torque using a rolling average of 10 values
3. Sets motor speed to 0 when average torque > 100
4. Sets motor speed to 2000 when average torque <= 100
"""

import time
import ctypes
import os
import sys
import argparse
import glob
from collections import deque
import threading
import signal

# Fix Python path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import from other modules
from python.core.ioni_config import activate_ioni
from python.core.set_speed import SpeedController

# Constants
TORQUE_THRESHOLD = 100
SAMPLE_INTERVAL = 0.1  # seconds between torque readings
WINDOW_SIZE = 5       # size of rolling average window
DEBOUNCE_TIME = 0.2    # seconds before allowing another speed change


def find_available_tty_usb_ports():
    """Find available USB serial devices"""
    return glob.glob('/dev/ttyUSB*')


def check_port_permissions(port):
    """Check if the current user has permissions to access the port"""
    try:
        return os.access(port, os.R_OK | os.W_OK)
    except Exception:
        return False


def print_permission_help(port):
    """Print helpful information about fixing permissions"""
    print("\n===== USB PORT PERMISSION ISSUE =====")
    print(f"You don't have permission to access {port}.")
    print("\nTo fix this issue, you can:")
    print("1. Run the script with sudo (temporary solution):")
    print(f"   sudo python3 {os.path.abspath(__file__)}")
    print("\n2. Add your user to the 'dialout' group (permanent solution):")
    print("   sudo usermod -a -G dialout $USER")
    print("   (You'll need to log out and log back in for this to take effect)")
    print("\n3. Create a udev rule (permanent solution):")
    print("   sudo nano /etc/udev/rules.d/99-usb-serial.rules")
    print("   Add this line:")
    print('   SUBSYSTEM=="tty", ATTRS{idVendor}=="XXXX", ATTRS{idProduct}=="XXXX", MODE="0666"')
    print("   (Replace XXXX with your device's vendor and product IDs)")
    print("   Then run: sudo udevadm control --reload-rules && sudo udevadm trigger")
    print("=======================================\n")


class TorqueBasedSpeedController:
    def __init__(self, port=None):
        # Setup library paths
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.port = port
        
        # Setup libraries
        os.environ['LD_LIBRARY_PATH'] = os.pathsep.join([
            os.path.join(self.root_dir, 'lib'),
            os.path.join(self.root_dir, 'lib/SimpleMotionV2'),
            os.environ.get('LD_LIBRARY_PATH', '')
        ]).strip(os.pathsep)
        
        # Load libraries
        self.torque_lib = ctypes.CDLL(os.path.join(self.root_dir, 'lib', 'libtorque_reader.so'))
        self.simucube_lib = ctypes.CDLL(os.path.join(self.root_dir, "lib/libsimucube.so"))
        
        # Configure function signatures
        self._configure_function_signatures()
        
        # Initialize variables
        self.handle = ctypes.c_int()
        self.torque_values = deque(maxlen=WINDOW_SIZE)
        self.running = False
        self.last_speed_change = 0
        self.current_speed = 0
        self.speed_controller = None
        self.lock = threading.Lock()

    def _configure_function_signatures(self):
        """Configure C function signatures for ctypes"""
        # Torque reader functions
        self.torque_lib.getTorqueRaw.argtypes = [ctypes.c_long, ctypes.POINTER(ctypes.c_int)]
        self.torque_lib.getTorqueRaw.restype = ctypes.c_int
        
        # Simucube functions
        self.simucube_lib.openSimucube.restype = ctypes.c_int
        self.simucube_lib.openSimucube.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self.simucube_lib.closeSimucube.argtypes = [ctypes.c_int]

    def initialize(self):
        """Initialize IONI driver and open connections"""
        print("Initializing IONI driver...")
        activate_ioni()
        
        print("Opening Simucube connection...")
        result = self.simucube_lib.openSimucube(ctypes.byref(self.handle))
        if result != 0:
            raise RuntimeError("Failed to open Simucube connection")
        
        print("Initializing speed controller...")
        
        # If no port was specified, try to autodetect
        if not self.port:
            available_ports = find_available_tty_usb_ports()
            if not available_ports:
                raise RuntimeError("No USB serial ports found. Please check your connections.")
            
            print(f"Available ports: {', '.join(available_ports)}")
            self.port = available_ports[0]
            print(f"Using port: {self.port}")
        
        # Check port permissions before trying to open
        if not os.path.exists(self.port):
            raise RuntimeError(f"Port {self.port} does not exist. Please check your connections.")
            
        if not check_port_permissions(self.port):
            print_permission_help(self.port)
            raise RuntimeError(f"Permission denied for port {self.port}")
        
        try:
            self.speed_controller = SpeedController(port=self.port)
            
            # Set initial speed to 0 for safety
            self.speed_controller.set_speed(0)
            print("Initialization complete")
        except RuntimeError as e:
            if "Connection failed" in str(e):
                print(f"\nFailed to connect to port {self.port}")
                print_permission_help(self.port)
            raise

    def read_torque(self):
        """Read a single torque value"""
        torque_value = ctypes.c_int(0)
        result = self.torque_lib.getTorqueRaw(self.handle.value, ctypes.byref(torque_value))
        if result != 0:
            print(f"Error reading torque: {result}")
            return None
        return torque_value.value

    def get_average_torque(self):
        """Get average torque from the rolling window"""
        if not self.torque_values:
            return 0
        return sum(self.torque_values) / len(self.torque_values)

    def update_speed(self, avg_torque):
        """Update motor speed based on average torque"""
        current_time = time.time()
        
        # Apply debouncing
        if current_time - self.last_speed_change < DEBOUNCE_TIME:
            return
        
        with self.lock:
            target_speed = 0 if avg_torque > TORQUE_THRESHOLD else 2000
            
            # Only change speed if it's different from current speed
            if target_speed != self.current_speed:
                print(f"Changing speed from {self.current_speed} to {target_speed} RPM (avg torque: {avg_torque:.2f})")
                self.speed_controller.set_speed(target_speed)
                self.current_speed = target_speed
                self.last_speed_change = current_time

    def monitoring_loop(self):
        """Main monitoring loop"""
        print("\nStarting torque monitoring...")
        print(f"Speed will be set to 0 RPM when average torque exceeds {TORQUE_THRESHOLD}")
        print(f"Speed will be set to 2000 RPM when average torque is below {TORQUE_THRESHOLD}")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            # Read torque value
            torque = self.read_torque()
            if torque is not None:
                # Add to rolling window
                self.torque_values.append(torque)
                
                # Calculate average
                avg_torque = self.get_average_torque()
                
                # Update display
                print(f"Current torque: {torque}, Average torque: {avg_torque:.2f}, Current speed: {self.current_speed} RPM\r", end='', flush=True)
                
                # Update motor speed
                self.update_speed(avg_torque)
            
            # Sleep for sampling interval
            time.sleep(SAMPLE_INTERVAL)

    def start(self):
        """Start the torque-based speed control system"""
        try:
            self.initialize()
            self.running = True
            
            # Set up signal handling for clean shutdown
            def signal_handler(sig, frame):
                print("\nShutting down...")
                self.stop()
                
            signal.signal(signal.SIGINT, signal_handler)
            
            # Start monitoring in the main thread
            self.monitoring_loop()
            
        except Exception as e:
            print(f"Error: {e}")
            self.stop()

    def stop(self):
        """Stop the system and clean up resources"""
        self.running = False
        print("\nStopping torque-based speed control...")
        
        # Stop motor
        if self.speed_controller:
            try:
                print("Setting speed to 0 RPM")
                self.speed_controller.set_speed(0)
            except Exception as e:
                print(f"Error stopping motor: {e}")
        
        # Close connections
        if hasattr(self, 'handle') and self.handle.value != 0:
            print("Closing Simucube connection")
            self.simucube_lib.closeSimucube(self.handle.value)
        
        print("System stopped")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Torque-based speed control for Simucube')
    parser.add_argument('--port', '-p', help='USB serial port (default: auto-detect)')
    parser.add_argument('--threshold', '-t', type=int, default=TORQUE_THRESHOLD,
                        help=f'Torque threshold (default: {TORQUE_THRESHOLD})')
    return parser.parse_args()


if __name__ == "__main__":
    # Print runtime information
    print(f"Running from: {os.path.abspath(__file__)}")
    print(f"Current directory: {os.getcwd()}")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Update constants if specified
    if args.threshold != TORQUE_THRESHOLD:
        TORQUE_THRESHOLD = args.threshold
        print(f"Using custom torque threshold: {TORQUE_THRESHOLD}")
    
    controller = TorqueBasedSpeedController(port=args.port)
    controller.start()