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

# Test the functions
handle = ctypes.c_int()

if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
    print("Simucube opened successfully.")

    if libsimucube.clearFaultsAndInitialize(handle.value) == 0:
        print("Faults cleared and motor initialized.")

        for speed in range(500, 2000, 100):
            if libsimucube.setSpeed(handle.value, speed) == 0:
                print(f"Speed set to {speed}.")

            # Wait for 5 seconds
            time.sleep(5)

            torque = ctypes.c_int()
            if libsimucube.getTorque(handle.value, ctypes.byref(torque)) == 0:
                print(f"Torque: {torque.value} Nm")

        if libsimucube.setSpeed(handle.value, 0) == 0:
            print("Motor stopped (speed set to 0).")

    libsimucube.closeSimucube(handle.value)
    print("Simucube closed.")
else:
    print("Failed to open Simucube.")
