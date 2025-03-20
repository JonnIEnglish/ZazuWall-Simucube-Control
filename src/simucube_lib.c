#include "simplemotion.h"
#include "simplemotion_defs.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h> // For listing devices

extern "C" {

    // List serial ports
    void listSerialPorts(char ports[][256], int *portCount) {
        struct dirent *entry;
        DIR *dir = opendir("/dev");
        if (dir == NULL) {
            perror("Failed to open /dev");
            return;
        }
        *portCount = 0;
        while ((entry = readdir(dir)) != NULL) {
            if (strstr(entry->d_name, "ttyUSB") || strstr(entry->d_name, "ttyACM")) {
                snprintf(ports[*portCount], 256, "/dev/%s", entry->d_name);
                (*portCount)++;
            }
        }
        closedir(dir);
    }

    // Open Simucube
    int openSimucube(smbus *smHandle) {
        char ports[10][256];
        int portCount = 0;
        listSerialPorts(ports, &portCount);
        if (portCount == 0) {
            fprintf(stderr, "No serial ports found.\n");
            return -1;
        }
        for (int i = 0; i < portCount; i++) {
            printf("Trying port: %s\n", ports[i]);
            *smHandle = smOpenBus(ports[i]);
            if (*smHandle != -1) {
                printf("SM bus opened successfully on %s\n", ports[i]);
                return 0;
            }
        }
        fprintf(stderr, "Failed to open SM bus on any port.\n");
        return -1;
    }

    // Close Simucube
    void closeSimucube(smbus smHandle) {
        smCloseBus(smHandle);
        printf("SM bus closed successfully.\n");
    }

    // Clear Faults and Enable Motor
    int clearFaultsAndInitialize(smbus smHandle) {
        smint32 faultStatus = 0;
        SM_STATUS status = smRead1Parameter(smHandle, 1, SMP_FAULTS, &faultStatus);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to read fault status.\n");
            return -1;
        }
        if (faultStatus != 0) {
            printf("Faults detected: %d. Attempting to clear...\n", faultStatus);
            status = smSetParameter(smHandle, 1, SMP_CONTROL_BITS1, SMP_CB1_CLEARFAULTS);
            if (status != SM_OK) {
                fprintf(stderr, "Failed to clear faults.\n");
                return -1;
            }
            printf("Faults cleared.\n");
        }
        status = smSetParameter(smHandle, 1, SMP_CONTROL_BITS1, SMP_CB1_ENABLE);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to enable the motor.\n");
            return -1;
        }
        printf("Motor enabled.\n");
        return 0;
    }

    // Set Speed
    int setSpeed(smbus smHandle, int speed) {
        SM_STATUS status = smSetParameter(smHandle, 1, SMP_ABSOLUTE_SETPOINT, speed);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to set speed to %d.\n", speed);
            return -1;
        }
        printf("Speed set to %d successfully.\n", speed);
        return 0;
    }

    // Get Torque
    int getTorque(smbus smHandle, int *torque) {
        smint32 torqueValue = 0;
        SM_STATUS status = smRead1Parameter(smHandle, 1, SMP_ACTUAL_TORQUE, &torqueValue);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to read torque.\n");
            return -1;
        }
        *torque = (int)torqueValue;
        printf("Torque read: %d\n", *torque);
        return 0;
    }

    // Get Faults
    int getFaults(smbus smHandle, int *faultStatus) {
        smint32 faults = 0;
        SM_STATUS status = smRead1Parameter(smHandle, 1, SMP_FAULTS, &faults);
        if (status != SM_OK) {
            fprintf(stderr, "Failed to read fault status.\n");
            return -1;
        }
        *faultStatus = (int)faults;
        printf("Faults read: %d\n", *faultStatus);
        return 0;
    }
}
