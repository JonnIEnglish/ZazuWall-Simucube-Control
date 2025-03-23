import time

# ADC Configuration
ADC_CHANNEL = 0
ADC_PATH = f"/sys/bus/iio/devices/iio:device0/in_voltage{ADC_CHANNEL}_raw"

# Button Calibration Thresholds
button_thresholds = {
    "button_2": 540,   # Increase speed
    "button_4": 1196,  # Decrease speed
    "no_press": 3507,  # No button pressed
}

# ADC Reader class
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

# Enhanced button detection
def detect_button(adc_value, thresholds):
    button_tolerance = 100  # Tolerance for button detection
    
    for button, threshold in thresholds.items():
        if abs(adc_value - threshold) < button_tolerance:
            return button
    
    return "no_press"  # Default if no button matches within tolerance

def main():
    # Initialize speed setpoint
    speed_setpoint = 1000  # Starting value
    
    # Initialize ADC reader
    adc_reader = ADCReader(ADC_PATH)
    
    # Variables for button handling
    last_button = "no_press"
    last_press_time = 0
    debounce_time = 0.1  # 100ms debounce for more stability
    
    # Button state tracking
    button_pressed = False
    
    print(f"Current speed setpoint: {speed_setpoint}")
    print("Press Ctrl+C to exit")
    print("- Button 2: Increase speed by 200")
    print("- Button 4: Decrease speed by 200")
    
    try:
        while True:
            # Read ADC value
            adc_value = adc_reader.read()
            
            if adc_value is not None:
                # Detect button press
                current_button = detect_button(adc_value, button_thresholds)
                current_time = time.time()
                
                # Only act if button changed and debounce time passed
                if current_button != last_button and (current_time - last_press_time) > debounce_time:
                    # Button state has changed
                    last_press_time = current_time
                    
                    # Check for button press events (from no_press to a button)
                    if last_button == "no_press" and current_button != "no_press":
                        # Button has been pressed
                        button_pressed = True
                        
                        # Process button press
                        if current_button == "button_2":  # Increase speed
                            speed_setpoint += 200
                            print(f"Speed increased to: {speed_setpoint}")
                        elif current_button == "button_4":  # Decrease speed
                            speed_setpoint -= 200
                            print(f"Speed decreased to: {speed_setpoint}")
                    
                    # Update last button state
                    last_button = current_button
            
            time.sleep(0.01)  # Small delay to reduce CPU usage
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        adc_reader.close()

if __name__ == "__main__":
    main()