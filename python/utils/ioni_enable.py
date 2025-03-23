import subprocess

def activate_ioni():
    """Activate IONI configuration mode."""
    import subprocess
    try:
        result = subprocess.run(
            ["/home/jonno/ZazuWall-Simucube-Control/tests/examples/Simucube-Ioni-Activate/enable_ioni_configurator"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error activating IONI: {e.stderr}")
        return False

if __name__ == "__main__":
    activate_ioni()
