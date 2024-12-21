import time
import threading
from smbus2 import SMBus
import subprocess

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
    "button_5": 2615,  # Toggle Auto Mode
    "no_press": 3507,  # No button pressed
}

# Shared Variables
incline_angle = 0  # Incline angle in degrees (starts at 0)
speed = 10         # Default speed in m/min
auto_mode = False  # Auto mode state
shared_lock = threading.Lock()  # Lock for thread-safe variable access

# Enable I2C Overlays
def enable_i2c_overlay(overlay_name):
    try:
        # Check if the overlay is already enabled
        result = subprocess.run(['ldto', 'status'], capture_output=True, text=True)
        if overlay_name in result.stdout:
            print(f"Overlay {overlay_name}: already exists")
            return
        # Enable the overlay if not already enabled
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
def button_checking_thread():
    global incline_angle, speed, auto_mode
    last_detected = None

    while True:
        adc_value = read_adc()
        if adc_value is not None:
            detected_button = detect_button(adc_value, button_thresholds)

            # Only act if the button press changes
            if detected_button != last_detected:
                last_detected = detected_button

                with shared_lock:
                    if detected_button == "button_1":
                        incline_angle = max(incline_angle - 5, -45)  # Decrease incline
                    elif detected_button == "button_2":
                        speed = min(speed + 1, 20)  # Increase speed
                    elif detected_button == "button_3":
                        incline_angle = min(incline_angle + 5, 15)  # Increase incline
                    elif detected_button == "button_4":
                        speed = max(speed - 1, 5)  # Decrease speed
                    elif detected_button == "button_5":
                        auto_mode = not auto_mode  # Toggle auto mode

        time.sleep(0.05)  # Polling delay

# LCD Updating Thread
def lcd_updating_thread():
    with SMBus(I2C_BUS) as bus:
        lcd_init(bus)

        while True:
            with shared_lock:
                speed_text = f"Speed: {speed:02} m/min"
                incline_text = f"Tilt:   {incline_angle:+03} deg"

            # Center both lines
            line_1 = speed_text.center(LCD_WIDTH)
            line_2 = incline_text.center(LCD_WIDTH)

            # Display on LCD
            lcd_display_string(bus, line_1, 1)
            lcd_display_string(bus, line_2, 2)

            time.sleep(0.5)  # Refresh rate

# Main Function
if __name__ == "__main__":
    try:
        # Enable I2C overlays
        enable_i2c_overlay('i2c-ao')
        enable_i2c_overlay('i2c-b')

        # Create and start threads
        button_thread = threading.Thread(target=button_checking_thread, daemon=True)
        lcd_thread = threading.Thread(target=lcd_updating_thread, daemon=True)

        button_thread.start()
        lcd_thread.start()

        # Keep the main thread running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting...")
