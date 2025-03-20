import ctypes
import time

# Load SimpleMotion V2 Library
libsimucube = ctypes.CDLL("/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/Ioni_Functions/SimpleMotionV2/libsimplemotionv2.so")

# Define function signatures
libsimucube.smSetParameter.restype = ctypes.c_int
libsimucube.smSetParameter.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
libsimucube.smOpenBus.restype = ctypes.c_void_p
libsimucube.smOpenBus.argtypes = [ctypes.c_char_p]
libsimucube.smCloseBus.restype = None
libsimucube.smCloseBus.argtypes = [ctypes.c_void_p]

# Parse and write configuration
def write_configuration(bus_handle, config):
    for param in config:
        addr = int(param["addr"])
        value = int(float(param["value"]) * float(param["scaling"]))
        readonly = param["readonly"].lower() == "true"

        if readonly:
            print(f"Skipping read-only parameter {param['name']} at address {addr}")
            continue

        result = libsimucube.smSetParameter(bus_handle, addr, value)
        if result == 0:
            print(f"Set parameter {param['name']} (addr {addr}) to {value} successfully.")
        else:
            print(f"Failed to set parameter {param['name']} (addr {addr}). Error code: {result}")

# Main function
if __name__ == "__main__":
    # Open bus
    bus = libsimucube.smOpenBus(b"/dev/ttyUSB0")
    if not bus:
        print("Failed to open bus.")
        exit(1)

    # Configuration (example structure, replace with parsed data)
    config = [
        {"addr": "6014", "value": "10721", "scaling": "1", "readonly": "true", "name": "GCFWVER"},
        {"addr": "425", "value": "0", "scaling": "1000", "readonly": "false", "name": "TRA1"},
        # Add other parameters from the parsed data
    ]

    try:
        write_configuration(bus, config)
    finally:
        libsimucube.smCloseBus(bus)
        print("Bus closed.")
