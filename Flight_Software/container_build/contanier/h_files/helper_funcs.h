#ifndef HELPER_FUNCS_H
#define HELPER_FUNCS_H

#include <string.h>
#include <stdio.h>
#include "pico/stdlib.h"

#include <stdio.h>
#include <string.h>

// Define a struct to hold the parsed data
struct GGAData {
    char UTCTime[12];  // Add UTC time
    double latitude;
    char nsIndicator;
    double longitude;
    char ewIndicator;
    double altitude;
    uint8_t positionFixIndicator;
    uint8_t satellitesUsed;
    //char checksum[4];
};

typedef struct GGAData gps;

// Function to parse the input string
void parseGGAString(const char *input, gps *data);
void formatTimestamp( char *input);





#endif