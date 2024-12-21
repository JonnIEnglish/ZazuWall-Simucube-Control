import subprocess

def activate_ioni():
    try:
        # Call the binary
        result = subprocess.run(
            ["/home/jonno/ZazuWall-Simucube-Control/le-Potato-Control/enable_ioni_configurator"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Output from IONI activation:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error activating IONI:")
        print(e.stderr)

if __name__ == "__main__":
    activate_ioni()
