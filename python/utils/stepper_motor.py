import time
import gpiod

# Verified Le Potato GPIO Configuration (Source [1][7])
PULSE_PIN = 93  # GPIOX_14 (Physical pin 16)
DIR_PIN = 94    # GPIOX_15 (Physical pin 18)
GPIO_CHIP = "gpiochip1"

# Motor Configuration
STEPS = 100000 
PULSE_DELAY = 0.00002  # 0.5ms pulse width (adjust if needed)

def setup_gpio():
    chip = gpiod.Chip(GPIO_CHIP)
    pulse_line = chip.get_line(PULSE_PIN)
    dir_line = chip.get_line(DIR_PIN)
    
    pulse_line.request(consumer="stepper", type=gpiod.LINE_REQ_DIR_OUT)
    dir_line.request(consumer="stepper", type=gpiod.LINE_REQ_DIR_OUT)
    
    return chip, pulse_line, dir_line

def move_motor(pulse, direction, dir_value, steps):
    direction.set_value(dir_value)
    for _ in range(steps):
        pulse.set_value(1)
        time.sleep(PULSE_DELAY)
        pulse.set_value(0)
        time.sleep(PULSE_DELAY)

def main():
    chip, pulse, direction = setup_gpio()
    
    try:
        print("Moving left steps")
        move_motor(pulse, direction, 0, STEPS)
        
        time.sleep(1)  # Pause between movements
        
        # print("Moving right 100 steps")
        # move_motor(pulse, direction, 1, STEPS)
        
    finally:
        chip.close()
        print("GPIO cleanup complete")

if __name__ == "__main__":
    main()
