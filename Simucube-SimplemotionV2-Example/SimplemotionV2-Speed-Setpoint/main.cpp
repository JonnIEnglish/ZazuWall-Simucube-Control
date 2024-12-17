#include <stdio.h>
#include <unistd.h> // For sleep()
#include "simplemotion.h"
#include "simplemotion_defs.h"

int main() {
    const char* portname = "/dev/cu.usbserial-D30A763D";
    smbus handle = smOpenBus(portname);
    if (handle == -1) {
        fprintf(stderr, "Failed to open SM bus on %s\n", portname);
        return 1;
    }
    printf("SM bus opened successfully on %s\n", portname);

    // Check for faults
    smint32 faultStatus = 0;
    SM_STATUS status = smRead1Parameter(handle, 1, SMP_FAULTS, &faultStatus);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to read fault status.\n");
        smCloseBus(handle);
        return 1;
    }
    if (faultStatus != 0) {
        fprintf(stderr, "Device reports faults: %d\n", faultStatus);

        // Attempt to clear faults
        status = smSetParameter(handle, 1, SMP_CONTROL_BITS1, SMP_CB1_CLEARFAULTS);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to clear faults.\n");
            smCloseBus(handle);
            return 1;
        }
        printf("Faults cleared.\n");

        // Check faults again
        status = smRead1Parameter(handle, 1, SMP_FAULTS, &faultStatus);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to read fault status after clearing.\n");
            smCloseBus(handle);
            return 1;
        }
        if (faultStatus != 0) {
            fprintf(stderr, "Device still reports faults: %d\n", faultStatus);
            smCloseBus(handle);
            return 1;
        }
    }
    printf("No faults reported.\n");

    // Enable the drive
    status = smSetParameter(handle, 1, SMP_CONTROL_BITS1, SMP_CB1_ENABLE);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to enable the drive.\n");
        smCloseBus(handle);
        return 1;
    }
    printf("Drive enabled.\n");

    // Set control mode to velocity
    status = smSetParameter(handle, 1, SMP_CONTROL_MODE, CM_VELOCITY);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to set velocity mode.\n");
        smCloseBus(handle);
        return 1;
    }
    printf("Control mode set to velocity.\n");

    // Send setpoint of 500
    smint32 setpoint = 500; // Adjust based on your configuration
    status = smSetParameter(handle, 1, SMP_ABSOLUTE_SETPOINT, setpoint);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to send velocity setpoint.\n");
        smCloseBus(handle);
        return 1;
    }
    printf("Velocity setpoint of %d sent. Motor should be turning now...\n", setpoint);

    // Wait for a while to observe the motor turning
    sleep(5);

    // Stop the motor
    status = smSetParameter(handle, 1, SMP_ABSOLUTE_SETPOINT, 0);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to stop the motor.\n");
    } else {
        printf("Motor stopped.\n");
    }

    // Disable the drive
    status = smSetParameter(handle, 1, SMP_CONTROL_BITS1, 0);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to disable the drive.\n");
    } else {
        printf("Drive disabled.\n");
    }

    smCloseBus(handle);
    return 0;
}
