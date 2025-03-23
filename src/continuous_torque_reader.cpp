#include <stdio.h>
#include "simplemotion.h"
#include "simplemotion_defs.h"

extern "C" {
    int getTorqueRaw(long handle, int* torque) {
        smint32 torqueValue = 0;
        SM_STATUS status = smRead1Parameter(handle, 1, SMP_ACTUAL_TORQUE, &torqueValue);
        if (status != SM_OK) {
            return -1;
        }
        *torque = torqueValue;
        return 0;
    }

    float convertRawToNm(long handle, int rawTorque) {
        // Convert from counts to Amps (560 counts per Amp as seen in the codebase)
        float torqueInAmps = rawTorque / 560.0f;
        
        // Get the motor's torque constant
        smint32 torqueConstantRaw = 0;
        SM_STATUS status = smRead1Parameter(handle, 1, SMP_MOTOR_TORQUE_OR_FORCE_CONSTANT, &torqueConstantRaw);
        float torqueConstant = (status == SM_OK) ? (torqueConstantRaw / 10000.0f) : 1.0f;
        
        return torqueInAmps * torqueConstant;
    }

    int getTorqueNm(long handle, float* torqueNm) {
        int rawTorque;
        int result = getTorqueRaw(handle, &rawTorque);
        if (result != 0) {
            return result;
        }
        *torqueNm = convertRawToNm(handle, rawTorque);
        return 0;
    }
}