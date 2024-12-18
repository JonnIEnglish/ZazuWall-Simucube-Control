#include "../include/simucube_control.h"
#include "../lib/simplemotion.h"

void set_velocity_setpoint(const char* port_name, int velocity) {
    smbus handle = smOpenBus(port_name);
    if (handle == -1) {
        fprintf(stderr, "Failed to open port %s\n", port_name);
        return;
    }

    smSetParameter(handle, 1, SMP_CONTROL_MODE, CM_VELOCITY);
    smSetParameter(handle, 1, SMP_ABSOLUTE_SETPOINT, velocity);

    smCloseBus(handle);
}
