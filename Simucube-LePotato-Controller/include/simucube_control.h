#ifndef SIMUCUBE_CONTROL_H
#define SIMUCUBE_CONTROL_H

#include "../lib/simplemotion.h"

// Function declarations
bool enable_ioni_config_mode(const char* port_name);
void set_velocity_setpoint(const char* port_name, int velocity);

#endif // SIMUCUBE_CONTROL_H
