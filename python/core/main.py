import time
import threading
from smbus2 import SMBus
import subprocess
import ctypes
from collections import deque

# Import utilities from utils package
from utils.i2c_enable import enable_i2c_overlays
from utils.lcd_control import lcd_init, lcd_display_string, lcd_send_byte

# I2C Configuration
I2C_BUS = 1
LCD_I2C_ADDR = 0x27
LCD_WIDTH = 16  # Max characters per line

# ADC Configuration
ADC_CHANNEL = 0
ADC_PATH = f"/sys/bus/iio/devices/iio:device0/in_voltage{ADC_CHANNEL}_raw"

# Button Calibration Thresholds
button_thresholds = {
    "button_1": 5,     # Reserved for incline adjustments
    "button_2": 540,   # Increase speed
    "button_3": 1807,  # Reserved for incline adjustments
    "button_4": 1196,  # Decrease speed
    "button_5": 2615,  # No action currently
    "no_press": 3507,  # No button pressed
}

# Motor Configuration
SPEED_SETPOINT = 1500  # Default speed (1500 rpm = 10 m/min)
MAX_SPEED_RPM = 3000   # Max speed (20 m/min)
MIN_SPEED_RPM = 1000   # Min speed (5 m/min)
SPEED_STEP_RPM = 200   # Increment/decrement step (1 m/min)
POLL_DELAY = 0.05      # Polling delay

# Shared Variables
current_speed = SPEED_SETPOINT
shared_lock = threading.Lock()

# Load the shared library
libsimucube = ctypes.CDLL("lib/libsimucube.so")

# Define function signatures
libsimucube.openSimucube.restype = ctypes.c_int
libsimucube.openSimucube.argtypes = [ctypes.POINTER(ctypes.c_int)]

libsimucube.closeSimucube.restype = None
libsimucube.closeSimucube.argtypes = [ctypes.c_int]

libsimucube.setSpeed.restype = ctypes.c_int
libsimucube.setSpeed.argtypes = [ctypes.c_int, ctypes.c_int]

libsimucube.clearFaultsAndInitialize.restype = ctypes.c_int
libsimucube.clearFaultsAndInitialize.argtypes = [ctypes.c_int]

# Enable IONI Configuration
def activate_ioni():
    try:
        # Call the binary
        result = subprocess.run(
            ["python/enable_ioni_configurator"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Output from IONI activation:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error activating IONI:")
        print(e.stderr)

# LCD Functions
def lcd_toggle_enable(bus, bits):
    bus.write_byte(LCD_I2C_ADDR, bits | 0b00000100)
    time.sleep(0.0005)
    bus.write_byte(LCD_I2C_ADDR, bits & ~0b00000100)
    time.sleep(0.0005)

# ADC Functions
def read_adc():
    try:
        with open(ADC_PATH, "r") as adc_file:
            raw_value = int(adc_file.read().strip())
            return raw_value
    except Exception as e:
        print(f"Error reading ADC: {e}")
        return None

def detect_button(adc_value, thresholds):
    closest_button = None
    closest_diff = float("inf")
    for button, threshold in thresholds.items():
        diff = abs(adc_value - threshold)
        if diff < closest_diff:
            closest_button = button
            closest_diff = diff
    return closest_button

# Button Checking Thread
def button_checking_thread(handle):
    global current_speed
    last_detected = None

    while True:
        adc_value = read_adc()
        if adc_value is not None:
            detected_button = detect_button(adc_value, button_thresholds)

            if detected_button != last_detected:
                last_detected = detected_button

                with shared_lock:
                    if detected_button == "button_2":
                        current_speed = min(current_speed + SPEED_STEP_RPM, MAX_SPEED_RPM)
                        libsimucube.setSpeed(handle.value, current_speed)
                        print(f"Speed increased to {current_speed} RPM.")
                    elif detected_button == "button_4":
                        current_speed = max(current_speed - SPEED_STEP_RPM, MIN_SPEED_RPM)
                        libsimucube.setSpeed(handle.value, current_speed)
                        print(f"Speed decreased to {current_speed} RPM.")
        time.sleep(0.05)

# LCD Updating Thread
def lcd_updating_thread():
    with SMBus(I2C_BUS) as bus:
        lcd_init(bus)

        while True:
            with shared_lock:
                speed_m_per_min = current_speed // 150
                line_1 = f"Speed: {speed_m_per_min:02} m/min".center(LCD_WIDTH)
                line_2 = "Motor Control".center(LCD_WIDTH)

            lcd_display_string(bus, line_1, 1)
            lcd_display_string(bus, line_2, 2)
            time.sleep(0.5)

# Main Function
if __name__ == "__main__":
    handle = ctypes.c_int()

    try:
        # Activate IONI configuration
        activate_ioni()

        # Open Simucube
        if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
            print("Simucube opened successfully.")

            # Clear faults and initialize
            print("Clearing faults and initializing Simucube...")
            if libsimucube.clearFaultsAndInitialize(handle.value) == 0:
                print("Faults cleared and motor initialized.")

                # Initialize speed
                libsimucube.setSpeed(handle.value, current_speed)

                # Start threads
                button_thread = threading.Thread(target=button_checking_thread, args=(handle,), daemon=True)
                lcd_thread = threading.Thread(target=lcd_updating_thread, daemon=True)

                button_thread.start()
                lcd_thread.start()

                # Keep the main thread running
                while True:
                    time.sleep(1)
            else:
                print("Failed to clear faults and initialize motor.")
        else:
            print("Failed to open Simucube.")

    except KeyboardInterrupt:
        print("Exiting...")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        libsimucube.setSpeed(handle.value, 0)
        libsimucube.closeSimucube(handle.value)
        print("Simucube closed.")
