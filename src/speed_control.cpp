#include <stdio.h>
#include <stdlib.h>
#include "../lib/SimpleMotionV2/simplemotion.h"
#include "../lib/SimpleMotionV2/simplemotion_defs.h"

// Global handle to store the connection
static smbus bus_handle = -1;

extern "C" {

/**
 * Opens a connection to the IONI driver
 * 
 * @param port Serial port to connect to (e.g., "/dev/ttyUSB0")
 * @return 0 if successful, error code otherwise
 */
int open_connection(const char* port) {
    // Close any previously open connection
    if (bus_handle != -1) {
        smCloseBus(bus_handle);
        bus_handle = -1;
    }
    
    // Open the connection
    bus_handle = smOpenBus(port);
    if (bus_handle == -1) {
        fprintf(stderr, "Failed to open SM bus on %s\n", port);
        return 1;
    }
    
    printf("SM bus opened successfully on %s\n", port);
    
    // Set control mode to velocity
    SM_STATUS status = smSetParameter(bus_handle, 1, SMP_CONTROL_MODE, CM_VELOCITY);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to set velocity mode\n");
        smCloseBus(bus_handle);
        bus_handle = -1;
        return 2;
    }
    
    return 0;
}

/**
 * Checks for faults on the IONI driver
 * 
 * @return 0 if no faults, fault code otherwise
 */
int check_faults() {
    if (bus_handle == -1) {
        fprintf(stderr, "Not connected\n");
        return -1;
    }
    
    smint32 faultStatus = 0;
    SM_STATUS status = smRead1Parameter(bus_handle, 1, SMP_FAULTS, &faultStatus);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to read fault status\n");
        return -2;
    }
    
    return faultStatus;
}

/**
 * Clears faults on the IONI driver
 * 
 * @return 0 if successful, error code otherwise
 */
int clear_faults() {
    if (bus_handle == -1) {
        fprintf(stderr, "Not connected\n");
        return 1;
    }
    
    SM_STATUS status = smSetParameter(bus_handle, 1, SMP_CONTROL_BITS1, SMP_CB1_CLEARFAULTS);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to clear faults\n");
        return 2;
    }
    
    printf("Faults cleared\n");
    return 0;
}

/**
 * Sets the speed of the IONI driver
 * 
 * @param rpm Speed in RPM
 * @return 0 if successful, error code otherwise
 */
int set_speed(int rpm) {
    if (bus_handle == -1) {
        fprintf(stderr, "Not connected\n");
        return 1;
    }
    
    // Enable the drive
    SM_STATUS status = smSetParameter(bus_handle, 1, SMP_CONTROL_BITS1, SMP_CB1_ENABLE);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to enable the drive\n");
        return 2;
    }
    
    // Set the velocity setpoint
    status = smSetParameter(bus_handle, 1, SMP_ABSOLUTE_SETPOINT, rpm);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to set velocity setpoint\n");
        return 3;
    }
    
    printf("Velocity setpoint set to %d RPM\n", rpm);
    return 0;
}

/**
 * Closes the connection to the IONI driver
 */
void close_connection() {
    if (bus_handle != -1) {
        // Stop the motor first
        smSetParameter(bus_handle, 1, SMP_ABSOLUTE_SETPOINT, 0);
        
        // Disable the drive
        smSetParameter(bus_handle, 1, SMP_CONTROL_BITS1, 0);
        
        // Close the bus
        smCloseBus(bus_handle);
        bus_handle = -1;
        printf("Connection closed\n");
    }
}

} // extern "C"