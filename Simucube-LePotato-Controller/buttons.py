import time

# ADC Channel to use
ADC_CHANNEL = 0  # Use 0 for SARADC_CH0 or 2 for SARADC_CH2

# Path to ADC raw value
ADC_PATH = f"/sys/bus/iio/devices/iio:device0/in_voltage{ADC_CHANNEL}_raw"

# Button calibration data
button_thresholds = {}

def read_adc():
    """Read the ADC raw value."""
    try:
        with open(ADC_PATH, "r") as adc_file:
            raw_value = int(adc_file.read().strip())
            return raw_value
    except Exception as e:
        print(f"Error reading ADC: {e}")
        return None

def calibrate_buttons(button_count):
    """
    Perform auto-calibration for each button and "no button pressed" mode.
    """
    global button_thresholds
    button_thresholds = {}  # Reset thresholds

    print("\nAuto-Calibration Mode")
    print("---------------------")
    print("Ensure only the requested button is pressed when prompted.")
    print("Wait for 'CALIBRATED!' message before releasing the button.\n")

    # Add the "no button pressed" mode
    print("Step 1: Leave all buttons unpressed.")
    input("Press Enter to start calibration for 'no button pressed': ")
    adc_value = read_adc()
    if adc_value is not None:
        button_thresholds["no_press"] = adc_value
        print(f"Calibrated 'no button pressed' with ADC value: {adc_value}\n")
    time.sleep(1)

    # Calibrate each button
    for i in range(1, button_count + 1):
        print(f"Step {i + 1}: Press Button {i}.")
        input(f"Press Enter to start calibration for Button {i}: ")
        adc_value = read_adc()
        if adc_value is not None:
            button_thresholds[f"button_{i}"] = adc_value
            print(f"Calibrated Button {i} with ADC value: {adc_value}\n")
        time.sleep(1)

    print("\nCalibration Complete!")
    print("Calibrated Thresholds:", button_thresholds)
    return button_thresholds

def detect_button(adc_value):
    """
    Detect which button is pressed based on calibrated ADC values.
    """
    if not button_thresholds:
        return "Uncalibrated"

    # Calculate ranges based on calibrated values
    closest_button = None
    closest_diff = float("inf")
    for button, threshold in button_thresholds.items():
        diff = abs(adc_value - threshold)
        if diff < closest_diff:
            closest_button = button
            closest_diff = diff

    return closest_button

if __name__ == "__main__":
    # Number of buttons to calibrate
    button_count = 5

    # Perform calibration
    calibrate_buttons(button_count)

    print("\nButton Detection Mode")
    print("---------------------")
    print("Press any button to test detection. Use Ctrl+C to exit.\n")

    try:
        while True:
            adc_value = read_adc()
            if adc_value is not None:
                detected_button = detect_button(adc_value)
                print(f"ADC Value: {adc_value}, Detected: {detected_button}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nExiting...")
