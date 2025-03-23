import ctypes
import os

class SpeedController:
    def __init__(self, port="/dev/ttyUSB0"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(script_dir))
        self.lib = ctypes.CDLL(os.path.join(root_dir, 'lib', 'libspeed_control.so'))
        self.lib.open_connection.argtypes = [ctypes.c_char_p]
        self.lib.open_connection.restype = ctypes.c_int
        self.lib.set_speed.argtypes = [ctypes.c_int]
        self.lib.set_speed.restype = ctypes.c_int
        self.lib.check_faults.restype = ctypes.c_int
        self.lib.clear_faults.restype = ctypes.c_int
        self.lib.close_connection.restype = None

        if (err := self.lib.open_connection(port.encode())) != 0:
            raise RuntimeError(f"Connection failed (error: {err})")

        # Check for faults
        if (faults := self.lib.check_faults()) != 0:
            print(f"Faults detected: {faults}. Attempting to clear...")
            if (clear_err := self.lib.clear_faults()) != 0:
                raise RuntimeError(f"Failed to clear faults (error: {clear_err})")
            print("Faults cleared successfully.")

    def set_speed(self, rpm: int):
        if (err := self.lib.set_speed(rpm)) != 0:
            raise RuntimeError(f"Speed set failed (error: {err})")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.lib.close_connection()

# Usage example
if __name__ == "__main__":
    with SpeedController() as controller:
        try:
            controller.set_speed(2000)
            input("Press Enter to stop...")
        except RuntimeError as e:
            print(f"Error: {e}")
        finally:
            try:
                controller.set_speed(0)
            except RuntimeError as e:
                print(f"Failed to stop motor: {e}")
