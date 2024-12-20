#include <stdio.h>
#include <unistd.h> // For sleep()
#include "simplemotion.h"
#include "simplemotion_defs.h"
#include <dirent.h> // For listing devices
#include <string.h> // For string comparisons

// Function to list serial ports
void listSerialPorts(char ports[][256], int *portCount) {
    struct dirent *entry;
    DIR *dir = opendir("/dev");

    if (dir == NULL) {
        perror("Failed to open /dev");
        return;
    }

    *portCount = 0; // Initialize port count

    while ((entry = readdir(dir)) != NULL) {
        if (strstr(entry->d_name, "ttyUSB") || strstr(entry->d_name, "ttyACM")) {
            snprintf(ports[*portCount], 256, "/dev/%s", entry->d_name);
            (*portCount)++;
        }
    }

    closedir(dir);
}

int main() {
    char ports[10][256]; // Array to store up to 10 serial port paths
    int portCount = 0;

    // List available serial ports
    listSerialPorts(ports, &portCount);

    if (portCount == 0) {
        printf("No serial ports found.\n");
        return 1;
    }

    printf("Available serial ports:\n");
    for (int i = 0; i < portCount; i++) {
        printf("%s\n", ports[i]);
    }

    // Try each port until one opens successfully
    smbus handle = -1;
    for (int i = 0; i < portCount; i++) {
        printf("Trying port: %s\n", ports[i]);
        handle = smOpenBus(ports[i]);
        if (handle != -1) {
            printf("SM bus opened successfully on %s\n", ports[i]);
            break;
        }
    }

    if (handle == -1) {
        fprintf(stderr, "Failed to open SM bus on any port.\n");
        return 1;
    }

    // Check for faults
    smint32 faultStatus = 0;
    SM_STATUS status = smRead1Parameter(handle, 1, SMP_FAULTS, &faultStatus);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to read fault status.\n");
        smCloseBus(handle);
        return 1;
    }

    if (faultStatus != 0) {
        printf("Device reports faults: %d\n", faultStatus);
        status = smSetParameter(handle, 1, SMP_CONTROL_BITS1, SMP_CB1_CLEARFAULTS);
        if (status == SM_OK) {
            printf("Faults cleared.\n");
        } else {
            fprintf(stderr, "Failed to clear faults.\n");
        }
    } else {
        printf("No faults reported.\n");
    }

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

    // Send a velocity setpoint
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
