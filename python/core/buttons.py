import time
import threading
from smbus2 import SMBus
import subprocess
from queue import Queue, Empty

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

# Communication queue for thread communication
update_queue = Queue()

# ADC Reader class for efficient file handling
class ADCReader:
    def __init__(self, path):
        self.path = path
        self.file = None
        
    def open(self):
        try:
            self.file = open(self.path, "r")
            return True
        except Exception as e:
            print(f"Error opening ADC file: {e}")
            return False
            
    def read(self):
        if not self.file:
            if not self.open():
                return None
        
        try:
            self.file.seek(0)
            raw_value = int(self.file.read().strip())
            return raw_value
        except Exception as e:
            print(f"Error reading ADC: {e}")
            self.close()
            return None
            
    def close(self):
        if self.file:
            self.file.close()
            self.file = None

# Enable I2C Overlays (unchanged)
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

# LCD Functions (unchanged)
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

# Button detection with optimizations
def detect_button(adc_value, thresholds):
    closest_button = None
    closest_diff = float("inf")
    
    for button, threshold in thresholds.items():
        diff = abs(adc_value - threshold)
        if diff < closest_diff:
            closest_button = button
            closest_diff = diff
            # Early termination for exact matches
            if diff < 10:  # Small tolerance
                break
    return closest_button

# Button Checking Thread - Optimized
def button_checking_thread():
    adc_reader = ADCReader(ADC_PATH)
    last_detected = None
    last_change_time = 0
    debounce_time = 0.05  # 50ms debounce
    
    # Initial values
    incline_angle = 0
    speed = 10
    auto_mode = False
    
    try:
        while True:
            adc_value = adc_reader.read()
            if adc_value is not None:
                detected_button = detect_button(adc_value, button_thresholds)
                current_time = time.time()
                
                # Only act if button changed and debounce time passed
                if detected_button != last_detected and (current_time - last_change_time) > debounce_time:
                    last_detected = detected_button
                    last_change_time = current_time
                    
                    # Process button press and send updates to LCD thread
                    if detected_button == "button_1":
                        incline_angle = max(incline_angle - 5, -45)
                        update_queue.put(("incline", incline_angle))
                    elif detected_button == "button_2":
                        speed = min(speed + 1, 20)
                        update_queue.put(("speed", speed))
                    elif detected_button == "button_3":
                        incline_angle = min(incline_angle + 5, 15)
                        update_queue.put(("incline", incline_angle))
                    elif detected_button == "button_4":
                        speed = max(speed - 1, 5)
                        update_queue.put(("speed", speed))
                    elif detected_button == "button_5":
                        auto_mode = not auto_mode
                        update_queue.put(("auto_mode", auto_mode))
            
            time.sleep(0.01)  # Reduced to 10ms for faster response
    finally:
        adc_reader.close()

# LCD Updating Thread - Optimized
def lcd_updating_thread():
    # Current display values
    current_speed = 10
    current_incline = 0
    
    with SMBus(I2C_BUS) as bus:
        lcd_init(bus)
        
        # Initial display
        speed_text = f"Speed: {current_speed:02} m/min"
        incline_text = f"Tilt:   {current_incline:+03} deg"
        lcd_display_string(bus, speed_text.center(LCD_WIDTH), 1)
        lcd_display_string(bus, incline_text.center(LCD_WIDTH), 2)
        
        while True:
            # Check for updates
            try:
                # Process all available updates in queue
                while not update_queue.empty():
                    update_type, value = update_queue.get_nowait()
                    
                    if update_type == "speed":
                        current_speed = value
                        speed_text = f"Speed: {current_speed:02} m/min"
                        lcd_display_string(bus, speed_text.center(LCD_WIDTH), 1)
                    
                    elif update_type == "incline":
                        current_incline = value
                        incline_text = f"Tilt:   {current_incline:+03} deg"
                        lcd_display_string(bus, incline_text.center(LCD_WIDTH), 2)
                    
                    # Mark task as done
                    update_queue.task_done()
            except Empty:
                pass  # No updates
            
            time.sleep(0.1)  # Check for updates more frequently

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
