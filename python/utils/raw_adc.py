import time

while True:
    try:
        with open("/sys/bus/iio/devices/iio:device0/in_voltage0_raw", "r") as adc_file:
            raw_value = int(adc_file.read().strip())
            adc_voltage = (raw_value / 4095) * 1.8  # Assuming a 10-bit ADC and 1.8V reference
            print(f"ADC value: {adc_voltage:.2f} V")
    except Exception as e:
        print(f"Error: {e}")
