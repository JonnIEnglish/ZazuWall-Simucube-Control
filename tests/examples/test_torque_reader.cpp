#include <stdio.h>
#include <unistd.h>
#include <cstring>
#include "simplemotion.h"
#include "simplemotion_defs.h"
#include <hidapi/hidapi.h>

#define GD_USB_VID 0x16d0    // Granite Devices VID
#define SIMUCUBE_PID 0x0d5a  // Simucube 1 PID
#define outReport 0x6B
#define enableSMUSB 9

// Function declarations from our wrapper library
extern "C" {
    int getTorqueRaw(long handle, int* torque);
}

// Basic structures needed for HID communication
struct commandPacket {
    unsigned char reportID;
    unsigned char command;
    unsigned short value;
    unsigned short value2;
};

// Function to enable Ioni configuration
bool enableIoniConfiguration() {
    hid_device* simucubehandle = NULL;
    
    if (hid_init() != 0) {
        fprintf(stderr, "Failed to initialize HIDAPI.\n");
        return false;
    }

    simucubehandle = hid_open(GD_USB_VID, SIMUCUBE_PID, NULL);
    if (!simucubehandle) {
        fprintf(stderr, "Unable to open SimuCUBE device.\n");
        hid_exit();
        return false;
    }

    commandPacket commandData;
    unsigned char transmitbuf[60];
    memset(&commandData, 0, sizeof(commandData));
    memset(transmitbuf, 0, sizeof(transmitbuf));

    commandData.reportID = outReport;
    commandData.command = enableSMUSB;

    memcpy(transmitbuf, &commandData, sizeof(commandPacket));

    hid_set_nonblocking(simucubehandle, 1);
    if (hid_write(simucubehandle, transmitbuf, 60) == -1) {
        fprintf(stderr, "Failed to send enableSMUSB command.\n");
        hid_close(simucubehandle);
        hid_exit();
        return false;
    }

    printf("Ioni configuration enabled successfully.\n");
    
    hid_close(simucubehandle);
    hid_exit();
    return true;
}

int main() {
    // Enable Ioni configuration first
    printf("Enabling Ioni configuration...\n");
    if (!enableIoniConfiguration()) {
        printf("Failed to enable Ioni configuration\n");
        return 1;
    }
    
    smbus handle;
    printf("Opening Simucube...\n");
    
    // Try to open the device on common serial ports
    const char* ports[] = {"/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1"};
    int numPorts = sizeof(ports) / sizeof(ports[0]);
    
    handle = -1;
    for (int i = 0; i < numPorts; i++) {
        printf("Trying port: %s\n", ports[i]);
        handle = smOpenBus(ports[i]);
        if (handle != -1) {
            printf("Successfully opened device on %s\n", ports[i]);
            break;
        }
    }
    
    if (handle == -1) {
        printf("Failed to open Simucube on any port\n");
        return 1;
    }

    // Monitor raw torque continuously for 10 seconds
    printf("\nMonitoring raw torque for 10 seconds...\n");
    printf("Press Ctrl+C to stop\n\n");
    
    for (int i = 0; i < 100; i++) { // 10 seconds with 100ms delay
        int rawTorque;
        if (getTorqueRaw(handle, &rawTorque) == 0) {
            printf("Raw torque value: %d\r", rawTorque);
            fflush(stdout);  // Make sure the output is displayed immediately
        } else {
            printf("Failed to read raw torque\n");
        }
        usleep(100000);  // 100ms delay
    }
    
    printf("\nTest complete\n");
    smCloseBus(handle);
    return 0;
}