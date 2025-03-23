import ctypes
import time
import subprocess
from collections import deque
import gpiod
import os

# Import utility functions
import sys
sys.path.append('/home/jonno/ZazuWall-Simucube-Control/python')
from utils.ioni_enable import activate_ioni

# Set up library paths
_base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['LD_LIBRARY_PATH'] = os.pathsep.join([
    os.path.join(_base_path, 'lib'),
    os.path.join(_base_path, 'lib/SimpleMotionV2'),
    os.environ.get('LD_LIBRARY_PATH', '')
]).strip(os.pathsep)

# Load the shared library using absolute path
libsimucube = ctypes.CDLL(os.path.join(_base_path, "lib/libsimucube.so"))

# Define function signatures
libsimucube.openSimucube.restype = ctypes.c_int
libsimucube.openSimucube.argtypes = [ctypes.POINTER(ctypes.c_int)]

libsimucube.closeSimucube.restype = None
libsimucube.closeSimucube.argtypes = [ctypes.c_int]

libsimucube.clearFaultsAndInitialize.restype = ctypes.c_int
libsimucube.clearFaultsAndInitialize.argtypes = [ctypes.c_int]

libsimucube.setSpeed.restype = ctypes.c_int
libsimucube.setSpeed.argtypes = [ctypes.c_int, ctypes.c_int]

libsimucube.getTorque.restype = ctypes.c_int
libsimucube.getTorque.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]

# Motor Configuration
SPEED_SETPOINT = 2000  # Speed when motor is enabled
POLL_DELAY = 0.05      # Delay between checks (in seconds)
ROLLING_WINDOW_SIZE = 20  # Number of samples for rolling average

# GPIO Configuration for Le Potato
# Le Potato has 2 chips with GPIO, so you need to specify both chip and pin number
# Before running this code, determine the correct chip and line for your pin:
# 1. Install required packages:
#    sudo apt update
#    sudo apt install python3-libgpiod
#    sudo apt install libretech-gpio libretech-dtoverlay
# 
# 2. Use the lgpio command to find the correct chip and pin:
#    lgpio info <PIN_NUMBER>  # Replace with your physical pin number
#    For example: lgpio info 12
#
# 3. Update these values based on the output:
CHIP_NAME = "/dev/gpiochip1"  # Update based on lgpio info output
LINE_OFFSET = 82              # Update based on lgpio info output

# Monitor Torque and Sensor
def monitor_torque_and_sensor(handle, chip, line_offset):
    """Monitor torque and sensor to control motor."""
    motor_running = False
    torque_window = deque(maxlen=ROLLING_WINDOW_SIZE)  # Rolling window for torque

    # Set up GPIO for Le Potato
    print(f"Attempting to initialize GPIO on chip {CHIP_NAME}, line {LINE_OFFSET}")
    line = chip.get_line(line_offset)
    print("Got GPIO line")
    config = gpiod.LineRequest()
    config.consumer = "nc_sensor"
    config.request_type = gpiod.LineRequest.DIRECTION_INPUT
    print("Requesting GPIO line...")
    line.request(config)
    print("GPIO line configured successfully")
    time.sleep(0.5)  # Small delay after initialization
    
    try:
        while True:
            # Read sensor state
            sensor_state = line.get_value()
            if sensor_state == 0:  # NC sensor triggered (connection open)
                print("Sensor triggered: Stopping motor...")
                if motor_running:
                    motor_running = False
                if libsimucube.setSpeed(handle.value, 0) == 0:
                    print("Motor disabled due to sensor.")
                else:
                    print("Failed to disable motor.")
                time.sleep(POLL_DELAY)
                continue

            # Continuously send 0 speed setpoint if motor is not running
            if not motor_running:
                if libsimucube.setSpeed(handle.value, 0) != 0:
                    print("Failed to maintain motor disabled state.")

            # Read torque value
            torque_value = ctypes.c_int()
            if libsimucube.getTorque(handle, ctypes.byref(torque_value)) == 0:
                torque_window.append(torque_value.value)
                average_torque = sum(torque_window) / len(torque_window)
                print(f"Torque: {torque_value.value}, Rolling Average Torque: {average_torque:.2f}")

                # Enable motor when average torque is below threshold
                if average_torque < 0 and not motor_running:
                    print("Rolling average torque is below threshold. Turning motor ON...")
                    motor_running = True
                    if libsimucube.setSpeed(handle.value, SPEED_SETPOINT) == 0:
                        print(f"Motor enabled at speed {SPEED_SETPOINT}.")
                    else:
                        print("Failed to enable motor.")

                # Disable motor when average torque is above or equal to threshold
                elif average_torque >= 0 and motor_running:
                    print("Rolling average torque is above or equal to threshold. Turning motor OFF...")
                    motor_running = False
                    if libsimucube.setSpeed(handle.value, 0) == 0:
                        print("Motor disabled.")
                    else:
                        print("Failed to disable motor.")

            else:
                print("Failed to read torque.")

            time.sleep(POLL_DELAY)
    finally:
        line.release()

# Main Function
if __name__ == "__main__":
    activate_ioni()

    handle = ctypes.c_int()
    
    try:
        # Setup GPIO for Le Potato
        chip = gpiod.Chip(CHIP_NAME)
        
        # Open Simucube
        if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
            print("Simucube opened successfully.")

            # Clear faults and initialize
            print("Clearing faults and initializing Simucube...")
            if libsimucube.clearFaultsAndInitialize(handle.value) == 0:
                print("Faults cleared and motor initialized.")

                # Start monitoring torque and sensor
                print("Monitoring torque and sensor to control motor...")
                monitor_torque_and_sensor(handle, chip, LINE_OFFSET)
            else:
                print("Failed to clear faults and initialize motor.")
        else:
            print("Failed to open Simucube.")
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'handle' in locals() and handle.value:
            if libsimucube.setSpeed(handle.value, 0) == 0:
                print("Motor disabled on exit.")
            libsimucube.closeSimucube(handle.value)
        if 'chip' in locals():
            chip.close()
        print("Simucube closed.")
