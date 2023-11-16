#ifndef HELPER_FUNCS_H
#define HELPER_FUNCS_H

#include <stdio.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    const char* command;
    uint8_t lastTwoValues[2];
} CommandPair;

CommandPair commandList[] = {
    {"Team_ID", {0, 1}},
    {"MISSION_TIME", {0, 2}},
    {"PACKET_COUNT", {0, 3}},
    {"MODE", {0, 4}},
    {"STATE", {0, 5}},
    {"ALTITUDE,", {0, 6}},
    {"AIR_SPEED", {0, 7}},
    {"HS_DEPLOYED", {0, 8}},
    {"PC_DEPLOYED", {0, 9}},
    {"TEMPERATURE", {0, 10}},
    {"PRESSURE", {0, 11}},
    {"VOLTAGE", {0, 12}},
    {"GPS_TIME", {0, 13}},
    {"GPS_ALTITUDE", {0, 14}},
    {"GPS_LATITUDE", {0, 15}},
    {"GPS_LONGITUDE", {0, 16}},
    {"GPS_SATS", {0, 17}},
    {"TILT_X", {0, 18}},
    {"TILT_Y", {0, 19}},
    {"ROT_Z", {0, 20}},
    {"CMD_ECHO", {0, 21}}
};

void updateLastTwoValues(uint8_t result, uint8_t* lastTwoValues) {
    lastTwoValues[1] = lastTwoValues[0];
    lastTwoValues[0] = result;
}

uint8_t parseAndExecuteCommands(const char* commandString, CommandPair* commands, size_t numCommands) {
    for (size_t i = 0; i < numCommands; i++) {
        if (strcmp(commandString, commands[i].command) == 0) {
            // Execute the corresponding command and update the last two values
            uint8_t result = commands[i].lastTwoValues[0];
            updateLastTwoValues(result, commands[i].lastTwoValues);
            return result;
        }
    }

    // Handle unknown commands or errors
    return 0;
}

int main() {
    const char* inputCommand = commandList; // Replace with your input string
    size_t numCommands = sizeof(commandList) / sizeof(commandList[0]);
    uint8_t result = parseAndExecuteCommands(inputCommand, commandList, numCommands);

    printf("Last Two Values for %s: %u, %u\n", inputCommand, commandList[result - 1].lastTwoValues[0], commandList[result - 1].lastTwoValues[1]);

    return 0;
}

#endif