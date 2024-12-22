import ctypes
import time
import subprocess
from collections import deque
import gpiod

# Activate IONI
def activate_ioni():
    try:
        # Call the binary
        result = subprocess.run(
            ["/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/enable_ioni_configurator"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Output from IONI activation:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error activating IONI:")
        print(e.stderr)

# Load the shared library
libsimucube = ctypes.CDLL("/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/Ioni_Functions/libsimucube.so")

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

# GPIO Configuration
CHIP_NAME = "gpiochip0"  # GPIO chip for GPIOAO bank
LINE_OFFSET = 6           # GPIOAO_6 (Pin 12)

# Monitor Torque and Sensor
def monitor_torque_and_sensor(handle, line):
    """Monitor torque and sensor to control motor."""
    motor_running = False
    torque_window = deque(maxlen=ROLLING_WINDOW_SIZE)  # Rolling window for torque

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

# Main Function
if __name__ == "__main__":
    activate_ioni()

    handle = ctypes.c_int()
    
    # Setup GPIO
    chip = gpiod.Chip(CHIP_NAME)
    line = chip.get_line(LINE_OFFSET)
    line.request(consumer="nc_sensor", type=gpiod.LINE_REQ_DIR_IN)

    try:
        # Open Simucube
        if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
            print("Simucube opened successfully.")

            # Clear faults and initialize
            print("Clearing faults and initializing Simucube...")
            if libsimucube.clearFaultsAndInitialize(handle.value) == 0:
                print("Faults cleared and motor initialized.")

                # Start monitoring torque and sensor
                print("Monitoring torque and sensor to control motor...")
                monitor_torque_and_sensor(handle, line)
            else:
                print("Failed to clear faults and initialize motor.")
        else:
            print("Failed to open Simucube.")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if libsimucube.setSpeed(handle.value, 0) == 0:
            print("Motor disabled on exit.")
        libsimucube.closeSimucube(handle.value)
        chip.close()
        print("Simucube closed.")
