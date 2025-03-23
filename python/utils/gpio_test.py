import time
import gpiod

# Selected GPIO Pins
DIR_PIN = 94    # Physical pin 18 (GPIOX_15)
CLK_PIN = 93    # Physical pin 32 (GPIOX_16)
GPIO_CHIP = "gpiochip1"  # Chip managing these pins

def setup_gpio():
    try:
        chip = gpiod.Chip(GPIO_CHIP)
        print(f"Opened GPIO chip: {chip.label}")

        dir_line = chip.get_line(DIR_PIN)
        clk_line = chip.get_line(CLK_PIN)

        dir_line.request(consumer="Test", type=gpiod.LINE_REQ_DIR_OUT)
        clk_line.request(consumer="Test", type=gpiod.LINE_REQ_DIR_OUT)

        print(f"Configured DIR_PIN={DIR_PIN} and CLK_PIN={CLK_PIN}")
        return chip, dir_line, clk_line

    except Exception as e:
        print(f"Error setting up GPIOs: {e}")
        raise

def toggle_pins(dir_line, clk_line):
    try:
        for _ in range(10):  # Toggle pins for ten cycles
            print("Setting pins HIGH")
            dir_line.set_value(1)  # Set DIR_PIN HIGH
            clk_line.set_value(1)  # Set CLK_PIN HIGH
            time.sleep(1)

            print("Setting pins LOW")
            dir_line.set_value(0)  # Set DIR_PIN LOW
            clk_line.set_value(0)  # Set CLK_PIN LOW
            time.sleep(1)

    except Exception as e:
        print(f"Error toggling pins: {e}")
        raise

def main():
    chip, dir_line, clk_line = None, None, None
    try:
        chip, dir_line, clk_line = setup_gpio()
        toggle_pins(dir_line, clk_line)

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        if chip:
            chip.close()
            print("Released GPIO resources")

if __name__ == "__main__":
    main()
