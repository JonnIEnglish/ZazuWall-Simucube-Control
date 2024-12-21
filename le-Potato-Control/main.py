import time
import threading
import subprocess
from smbus2 import SMBus
import ctypes

# I2C Configuration
I2C_BUS = 1
LCD_I2C_ADDR = 0x27
LCD_WIDTH = 16  # Max characters per line

# ADC Configuration
ADC_CHANNEL = 0
ADC_PATH = f"/sys/bus/iio/devices/iio:device0/in_voltage{ADC_CHANNEL}_raw"

# Button Calibration Thresholds
button_thresholds = {
    "button_1": 5,     # Decrease incline
    "button_2": 540,   # Increase speed
    "button_3": 1807,  # Increase incline
    "button_4": 1196,  # Decrease speed
    "button_5": 2615,  # Toggle Motor
    "no_press": 3507,  # No button pressed
}

# Shared Variables
incline_angle = 0  # Incline angle in degrees
speed = 10         # Default speed in m/min
auto_mode = False  # Auto mode state
motor_running = False
shared_lock = threading.Lock()  # Lock for thread-safe variable access

# Simucube Configuration
IONI_SPEED_BASE = 1000  # Speed setpoint for 10 m/min
IONI_SPEED_STEP = 200   # Speed increment per 1 m/min

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

# Enable I2C Overlays
def enable_i2c_overlay(overlay_name):
    try:
        result = subprocess.run(['ldto', 'status'], capture_output=True, text=True)
        if overlay_name in result.stdout:
            print(f"Overlay {overlay_name}: already exists")
            return
        subprocess.check_call(['sudo', 'ldto', 'enable', overlay_name])
        print(f"Successfully enabled {overlay_name} overlay.")
    except subprocess.CalledProcessError as e:
        print(f"Error enabling I2C overlays: {e}")

# LCD Functions
def lcd_toggle_enable(bus, bits):
    bus.write_byte(LCD_I2C_ADDR, bits | 0b00000100)
    time.sleep(0.0005)
    bus.write_byte(LCD_I2C_ADDR, bits & ~0b00000100)
    time.sleep(0.0005)

def lcd_send_byte(bus, bits, mode):
    high_bits = mode | (bits & 0xF0) | 0x08  # Backlight ON
    low_bits = mode | ((bits << 4) & 0xF0) | 0x08
    bus.write_byte(LCD_I2C_ADDR, high_bits)
    lcd_toggle_enable(bus, high_bits)
    bus.write_byte(LCD_I2C_ADDR, low_bits)
    lcd_toggle_enable(bus, low_bits)

def lcd_init(bus):
    lcd_send_byte(bus, 0x33, 0)
    lcd_send_byte(bus, 0x32, 0)
    lcd_send_byte(bus, 0x06, 0)
    lcd_send_byte(bus, 0x0C, 0)
    lcd_send_byte(bus, 0x28, 0)
    lcd_send_byte(bus, 0x01, 0)
    time.sleep(0.005)

def lcd_display_string(bus, message, line):
    if line == 1:
        lcd_send_byte(bus, 0x80, 0)
    elif line == 2:
        lcd_send_byte(bus, 0xC0, 0)
    for char in message.ljust(LCD_WIDTH, " "):
        lcd_send_byte(bus, ord(char), 1)

# ADC Functions
def read_adc():
    try:
        with open(ADC_PATH, "r") as adc_file:
            return int(adc_file.read().strip())
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

# Simucube Functions
def update_simucube_speed(handle):
    setpoint = IONI_SPEED_BASE + (speed - 10) * IONI_SPEED_STEP
    libsimucube.setSpeed(handle, setpoint)

# Button Thread
def button_checking_thread(handle):
    global incline_angle, speed, auto_mode, motor_running
    last_detected = None

    while True:
        adc_value = read_adc()
        if adc_value is not None:
            detected_button = detect_button(adc_value, button_thresholds)

            if detected_button != last_detected:
                last_detected = detected_button

                with shared_lock:
                    if detected_button == "button_1":
                        incline_angle = max(incline_angle - 5, -45)
                    elif detected_button == "button_2":
                        speed = min(speed + 1, 20)
                        update_simucube_speed(handle)
                    elif detected_button == "button_3":
                        incline_angle = min(incline_angle + 5, 15)
                    elif detected_button == "button_4":
                        speed = max(speed - 1, 5)
                        update_simucube_speed(handle)
                    elif detected_button == "button_5":
                        motor_running = not motor_running
                        if motor_running:
                            update_simucube_speed(handle)
                        else:
                            libsimucube.setSpeed(handle, 0)

        time.sleep(0.05)

# LCD Thread
def lcd_updating_thread():
    with SMBus(I2C_BUS) as bus:
        lcd_init(bus)

        while True:
            with shared_lock:
                speed_text = f"Speed: {speed:02} m/min"
                incline_text = f"Tilt:   {incline_angle:+03} deg"

            line_1 = speed_text.center(LCD_WIDTH)
            line_2 = incline_text.center(LCD_WIDTH)
            lcd_display_string(bus, line_1, 1)
            lcd_display_string(bus, line_2, 2)
            time.sleep(0.5)

# Main Function
if __name__ == "__main__":
    handle = ctypes.c_int()
    try:
        enable_i2c_overlay('i2c-ao')
        enable_i2c_overlay('i2c-b')

        if libsimucube.openSimucube(ctypes.byref(handle)) == 0:
            print("Simucube opened successfully.")
            libsimucube.clearFaultsAndInitialize(handle.value)

            button_thread = threading.Thread(target=button_checking_thread, args=(handle,), daemon=True)
            lcd_thread = threading.Thread(target=lcd_updating_thread, daemon=True)

            button_thread.start()
            lcd_thread.start()

            while True:
                time.sleep(1)
        else:
            print("Failed to open Simucube.")

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        libsimucube.closeSimucube(handle.value)
