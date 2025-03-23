import ctypes
import time
import os
from pathlib import Path

# Get the absolute path to the library
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(script_dir))

# Add lib directories to path
os.environ['LD_LIBRARY_PATH'] = os.pathsep.join([
    os.path.join(root_dir, 'lib'),
    os.path.join(root_dir, 'lib/SimpleMotionV2'),
    os.environ.get('LD_LIBRARY_PATH', '')
]).strip(os.pathsep)

# Load the torque reader library
lib = ctypes.CDLL(os.path.join(root_dir, 'lib', 'libtorque_reader.so'))

# Define function signatures for the torque reader function
getTorqueRaw = lib.getTorqueRaw
getTorqueRaw.argtypes = [ctypes.c_long, ctypes.POINTER(ctypes.c_int)]
getTorqueRaw.restype = ctypes.c_int

# Load IONI activation functions
libsimucube = ctypes.CDLL(os.path.join(root_dir, "lib/libsimucube.so"))
libsimucube.openSimucube.restype = ctypes.c_int
libsimucube.openSimucube.argtypes = [ctypes.POINTER(ctypes.c_int)]
libsimucube.closeSimucube.argtypes = [ctypes.c_int]

def read_continuous_torque(interval=0.1):
    """
    Continuously read raw torque values from the device
    Args:
        interval: Time between readings in seconds (default 0.1)
    """
    # Open Simucube
    handle = ctypes.c_int()
    result = libsimucube.openSimucube(ctypes.byref(handle))
    
    if result != 0:
        print("Failed to open Simucube")
        return

    print("Successfully opened Simucube")
    torque_value = ctypes.c_int(0)
    
    try:
        print("\nMonitoring raw torque values. Press Ctrl+C to stop...\n")
        while True:
            # Get raw torque value
            result = getTorqueRaw(handle.value, ctypes.byref(torque_value))
            if result == 0:
                print(f"Raw torque value: {torque_value.value}\r", end='', flush=True)
            else:
                print(f"Error getting raw torque. Error code: {result}")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping torque reading...")
    finally:
        # Close Simucube when done
        libsimucube.closeSimucube(handle.value)
        print("Simucube closed")

if __name__ == "__main__":
    read_continuous_torque()
