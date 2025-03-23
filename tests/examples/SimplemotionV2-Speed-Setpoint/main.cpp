#include <stdio.h>
#include <unistd.h>
#include <termios.h>
#include <fcntl.h>
#include "simplemotion.h"
#include "simplemotion_defs.h"
#include <dirent.h>
#include <string.h>

// Function to make stdin non-blocking
void makeStdinNonBlocking() {
    int flags = fcntl(STDIN_FILENO, F_GETFL);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);
}

// Function to check if a key was pressed
bool isKeyPressed() {
    char buf[1];
    return read(STDIN_FILENO, buf, 1) > 0;
}

// Function to perform emergency stop
void emergencyStop(smbus handle) {
    printf("\nEMERGENCY STOP TRIGGERED!\n");
    
    // Immediately set velocity to 0
    smSetParameter(handle, 1, SMP_ABSOLUTE_SETPOINT, 0);
    
    // Disable the drive
    smSetParameter(handle, 1, SMP_CONTROL_BITS1, 0);
    
    printf("Motor stopped and drive disabled.\n");
}

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

// Function to decode fault codes
void decodeFault(smint32 faultCode) {
    if (faultCode & 0x481001) {
        printf("Watchdog timeout detected (Communication error)\n");
    }
    // Add other fault code checks as needed
}

int main() {
    char ports[10][256]; // Array to store up to 10 serial port paths
    int portCount = 0;

    // Make stdin non-blocking for key detection
    makeStdinNonBlocking();
    printf("Press any key for emergency stop!\n");

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
        decodeFault(faultStatus);
        status = smSetParameter(handle, 1, SMP_CONTROL_BITS1, SMP_CB1_CLEARFAULTS);
        if (status == SM_OK) {
            printf("Faults cleared.\n");
        } else {
            fprintf(stderr, "Failed to clear faults.\n");
        }
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

    // Initial velocity setpoint is 0
    smint32 setpoint = 0;
    status = smSetParameter(handle, 1, SMP_ABSOLUTE_SETPOINT, setpoint);
    if (status != SM_OK) {
        fprintf(stderr, "Failed to send velocity setpoint.\n");
        smCloseBus(handle);
        return 1;
    }
    printf("Initial velocity setpoint of %d sent.\n", setpoint);

    // Run while checking for faults, refreshing watchdog, reading torque, and monitoring for keypress
    for (int i = 0; i < 5000; i++) { // 50 iterations of 100ms = 5 seconds
        usleep(100000);  // Sleep for 100ms between communications
        
        // Check for emergency stop
        if (isKeyPressed()) {
            emergencyStop(handle);
            smCloseBus(handle);
            return 0;
        }
        
        // Read torque
        smint32 torqueValue = 0;
        status = smRead1Parameter(handle, 1, SMP_ACTUAL_TORQUE, &torqueValue);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to read torque.\n");
        } else {
            printf("Current torque: %d\n", torqueValue);
            
            // Set speed based on torque value
            smint32 newSetpoint = (torqueValue < 10000) ? 2000 : 0;
            if (newSetpoint != setpoint) {
                setpoint = newSetpoint;
                status = smSetParameter(handle, 1, SMP_ABSOLUTE_SETPOINT, setpoint);
                if (status != SM_OK) {
                    fprintf(stderr, "Failed to update velocity setpoint.\n");
                } else {
                    printf("Updated velocity setpoint to %d based on torque\n", setpoint);
                }
            }
        }
        
        // Refresh watchdog by reading a parameter
        smint32 dummy;
        status = smRead1Parameter(handle, 1, SMP_FAULTS, &dummy);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to refresh watchdog.\n");
            smCloseBus(handle);
            return 1;
        }
        
        // Check for faults
        smint32 currentFaults = 0;
        status = smRead1Parameter(handle, 1, SMP_FAULTS, &currentFaults);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to read fault status during operation.\n");
            smCloseBus(handle);
            return 1;
        }
        
        if (currentFaults != 0) {
            printf("Fault detected during operation! Fault code: %d\n", currentFaults);
            decodeFault(currentFaults);
            emergencyStop(handle);
            smCloseBus(handle);
            return 1;
        }
        
        if (i % 10 == 0) { // Print status every second
            printf("Running... No faults detected (Second %d/5)\n", i/10 + 1);
        }
    }

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
