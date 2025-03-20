import time
import gpiod

# GPIO Configuration for Stepper Motor
PULSE_PIN = 23  # GPIO23 (Physical pin 16)
DIR_PIN = 18    # GPIO18 (Physical pin 12)
GPIO_CHIP = "/dev/gpiochip1"  # GPIO chip device (updated)

# Stepper Motor Pulse Delay
PULSE_DELAY = 0.001  # Delay between pulses (adjust for speed)

# GPIO Initialization
def setup_gpio():
    try:
        chip = gpiod.Chip(GPIO_CHIP)
        print(f"GPIO chip detected: {GPIO_CHIP}")

        pulse_line = chip.get_line(PULSE_PIN)
        dir_line = chip.get_line(DIR_PIN)

        pulse_line.request(consumer="StepperMotor", type=gpiod.LINE_REQ_DIR_OUT)
        dir_line.request(consumer="StepperMotor", type=gpiod.LINE_REQ_DIR_OUT)

        print(f"Successfully configured GPIO lines: PULSE_PIN={PULSE_PIN}, DIR_PIN={DIR_PIN}")
        return chip, pulse_line, dir_line

    except OSError as e:
        print(f"Error during GPIO setup: {e}")
        raise

# GPIO Functions for Stepper Motor
def step_motor(pulse_line, dir_line, direction, steps=1):
    """Step the motor in the given direction for a number of steps."""
    dir_line.set_value(direction)  # Set direction
    for _ in range(steps):
        pulse_line.set_value(1)  # Pulse HIGH
        time.sleep(PULSE_DELAY)
        pulse_line.set_value(0)  # Pulse LOW
        time.sleep(PULSE_DELAY)

# Main Function
if __name__ == "__main__":
    try:
        # Setup GPIO
        chip, pulse_line, dir_line = setup_gpio()

        # Test motor movement
        print("Testing stepper motor: moving forward 50 steps")
        step_motor(pulse_line, dir_line, 1, 50)  # Move forward

        print("Testing stepper motor: moving backward 50 steps")
        step_motor(pulse_line, dir_line, 0, 50)  # Move backward

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if 'chip' in locals():
            chip.close()
