#include <stdio.h>
#include <unistd.h>

// Function declarations from our wrapper library
extern "C" {
    int openSimucube(void* smHandle);
    void closeSimucube(long smHandle);
    int clearFaultsAndInitialize(long smHandle);
    int setSpeed(long smHandle, int speed);
    int getTorque(long smHandle, int* torque);
    int getFaults(long smHandle, int* faultStatus);
}

int main() {
    void* handle = nullptr;
    
    // Try to open Simucube
    printf("Opening Simucube...\n");
    if (openSimucube(&handle) != 0) {
        printf("Failed to open Simucube\n");
        return 1;
    }

    long smHandle = (long)handle;

    // Initialize and clear faults
    printf("Initializing motor...\n");
    if (clearFaultsAndInitialize(smHandle) != 0) {
        printf("Failed to initialize motor\n");
        closeSimucube(smHandle);
        return 1;
    }

    // Set a low speed and monitor torque
    printf("Setting motor speed to 500...\n");
    if (setSpeed(smHandle, 500) != 0) {
        printf("Failed to set speed\n");
        closeSimucube(smHandle);
        return 1;
    }

    // Monitor torque for 5 seconds
    printf("Monitoring torque for 5 seconds...\n");
    for (int i = 0; i < 5; i++) {
        int torque = 0;
        if (getTorque(smHandle, &torque) == 0) {
            printf("Current torque: %d\n", torque);
        }
        sleep(1);
    }

    // Stop motor
    printf("Stopping motor...\n");
    if (setSpeed(smHandle, 0) != 0) {
        printf("Failed to stop motor\n");
    }

    // Close connection
    closeSimucube(smHandle);
    printf("Test complete\n");

    return 0;
}