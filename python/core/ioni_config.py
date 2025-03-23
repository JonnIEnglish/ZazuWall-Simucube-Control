"""
IONI Configuration Module

This module handles the configuration and activation of the IONI motor controller.
It provides core functionality for enabling IONI configuration mode in the SimuCUBE system.
"""

import subprocess
import os
from pathlib import Path

class IoniConfigError(Exception):
    """Custom exception for IONI configuration errors."""
    pass

def get_configurator_path():
    """Get the path to the IONI configurator executable."""
    # Get the root directory of the project
    root_dir = Path(__file__).parent.parent.parent
    return root_dir / "src" / "enable_ioni_configurator"

def activate_ioni():
    """
    Activate IONI configuration mode.
    
    This function enables the configuration mode for the IONI motor controller
    by executing the enable_ioni_configurator binary.
    
    Returns:
        bool: True if activation was successful, False otherwise.
        
    Raises:
        IoniConfigError: If there's an error during activation.
    """
    try:
        configurator_path = get_configurator_path()
        if not configurator_path.exists():
            raise IoniConfigError(f"Configurator not found at {configurator_path}")
            
        result = subprocess.run(
            [str(configurator_path)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error activating IONI: {e.stderr}"
        print(error_msg)
        raise IoniConfigError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error during IONI activation: {str(e)}"
        print(error_msg)
        raise IoniConfigError(error_msg) from e

if __name__ == "__main__":
    try:
        activate_ioni()
    except IoniConfigError as e:
        print(f"Failed to activate IONI: {e}")
        exit(1)