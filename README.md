# ZazuWall-Simucube-Control

Control system for ZazuWall using Simucube motor controllers.

## Project Structure

```
├── src/        # C source files for Simucube control
├── lib/        # External libraries (SimpleMotionV2)
├── python/     # Python package
│   ├── core/   # Main application code
│   ├── utils/  # Utility functions and helpers
│   └── tests/  # Unit tests
├── tests/      # Integration tests and examples
│   └── examples/
└── build/      # Compiled binaries
```

## Prerequisites

- Python 3.6 or higher
- GCC compiler for C code
- I2C and GPIO enabled on your system
- SimpleMotionV2 library
- HIDAPI library

## Installation

1. Install system dependencies:
   ```bash
   sudo apt-get install gcc build-essential python3-dev
   ```

2. Install Python package in development mode:
   ```bash
   pip install -e .
   ```

## Usage

The package provides two main commands:

1. Standard motor control with LCD interface:
   ```bash
   zazuwall
   ```

2. Torque-based motor control:
   ```bash
   zazuwall-torque
   ```

## Development

- Use `python -m pytest python/tests/` to run tests
- Source code is formatted according to PEP 8
- C code follows Linux kernel coding style

## License

Apache License 2.0 - See LICENSE file for details