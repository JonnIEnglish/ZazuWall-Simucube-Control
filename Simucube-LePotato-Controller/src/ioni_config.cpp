#include <stdio.h>
#include <wchar.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "hidapi.h"
#include "config_comm_defines.h"

// Granite Devices VID and SimuCUBE PID
#define GD_USB_VID 0x16d0    // Granite Devices Vendor ID
#define SIMUCUBE_PID 0x0d5a  // SimuCUBE Product ID

hid_device* simucubehandle = NULL;

// Connect to the SimuCUBE device
bool connectSimuCube() {
    if (hid_init() != 0) {
        fprintf(stderr, "Failed to initialize HIDAPI.\n");
        return false;
    }

    simucubehandle = hid_open(GD_USB_VID, SIMUCUBE_PID, NULL);
    if (!simucubehandle) {
        fprintf(stderr, "Unable to open SimuCUBE device.\n");
        return false;
    }
    return true;
}

// Write data to the SimuCUBE device
bool writeSimucube(unsigned char *data, size_t length) {
    // Set non-blocking mode (optional)
    hid_set_nonblocking(simucubehandle, 1);
    if (hid_write(simucubehandle, data, length) == -1) {
        fprintf(stderr, "hid_write() failed: %ls\n", hid_error(simucubehandle));
        return false;
    }
    return true;
}

// Enable IONI Configuration Mode
bool enableIoniConfigMode() {
    printf("Attempting to connect to SimuCUBE...\n");

    if (!connectSimuCube()) {
        return false;
    }

    // Prepare command to enable IONI configuration mode
    commandPacket commandData;
    unsigned char transmitbuf[60];
    memset(&commandData, 0, sizeof(commandData));
    memset(transmitbuf, 0, sizeof(transmitbuf));

    // Set command fields
    commandData.reportID = outReport;  // Defined in config_comm_defines.h
    commandData.command = enableSMUSB; // The command to enable IONI configuration mode

    // Copy into the transmit buffer
    memcpy(transmitbuf, &commandData, sizeof(commandPacket));

    // Send command
    if (!writeSimucube(transmitbuf, sizeof(transmitbuf))) {
        fprintf(stderr, "Failed to send enableSMUSB command.\n");
        hid_close(simucubehandle);
        hid_exit();
        return false;
    }

    printf("IONI configuration mode enabled successfully.\n");

    // Clean up
    hid_close(simucubehandle);
    hid_exit();
    return true;
}
