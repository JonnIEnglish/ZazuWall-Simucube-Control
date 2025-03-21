#include <stdio.h>
#include <unistd.h>
#include <string.h>

// Basic HID definitions we need
#define GD_USB_VID 0x16d0    // Granite Devices VID
#define SIMUCUBE_PID 0x0d5a  // Simucube 1 PID
#define outReport 0x6B
#define enableSMUSB 9

// Function declarations from our wrapper library
extern "C" {
    int openSimucube(void* smHandle);
    void closeSimucube(long smHandle);
    int clearFaultsAndInitialize(long smHandle);
    int setSpeed(long smHandle, int speed);
    int getTorque(long smHandle, int* torque);
    int getFaults(long smHandle, int* faultStatus);
}

// Basic structures needed for HID communication
struct commandPacket {
    unsigned char reportID;
    unsigned char command;
    unsigned short value;
    unsigned short value2;
};

// Function declarations for HID API
extern "C" {
    struct hid_device_;
    typedef struct hid_device_ hid_device;
    int hid_init(void);
    hid_device* hid_open(unsigned short vendor_id, unsigned short product_id, const wchar_t* serial_number);
    void hid_close(hid_device* device);
    int hid_write(hid_device* device, const unsigned char* data, size_t length);
    void hid_exit(void);
    int hid_set_nonblocking(hid_device* device, int nonblock);
}

// Function to enable Ioni configuration
bool enableIoniConfiguration() {
    hid_device* simucubehandle = NULL;
    
    // Initialize HID API
    if (hid_init() != 0) {
        fprintf(stderr, "Failed to initialize HIDAPI.\n");
        return false;
    }

    // Open Simucube HID device
    simucubehandle = hid_open(GD_USB_VID, SIMUCUBE_PID, NULL);
    if (!simucubehandle) {
        fprintf(stderr, "Unable to open SimuCUBE device.\n");
        hid_exit();
        return false;
    }

    // Prepare command to enable SM USB configuration mode
    commandPacket commandData;
    unsigned char transmitbuf[60];
    memset(&commandData, 0, sizeof(commandData));
    memset(transmitbuf, 0, sizeof(transmitbuf));

    // Set command fields
    commandData.reportID = outReport;
    commandData.command = enableSMUSB;

    // Copy into the transmit buffer
    memcpy(transmitbuf, &commandData, sizeof(commandPacket));

    // Send command
    hid_set_nonblocking(simucubehandle, 1);
    if (hid_write(simucubehandle, transmitbuf, 60) == -1) {
        fprintf(stderr, "Failed to send enableSMUSB command.\n");
        hid_close(simucubehandle);
        hid_exit();
        return false;
    }

    printf("Ioni configuration enabled successfully.\n");
    
    // Clean up HID
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
    
    // Continue with original motor control code
    void* handle = nullptr;
    
    // Try to open Simucube
    printf("Opening Simucube...\n");
    if (openSimucube(&handle) != 0) {
        printf("Failed to open Simucube\n");
        return 1;
    }

    long smHandle = (long)handle;

    // Check initial fault status
    int faultStatus = 0;
    if (getFaults(smHandle, &faultStatus) == 0) {
        printf("Faults detected: %d. Attempting to clear...\n", faultStatus);
    } else {
        printf("Failed to read fault status\n");
        closeSimucube(smHandle);
        return 1;
    }

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