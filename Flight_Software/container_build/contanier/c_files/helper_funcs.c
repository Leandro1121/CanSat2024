#include "../h_files/helper_funcs.h"
#include "hardware/uart.h"



// Function to parse the input string
void parseGGAString(const char *input, gps *data) {
     int result = sscanf(input, "$GPGGA,%11[^,],%lf,%c,%lf,%c,%lf,%d,%d,", 
                    data->UTCTime,
                    &data->latitude, &data->nsIndicator,
                    &data->longitude, &data->ewIndicator,
                    &data->altitude, &data->positionFixIndicator, 
                    &data->satellitesUsed);

    
     if (result < 8) {
        data->latitude = 0;
        data->nsIndicator = 'N';  // Set to 'N' by default
        data->longitude = 0;
        data->ewIndicator = 'E';  // Set to 'E' by default
        data->altitude = 0;
        data->positionFixIndicator = 0;
        data->satellitesUsed = 0;
    }
    formatTimestamp(data->UTCTime);
}

void formatTimestamp(char *input) {
    int hh, mm, ss;
    double fractionalSeconds;
    
    sscanf(input, "%2d%2d%2d.%f", &hh, &mm, &ss, &fractionalSeconds);
    snprintf(input, 9, "%02d:%02d:%02d", hh, mm, ss);
}
