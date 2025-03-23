from smbus2 import SMBus
import time

# I2C Configuration
I2C_BUS = 1  # /dev/i2c-1
LCD_I2C_ADDR = 0x27  # Detected address
LCD_WIDTH = 16  # Max characters per line

# LCD Commands
LCD_CHR = 1  # Mode - Sending data
LCD_CMD = 0  # Mode - Sending command
LCD_LINE_1 = 0x80  # Address for 1st line
LCD_LINE_2 = 0xC0  # Address for 2nd line
LCD_BACKLIGHT = 0x08  # Backlight ON
ENABLE = 0b00000100  # Enable bit

# Toggle Enable with increased delay
def lcd_toggle_enable(bus, bits):
    """Toggle the enable bit on the LCD."""
    retries = 3
    while retries > 0:
        try:
            bus.write_byte(LCD_I2C_ADDR, bits | ENABLE)
            time.sleep(0.005)  # Increase delay significantly
            bus.write_byte(LCD_I2C_ADDR, bits & ~ENABLE)
            time.sleep(0.005)  # Increase delay significantly
            return
        except Exception as e:
            retries -= 1
            print(f"Toggle error (retries left: {retries}): {e}")
            time.sleep(0.1)  # Longer recovery delay
    
    # If we get here, all retries failed
    print("Toggle enable failed after multiple attempts")

# Send Byte with error handling
def lcd_send_byte(bus, bits, mode):
    """Send a byte to the LCD with error handling."""
    try:
        high_bits = mode | (bits & 0xF0) | LCD_BACKLIGHT
        low_bits = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT

        bus.write_byte(LCD_I2C_ADDR, high_bits)
        lcd_toggle_enable(bus, high_bits)
        time.sleep(0.002)  # Add delay between operations

        bus.write_byte(LCD_I2C_ADDR, low_bits)
        lcd_toggle_enable(bus, low_bits)
        time.sleep(0.002)  # Add delay between operations
    except Exception as e:
        print(f"Error sending byte {hex(bits)}: {e}")
        # Continue despite errors
        time.sleep(0.05)  # Longer recovery delay

# LCD Initialization
def lcd_init(bus):
    """Initialize the LCD."""
    lcd_send_byte(bus, 0x33, LCD_CMD)  # Initialize
    lcd_send_byte(bus, 0x32, LCD_CMD)  # Set to 4-bit mode
    lcd_send_byte(bus, 0x06, LCD_CMD)  # Cursor move direction
    lcd_send_byte(bus, 0x0C, LCD_CMD)  # Display ON, Cursor OFF
    lcd_send_byte(bus, 0x28, LCD_CMD)  # 2 line display
    lcd_send_byte(bus, 0x01, LCD_CMD)  # Clear display
    time.sleep(0.2)  # Increase delay to 200ms to ensure LCD is ready

# Display String
def lcd_display_string(bus, message, line):
    """Display a string on the LCD."""
    lcd_send_byte(bus, line, LCD_CMD)
    for char in message.ljust(LCD_WIDTH, " "):  # Pad string to LCD width
        lcd_send_byte(bus, ord(char), LCD_CHR)

# Clear LCD
def lcd_clear(bus):
    """Clear the LCD display."""
    lcd_send_byte(bus, 0x01, LCD_CMD)
    time.sleep(0.005)

# Main Program
if __name__ == "__main__":
    try:
        print("Opening I2C bus...")
        with SMBus(I2C_BUS) as bus:
            print("Initializing LCD...")
            try:
                lcd_init(bus)
                print("LCD initialized successfully")
                
                # Display initial messages
                lcd_display_string(bus, "Hello, Le Potato!", LCD_LINE_1)
                lcd_display_string(bus, "I2C LCD Ready!", LCD_LINE_2)
                time.sleep(3)

                # Dynamic updates
                counter = 0
                while True:
                    lcd_clear(bus)
                    lcd_display_string(bus, f"Counter: {counter}", LCD_LINE_1)
                    lcd_display_string(bus, "Working...", LCD_LINE_2)
                    counter += 1
                    time.sleep(1)
            except Exception as e:
                print(f"LCD operation error: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"Bus connection error: {e}")
        import traceback
        traceback.print_exc()
