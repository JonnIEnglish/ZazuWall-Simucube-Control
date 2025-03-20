import ctypes
import time

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

# Hold motor speed for a specific duration
def hold_motor_speed(handle, speed, duration):
    """Set and hold motor speed for the given duration."""
    set_speed_result = libsimucube.setSpeed(handle.value, speed)
    if set_speed_result == 0:
        print(f"Speed set to {speed}. Holding for {duration} seconds.")
        start_time = time.time()
        while time.time() - start_time < duration:
            torque = ctypes.c_int()
            if libsimucube.getTorque(handle.value, ctypes.byref(torque)) == 0:
                print(f"Torque: {torque.value} Nm")
            time.sleep(0.1)  # Polling delay
    else:
        print(f"Failed to set speed to {speed}. Error code: {set_speed_result}")

# Test the functions
handle = ctypes.c_int()

if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
    print("Simucube opened successfully.")

    if libsimucube.clearFaultsAndInitialize(handle.value) == 0:
        print("Faults cleared and motor initialized.")

        speed = 500  # Speed setpoint
        duration = 5  # Duration to hold the speed

        # Hold the motor at the specified speed for the duration
        hold_motor_speed(handle, speed, duration)

        # Stop the motor
        if libsimucube.setSpeed(handle.value, 0) == 0:
            print("Motor stopped (speed set to 0).")
        else:
            print("Failed to stop the motor.")

    libsimucube.closeSimucube(handle.value)
    print("Simucube closed.")
else:
    print("Failed to open Simucube.")
