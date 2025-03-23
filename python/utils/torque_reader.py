import ctypes
import os
import sys

# Get base project directory
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add SimpleMotionV2 directory to dynamic library path
simplemotionv2_path = os.path.join(base_dir, "lib", "SimpleMotionV2")

# Pre-load libsimplemotionv2.so dependency
try:
    ctypes.CDLL(os.path.join(simplemotionv2_path, "libsimplemotionv2.so"))
except OSError as e:
    raise ImportError(f"Failed to load libsimplemotionv2.so: {e}")

# Now load your main library
_lib_path = os.path.join(base_dir, "lib", "libsimucube.so")
try:
    _libsimucube = ctypes.CDLL(_lib_path)
except OSError as e:
    raise ImportError(f"Failed to load torque reader library: {e}")

# Define parameters from simplemotion_defs.h
SMP_ACTUAL_TORQUE = 901  # Torque feedback (560 counts per Amp)
SMP_MOTOR_TORQUE_OR_FORCE_CONSTANT = 422  # (10000*Nm/A format)
SM_OK = 0  # Success return code

# Define function signatures for library
_libsimucube.smOpenBus.argtypes = [ctypes.c_char_p]
_libsimucube.smOpenBus.restype = ctypes.c_int

_libsimucube.smCloseBus.argtypes = [ctypes.c_int]
_libsimucube.smCloseBus.restype = None

_libsimucube.smRead1Parameter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
_libsimucube.smRead1Parameter.restype = ctypes.c_int

def open_bus(port: str) -> int:
    """
    Open a connection to the SimpleMotion bus.
    
    Args:
        port: Serial port name (e.g., '/dev/ttyUSB0')
        
    Returns:
        Handle to the bus or -1 on failure
    """
    return _libsimucube.smOpenBus(port.encode('utf-8'))

def close_bus(handle: int) -> None:
    """
    Close the SimpleMotion bus connection.
    
    Args:
        handle: Bus handle from open_bus()
    """
    if handle != -1:
        _libsimucube.smCloseBus(handle)

def get_torque(handle: int, node_id: int = 1) -> float:
    """
    Get the current torque from the motor in Newton-meters.
    
    Args:
        handle: SimpleMotion bus handle from open_bus()
        node_id: Node ID (default: 1)
        
    Returns:
        Torque in Newton-meters or None on error
    """
    if handle == -1:
        return None
    
    # Read actual torque value (in hardware units - 560 counts per Amp)
    raw_torque = ctypes.c_int()
    status = _libsimucube.smRead1Parameter(handle, node_id, SMP_ACTUAL_TORQUE, ctypes.byref(raw_torque))
    if status != SM_OK:
        print(f"Failed to read torque value, status: {status}")
        return None
    
    # Read motor torque constant (10000*Nm/A format)
    torque_constant_raw = ctypes.c_int()
    status = _libsimucube.smRead1Parameter(handle, node_id, SMP_MOTOR_TORQUE_OR_FORCE_CONSTANT, ctypes.byref(torque_constant_raw))
    if status != SM_OK:
        print(f"Failed to read torque constant, status: {status}")
        # Use a default value if we can't read it
        torque_constant = 1.0
    else:
        torque_constant = torque_constant_raw.value / 10000.0  # Convert from 10000*Nm/A format
    
    # Convert from counts to Amps, then to Nm
    torque_in_amps = raw_torque.value / 560.0  # Convert from counts to Amps
    torque_in_nm = torque_in_amps * torque_constant
    
    return torque_in_nm

def find_available_ports():
    """
    Find available serial ports that might be connected to the device.
    
    Returns:
        List of available port paths
    """
    import glob
    return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')

def monitor_torque():
    """
    Monitor and print torque values continuously.
    """
    # Find available ports
    ports = find_available_ports()
    
    if not ports:
        print("No serial ports found. Make sure your device is connected.")
        return
    
    # Try to connect to each port
    handle = -1
    for port in ports:
        print(f"Trying to connect to {port}...")
        handle = open_bus(port)
        if handle != -1:
            print(f"Connected to {port}")
            break
    
    if handle == -1:
        print("Failed to connect to any port")
        return
    
    try:
        # Read torque continuously
        print("Reading torque values. Press Ctrl+C to exit.")
        while True:
            torque = get_torque(handle)
            if torque is not None:
                print(f"Current torque: {torque:.3f} Nm")
            else:
                print("Failed to read torque")
            
            import time
            time.sleep(0.1)  # Read every 100ms
    
    except KeyboardInterrupt:
        print("Monitoring stopped")
    
    finally:
        # Clean up
        close_bus(handle)
        print("Connection closed")

if __name__ == "__main__":
    monitor_torque()
