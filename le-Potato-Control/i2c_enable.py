import subprocess

def enable_i2c_overlays():
    try:
        # Enable I2C AO overlay
        subprocess.run(["sudo", "ldto", "enable", "i2c-ao"], check=True)
        print("Successfully enabled i2c-ao overlay.")
        
        # Enable I2C B overlay
        subprocess.run(["sudo", "ldto", "enable", "i2c-b"], check=True)
        print("Successfully enabled i2c-b overlay.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error enabling I2C overlays: {e}")

def main():
    # Enable I2C overlays
    enable_i2c_overlays()

    # Your main program logic here
    print("I2C setup complete. Starting main program...")

if __name__ == "__main__":
    main()
