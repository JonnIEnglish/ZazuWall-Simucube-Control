import time
import random
from smbus2 import SMBus

# I2C Configuration
I2C_BUS = 1  # /dev/i2c-1
LCD_I2C_ADDR = 0x27  # Detected address for your LCD
LCD_WIDTH = 16  # Max characters per line

# ADC Configuration
ADC_CHANNEL = 0
ADC_PATH = f"/sys/bus/iio/devices/iio:device0/in_voltage{ADC_CHANNEL}_raw"

# Button Calibration Thresholds
button_thresholds = {
    "no_press": 3507,
    "button_1": 5,
    "button_2": 540,
    "button_3": 1807,
    "button_4": 1196,
    "button_5": 2615,
}

# LCD Functions
def lcd_toggle_enable(bus, bits):
    """Toggle the enable bit on the LCD."""
    bus.write_byte(LCD_I2C_ADDR, bits | 0b00000100)
    time.sleep(0.0005)
    bus.write_byte(LCD_I2C_ADDR, bits & ~0b00000100)
    time.sleep(0.0005)

def lcd_send_byte(bus, bits, mode):
    """Send a byte to the LCD."""
    high_bits = mode | (bits & 0xF0) | 0x08  # Backlight ON
    low_bits = mode | ((bits << 4) & 0xF0) | 0x08
    bus.write_byte(LCD_I2C_ADDR, high_bits)
    lcd_toggle_enable(bus, high_bits)
    bus.write_byte(LCD_I2C_ADDR, low_bits)
    lcd_toggle_enable(bus, low_bits)

def lcd_init(bus):
    """Initialize the LCD."""
    lcd_send_byte(bus, 0x33, 0)  # Initialize
    lcd_send_byte(bus, 0x32, 0)  # Set to 4-bit mode
    lcd_send_byte(bus, 0x06, 0)  # Cursor move direction
    lcd_send_byte(bus, 0x0C, 0)  # Display ON, Cursor OFF
    lcd_send_byte(bus, 0x28, 0)  # 2 line display
    lcd_send_byte(bus, 0x01, 0)  # Clear display
    time.sleep(0.005)

def lcd_display_string(bus, message, line):
    """Display a string on the LCD."""
    if line == 1:
        lcd_send_byte(bus, 0x80, 0)
    elif line == 2:
        lcd_send_byte(bus, 0xC0, 0)
    for char in message.ljust(LCD_WIDTH, " "):
        lcd_send_byte(bus, ord(char), 1)

# ADC Functions
def read_adc():
    """Read the ADC raw value."""
    try:
        with open(ADC_PATH, "r") as adc_file:
            raw_value = int(adc_file.read().strip())
            return raw_value
    except Exception as e:
        print(f"Error reading ADC: {e}")
        return None

def detect_button(adc_value):
    """Detect which button is pressed based on calibrated ADC values."""
    closest_button = None
    closest_diff = float("inf")
    for button, threshold in button_thresholds.items():
        diff = abs(adc_value - threshold)
        if diff < closest_diff:
            closest_button = button
            closest_diff = diff
    return closest_button

# Game Logic
def button_catch_game(bus):
    score = 0
    game_time = 30  # 30 seconds game duration
    start_time = time.time()

    while time.time() - start_time < game_time:
        target_button = random.choice([f"button_{i}" for i in range(1, 6)])
        lcd_display_string(bus, f"Press {target_button}!", 1)
        lcd_display_string(bus, f"Score: {score}", 2)

        button_pressed = None
        while button_pressed != target_button:
            adc_value = read_adc()
            if adc_value is not None:
                button_pressed = detect_button(adc_value)
                if button_pressed == target_button:
                    score += 1
                    lcd_display_string(bus, "Correct!        ", 1)
                    time.sleep(1)
                    break

        time.sleep(0.5)  # Short delay between rounds

    # Game Over
    lcd_display_string(bus, "Game Over!      ", 1)
    lcd_display_string(bus, f"Final Score: {score}", 2)
    time.sleep(5)
    lcd_display_string(bus, "                 ", 1)
    lcd_display_string(bus, "                 ", 2)

# Main Function
if __name__ == "__main__":
    try:
        with SMBus(I2C_BUS) as bus:
            # Initialize the LCD
            lcd_init(bus)

            # Start the game
            button_catch_game(bus)

    except Exception as e:
        print(f"Error: {e}")
