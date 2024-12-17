# Simucube SimpleMotionV2 Examples

This folder contains two example projects that demonstrate how to interface with Simucube motor controllers. Both examples showcase different functionalities of the Simucube system using the Granite Devices SimpleMotion V2 library.

---

## Requirements and Setup

- **Powering the Simucube**: Ensure the Simucube is powered on with the DIP switches in their normal positions.
- **USB Connections**:
  - The **Simucube-Ioni-Activate** example requires a USB connection to the **X3 port**.
  - The **SimplemotionV2-Speed-Setpoint** example requires a USB connection to the **X4 port**.
  - Both USB connections can be made simultaneously.

---

## Projects

### 1. **Simucube-Ioni-Activate**
- **Description**:  
  This example puts the Simucube controller into **IONI configuration mode** via USB (connected to the X3 port). This is a required step to enable control of the motor drive using the SimpleMotion V2 library.

- **Key Features**:
  - Communicates with the Simucube controller using HIDAPI.
  - Configures the IONI drive for further operation.
  - Activates the Simucube controller for use with the SimpleMotion V2 library.

- **Usage**:
  1. Connect the Simucube to your computer via USB (X3 port).
  2. Compile the program using the provided `Makefile`.
  3. Run the binary (`./enable_ioni_configurator`) to put the Simucube into IONI configuration mode.

---

### 2. **SimplemotionV2-Speed-Setpoint**
- **Description**:  
  This example demonstrates how to control the velocity of a motor connected to the Simucube controller using the **SimpleMotion V2 library**. The program enables the motor, sets the control mode to velocity, and sends a speed setpoint.

- **Key Features**:
  - Reads and checks the Simucube for fault statuses.
  - Enables the motor drive.
  - Sets the control mode to velocity.
  - Sends a velocity setpoint (e.g., 500) to spin the motor.
  - Stops the motor and disables the drive after a short delay.

- **Usage**:
  1. Connect the Simucube to your computer via USB (X4 port).
  2. Compile the program using the provided `Makefile`.
  3. Run the binary (`./smv2_control_demo`) to control the motor.

---

## Dependencies

Both examples depend on the following:

- **[SimpleMotion V2 Library](https://granitedevices.com/wiki/SimpleMotion)**:  
  Developed by Granite Devices, this library is used for communication with the Simucube controller. Make sure the library headers and shared libraries are available in the project directories or system paths.
  
- **HIDAPI Library**:  
  Used in the **Simucube-Ioni-Activate** example for USB HID communication.

To set up these dependencies:
- Install HIDAPI (e.g., via Homebrew on macOS: `brew install hidapi`).
- Include the SimpleMotion V2 library in the project folder or ensure it is installed system-wide.

---

## Acknowledgments

These examples utilize the **SimpleMotion V2 library**, developed and maintained by **Granite Devices**. For more information, visit the [SimpleMotion Wiki](https://granitedevices.com/wiki/SimpleMotion).

---

## How to Build and Run

### Building:
1. Navigate to the respective project directory (`Simucube-Ioni-Activate` or `SimplemotionV2-Speed-Setpoint`).
2. Run `make` to compile the program.

### Running:
- For **Simucube-Ioni-Activate**, execute:  
  ```bash
  ./enable_ioni_configurator

