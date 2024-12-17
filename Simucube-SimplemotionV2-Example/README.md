# Simucube SimpleMotionV2 Examples

This folder contains two example projects demonstrating how to interface with Simucube motor controllers using the SimpleMotion V2 API. Each example highlights specific functionalities and control features of the Simucube system.

---

## Projects

### 1. **SimplemotionV2-Speed-Setpoint**
- **Description:**
  Demonstrates how to control the motor's velocity using the SimpleMotion V2 library. The program sets the control mode to velocity and sends a speed setpoint to spin the motor.

- **Key Features:**
  - Connects to the motor controller via SimpleMotion V2.
  - Reads and checks fault status.
  - Enables the motor drive.
  - Sets the control mode to velocity.
  - Sends a velocity setpoint (e.g., 500) and observes the motor spinning.
  - Stops the motor and disables the drive after a short delay.

- **Usage:**
  1. Compile the program using the provided `Makefile`.
  2. Execute the binary (`./smv2_control_demo`) to observe the motor behavior.

---

### 2. **Simucube-Ioni-Activate**
- **Description:**
  Demonstrates how to configure and enable the IONI drive on a Simucube controller using HIDAPI. This example shows how to communicate with the controller and activate the drive.

- **Key Features:**
  - Uses HIDAPI for USB communication.
  - Sends configuration commands to activate the IONI drive.
  - A starting point for further drive configuration tasks.

- **Usage:**
  1. Compile the program using the provided `Makefile`.
  2. Execute the binary (`./enable_ioni_configurator`) to activate the drive.

---

## Dependencies

Both examples depend on the following:
- **SimpleMotion V2 library**: Required for communication with the Simucube controller.
- **HIDAPI library** (Simucube-Ioni-Activate only): For USB HID communication.

Ensure that:
1. SimpleMotion V2 headers and shared libraries are available in the project directories or system paths.
2. HIDAPI is installed and accessible for Simucube-Ioni-Activate.

---

## How to Build and Run

1. **Compile**:
   - Navigate to the project directory (`SimplemotionV2-Speed-Setpoint` or `Simucube-Ioni-Activate`).
   - Run `make` to compile the program.

2. **Run**:
   - Execute the compiled binary (e.g., `./smv2_control_demo` or `./enable_ioni_configurator`).

---

## Notes
- These examples are designed for macOS but can be adapted to other platforms by adjusting the library paths in the `Makefile`.
- Ensure the Simucube controller and motors are correctly connected and configured before running the programs.

Feel free to explore, modify, and use these examples as a reference for your own Simucube-based projects!

---
