#include "simucube_control.h"
#include <unistd.h> // for sleep()

int main() {
    const char* port_x3 = "/dev/cu.usbserial-X3"; // X3 USB port
    const char* port_x4 = "/dev/cu.usbserial-X4"; // X4 USB port

    // Enable IONI configuration mode on X3
    if (!enable_ioni_config_mode(port_x3)) {
        return 1;
    }

    // Main control loop
    while (true) {
        set_velocity_setpoint(port_x4, 500); // Set velocity to 500
        sleep(5);                            // Wait 5 seconds
        set_velocity_setpoint(port_x4, 0);   // Stop motor
        sleep(5);                            // Wait 5 seconds
    }

    return 0;
}
