import gpiod
import time

# GPIO Configuration
CHIP_NAME = "gpiochip0"  # GPIO chip for GPIOAO bank
LINE_OFFSET = 6          # GPIOAO_6 (Pin 12)

# Setup GPIO
chip = gpiod.Chip(CHIP_NAME)
line = chip.get_line(LINE_OFFSET)
line.request(consumer="nc_sensor", type=gpiod.LINE_REQ_DIR_IN)

print("Testing GPIOAO_6 (Pin 12)...")

try:
    while True:
        # Read the value of GPIOAO_6
        value = line.get_value()
        if value == 1:
            print("Sensor Idle (connection closed).")
        else:
            print("Sensor Triggered (connection open).")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    chip.close()
