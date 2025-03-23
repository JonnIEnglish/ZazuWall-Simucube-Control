#!/usr/bin/env python3
"""
Torque-Based Speed Control with Button Interface

This module combines:
1. IONI driver initialization
2. Continuous torque monitoring
3. Motor speed control based on torque thresholds
4. Button functionality to manually adjust speed setpoint

Button 2 increases speed by 200 RPM
Button 4 decreases speed by 200 RPM
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
WINDOW_SIZE = 5        # size of rolling average window
DEBOUNCE_TIME = 0.2    # seconds before allowing another speed change
SPEED_INCREMENT = 200  # RPM to increase/decrease with button press
DEFAULT_SPEED = 2000   # Default speed when torque is below threshold

# ADC Configuration for button reading
ADC_CHANNEL = 0
ADC_PATH = f"/sys/bus/iio/devices/iio:device0/in_voltage{ADC_CHANNEL}_raw"

# Button Calibration Thresholds - only using buttons 2 and 4
button_thresholds = {
    "button_2": 540,   # Increase speed
    "button_4": 1196,  # Decrease speed
    "no_press": 3507,  # No button pressed
}


# ADC Reader class for button detection
class ADCReader:
    def __init__(self, path):
        self.path = path
        self.file = None
        
    def open(self):
        try:
            self.file = open(self.path, "r")
            return True
        except Exception as e:
            print(f"Error opening ADC file: {e}")
            return False
            
    def read(self):
        if not self.file:
            if not self.open():
                return None
        
        try:
            self.file.seek(0)
            raw_value = int(self.file.read().strip())
            return raw_value
        except Exception as e:
            print(f"Error reading ADC: {e}")
            self.close()
            return None
            
    def close(self):
        if self.file:
            self.file.close()
            self.file = None


# Button detection function
def detect_button(adc_value, thresholds):
    button_tolerance = 100  # Tolerance for button detection
    
    for button, threshold in thresholds.items():
        if abs(adc_value - threshold) < button_tolerance:
            return button
    
    return "no_press"  # Default if no button matches within tolerance


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


class TorqueAndButtonSpeedController:
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
        self.target_speed = DEFAULT_SPEED  # This is the user-adjustable setpoint
        self.speed_controller = None
        self.lock = threading.Lock()
        
        # Button handling variables
        self.adc_reader = ADCReader(ADC_PATH)
        self.last_button = "no_press"
        self.last_button_time = 0
        self.button_debounce_time = 0.1  # 100ms debounce for buttons

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
            # If torque is above threshold, stop motor
            # Otherwise, use the user-adjustable target speed
            actual_speed = 0 if avg_torque > TORQUE_THRESHOLD else self.target_speed
            
            # Only change speed if it's different from current speed
            if actual_speed != self.current_speed:
                print(f"Changing speed from {self.current_speed} to {actual_speed} RPM (avg torque: {avg_torque:.2f})")
                self.speed_controller.set_speed(actual_speed)
                self.current_speed = actual_speed
                self.last_speed_change = current_time

    def check_buttons(self):
        """Check for button presses and update target speed"""
        adc_value = self.adc_reader.read()
        if adc_value is None:
            return
            
        current_button = detect_button(adc_value, button_thresholds)
        current_time = time.time()
        
        # Only process if button changed and debounce time passed
        if current_button != self.last_button and (current_time - self.last_button_time) > self.button_debounce_time:
            # Only process button press events (from no_press to a button)
            if self.last_button == "no_press" and current_button != "no_press":
                with self.lock:
                    if current_button == "button_2":  # Increase speed
                        self.target_speed += SPEED_INCREMENT
                        print(f"\nSpeed setpoint increased to: {self.target_speed} RPM")
                    elif current_button == "button_4":  # Decrease speed
                        self.target_speed = max(0, self.target_speed - SPEED_INCREMENT)
                        print(f"\nSpeed setpoint decreased to: {self.target_speed} RPM")
            
            # Update button state
            self.last_button = current_button
            self.last_button_time = current_time

    def monitoring_loop(self):
        """Main monitoring loop"""
        print("\nStarting torque and button monitoring...")
        print(f"Speed will be set to 0 RPM when average torque exceeds {TORQUE_THRESHOLD}")
        print(f"Default speed is {DEFAULT_SPEED} RPM when torque is below threshold")
        print("Use buttons to adjust the speed setpoint:")
        print(f"- Button 2: Increase speed by {SPEED_INCREMENT} RPM")
        print(f"- Button 4: Decrease speed by {SPEED_INCREMENT} RPM")
        print("Press Ctrl+C to stop\n")
        
        while self.running:
            # Check for button presses
            self.check_buttons()
            
            # Read torque value
            torque = self.read_torque()
            if torque is not None:
                # Add to rolling window
                self.torque_values.append(torque)
                
                # Calculate average
                avg_torque = self.get_average_torque()
                
                # Update display
                print(f"Current torque: {torque}, Avg torque: {avg_torque:.2f}, Speed: {self.current_speed} RPM, Setpoint: {self.target_speed} RPM\r", end='', flush=True)
                
                # Update motor speed
                self.update_speed(avg_torque)
            
            # Sleep for sampling interval
            time.sleep(SAMPLE_INTERVAL)

    def start(self):
        """Start the combined torque and button speed control system"""
        try:
            self.initialize()
            self.running = True
            self.target_speed = DEFAULT_SPEED  # Set initial target speed
            
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
        print("\nStopping speed control system...")
        
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
            
        # Close ADC reader
        if self.adc_reader:
            self.adc_reader.close()
        
        print("System stopped")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Torque and button-based speed control for Simucube')
    parser.add_argument('--port', '-p', help='USB serial port (default: auto-detect)')
    parser.add_argument('--threshold', '-t', type=int, default=TORQUE_THRESHOLD,
                        help=f'Torque threshold (default: {TORQUE_THRESHOLD})')
    parser.add_argument('--speed', '-s', type=int, default=DEFAULT_SPEED,
                        help=f'Default speed in RPM (default: {DEFAULT_SPEED})')
    parser.add_argument('--increment', '-i', type=int, default=SPEED_INCREMENT,
                        help=f'Speed increment per button press (default: {SPEED_INCREMENT})')
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
    
    if args.speed != DEFAULT_SPEED:
        DEFAULT_SPEED = args.speed
        print(f"Using custom default speed: {DEFAULT_SPEED} RPM")
        
    if args.increment != SPEED_INCREMENT:
        SPEED_INCREMENT = args.increment
        print(f"Using custom speed increment: {SPEED_INCREMENT} RPM")
    
    controller = TorqueAndButtonSpeedController(port=args.port)
    controller.start()