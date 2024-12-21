import time
import ctypes
import subprocess
from collections import deque

# Simucube Configuration
IONI_SPEED_BASE = 1000  # Speed setpoint for 10 m/min
IONI_SPEED_STEP = 200   # Speed increment per 1 m/min
TORQUE_WINDOW_SIZE = 50  # Number of samples for rolling average
POLLING_INTERVAL = 0.01  # Polling interval in seconds

# Load the shared Simucube library
libsimucube = ctypes.CDLL("/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/Ioni_Functions/libsimucube.so")

# Define Simucube function signatures
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

def activate_ioni():
    """Activate IONI mode."""
    try:
        result = subprocess.run(
            ["./enable_ioni_configurator"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Output from IONI activation:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error activating IONI:")
        print(e.stderr)
        raise Exception("IONI activation failed.")

def enable_motor(handle):
    """Enable the motor."""
    if libsimucube.clearFaultsAndInitialize(handle.value) == 0:
        print("Motor enabled successfully.")
    else:
        print("Failed to enable the motor.")

def disable_motor(handle):
    """Disable the motor."""
    if libsimucube.setSpeed(handle.value, 0) == 0:
        print("Motor disabled (speed set to 0).")
    else:
        print("Failed to disable the motor.")

def monitor_torque(handle):
    """Monitor torque using a rolling average and control motor state."""
    torque_window = deque(maxlen=TORQUE_WINDOW_SIZE)
    motor_running = False

    while True:
        torque_value = ctypes.c_int()
        if libsimucube.getTorque(handle, ctypes.byref(torque_value)) == 0:
            torque_window.append(torque_value.value)
            rolling_avg_torque = sum(torque_window) / len(torque_window)

            print(f"Raw Torque: {torque_value.value}, Rolling Avg Torque: {rolling_avg_torque:.2f}")

            if rolling_avg_torque < 0 and not motor_running:
                print("Torque is negative. Turning motor ON...")
                motor_running = True
                setpoint = IONI_SPEED_BASE  # Set speed to 10 m/min
                libsimucube.setSpeed(handle.value, setpoint)
            elif rolling_avg_torque >= 0 and motor_running:
                print("Torque is zero or positive. Turning motor OFF...")
                motor_running = False
                disable_motor(handle)
        else:
            print("Failed to read torque.")
        
        time.sleep(POLLING_INTERVAL)

# Main Function
if __name__ == "__main__":
    handle = ctypes.c_int()
    try:
        # Activate IONI
        activate_ioni()

        # Open Simucube
        if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
            print("Simucube opened successfully.")

            # Clear faults and initialize
            print("Clearing faults and initializing Simucube...")
            disable_motor(handle)  # Disable first for clean initialization
            enable_motor(handle)   # Enable after clearing faults

            # Start torque monitoring
            print("Starting torque monitoring...")
            monitor_torque(handle)

        else:
            print("Failed to open Simucube.")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        disable_motor(handle)  # Ensure motor is disabled on exit
        libsimucube.closeSimucube(handle.value)
        print("Simucube closed.")
