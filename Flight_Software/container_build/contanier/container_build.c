#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/spi.h"
#include "hardware/timer.h"
#include "hardware/irq.h"
#include "hardware/adc.h"
#include "strings.h"
#include <string.h>
#include "math.h"
#include "pico/multicore.h"
// Main sensor libraries
#include "h_files/bmp280_i2c.h"
#include "h_files/bno055.h" 
#include "h_files/power_status.h"
#include "h_files/helper_funcs.h"
#include "h_files/AdafruitPMTK.h"

//TEAM INFO 
#define TEAM_ID 1071 //TODO Change this to actuall team id

// General UART Settings 
#define BAUD_RATE 9600
#define DATA_BITS 8
#define STOP_BITS 1
#define PARITY    UART_PARITY_NONE

// Defines related to Xbee communication through UART
#define UART_TX_PIN_XBEE 8
#define UART_RX_PIN_XBEE 9
#define UART_ID_XBEE uart1

// Defines related to Xbee communication through UART
#define UART_TX_PIN_GPS 0
#define UART_RX_PIN_GPS 1
#define UART_ID_GPS uart0

// Trigger Pins Numbers
#define BCN_PIN 5 // Change later
#define CAM_TRIGGER 6

// Altitude Calculations variables
#define GRAVITY_CONSTANT 9.80665  // Standard gravity constant in m/s^2
#define MOLAR_MASS_AIR 0.0289644  // Molar mass of dry air in kg/mol
#define UNIVERSAL_GAS_CONSTANT 8.31447  // Universal gas constant in J/(mol·K)
#define SEA_LEVEL_STANDARD_TEMPERATURE 288.15  // Standard sea level temperature in K
#define SEA_LEVEL_STANDARD_PRESSURE 101325.0  // Standard sea level pressure in Pa

// Variables that exist througout 
volatile bool new_TX = true;
volatile uint32_t mission_time = 0; 

// Interrupt to set transmssion at 1Hz
int64_t  alarm_callback(alarm_id_t id, void *user_data)
{
    // Set new transmission flag to true
    new_TX = true;
    return 0;
}
// Internal Mission Time Keeper
bool repeating_timer_callback(struct repeating_timer *t) {
    mission_time ++; 
    return true;
}
void xbee_uart_rx(char* command_string){
    //Collecting all incoming data from uart
    uint8_t i = 0; 
    while (uart_is_readable(UART_ID_XBEE)) {
        // While there is something in the UART system, Add it to array of characters
        command_string[i] = uart_getc(UART_ID_XBEE);
        // Increment place holder.
        i ++; 
    } 
    
 
}
void setup_xbee_coms(){
    // Set up our UART with a basic baud rate.
    uart_init(UART_ID_XBEE, BAUD_RATE);

    // Set the TX and RX pins by using the function select on the GPIO
    // Set datasheet for more information on function select
    gpio_set_function(UART_TX_PIN_XBEE, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN_XBEE, GPIO_FUNC_UART);

    // Set UART flow control CTS/RTS, we don't want these, so turn them off
    uart_set_hw_flow(UART_ID_XBEE, false, false);

    // Set our data format
    uart_set_format(UART_ID_XBEE, DATA_BITS, STOP_BITS, PARITY);

    // Turn off FIFO's - we want to do this character by character
    uart_set_fifo_enabled(UART_ID_XBEE, false);

}
void uart_Rx_handler_gps(char *gps_info){
    // Initialize a counter variables
    int j,i = 0;
    // If the uart is ready to read
    if (uart_is_readable(UART_ID_GPS)) {
        // This never actually returns to false becuase 
        //there is always data 
        char c = uart_getc(UART_ID_GPS);
        // We don't save the start character $
        while (!uart_is_readable(UART_ID_GPS)) {
            // Save new charcter in c for checking
            c = uart_getc(UART_ID_GPS);
            gps_info[i++] = c;
            // We want to keep track of how many lines we have
            if (c == '\n') j++;
            // Once we have two lines, we have a full packet; 
            if (j == 1) break; // ! This controls how many lines of NMEA info
        }
    }  
}
void setup_gps_coms(){
    // Set up our UART with a basic baud rate.
    uart_init(UART_ID_GPS, BAUD_RATE);

    // Set the TX and RX pins by using the function select on the GPIO
    // Set datasheet for more information on function select
    gpio_set_function(UART_TX_PIN_GPS, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN_GPS, GPIO_FUNC_UART);

    // Set UART flow control CTS/RTS, we don't want these, so turn them off
    uart_set_hw_flow(UART_ID_GPS, false, false);

    // Set our data format
    uart_set_format(UART_ID_GPS, DATA_BITS, STOP_BITS, PARITY);

    // Turn off FIFO's - we want to do this character by character
    uart_set_fifo_enabled(UART_ID_GPS, false);

    //Send a command so we only receive RMC and CGA NEMA Sentences
    // ! Remember if you want to use another command add "\r\n"
    uart_puts(UART_ID_GPS, PMTK_SET_NMEA_OUTPUT_GGAONLY); 
}
double press_to_alt_bar(double pressure) {
    return ((SEA_LEVEL_STANDARD_TEMPERATURE / GRAVITY_CONSTANT) * log(SEA_LEVEL_STANDARD_PRESSURE / pressure));
}

void setup_bmp280(){

}
void setup_bno055(){

}
void setup_powersource(){  

}
// void setup_spi_gps(){
// // Initialize the SPI bus
//     spi_init(SPI_CORE0_BUS, BAUD_RATE);
//     gpio_set_function(SPI_CORE0_MISO, GPIO_FUNC_SPI);
//     gpio_set_function(SPI_CORE0_MOSI, GPIO_FUNC_SPI);
//     gpio_set_function(SPI_CORE0_SCK, GPIO_FUNC_SPI);

//     // Set up SPI configuration
//     spi_set_format(SPI_CORE0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
// }

// void core1_interrupt_handler(){
//     while(multicore_fifo_rvalid()){

//     }
//    multicore_fifo_clear_irq();

// }
// void core1_entry(){
//     multicore_fifo_clear_irq();
//     irq_set_exclusive_handler(SIO_IRQ_PROC1, core1_interrupt_handler);
//     irq_set_enabled(SIO_IRQ_PROC1, true);

//     while(1){
//         tight_loop_contents();
//     }
// }


void command_parse(uint8_t *command, int16_t *value2, char  *commamnd_string) { 
    // int team_id;
    // char comm[10];

    // // TODO Add TX variable you will be parseing 
    // // TODO Parse function in here Use command_string its volatile
    // sscanf(command_string, "CMD,%d,%s,%d", &team_id, comm, *value2 );

    // if (team_id == TEAM_ID){
    //     if (strcmp(comm,"SIMP")== 0) *command = 3;
    //     else if (strcmp(comm,"CX")== 0) *command = 0;
    //     else if (strcmp(comm,"BCN")== 0) *command = 5;
    //     else if (strcmp(comm,"ST")== 0) *command = 1;
    //     else if (strcmp(comm,"CAL")== 0) *command = 4;
    //     else if (strcmp(comm,"SIM")== 0) *command = 2;
    //     else *command = 7; //Default Case does nothing
    // }
    

}


int main (int argc, char **argv)
{
    stdio_init_all();

    // Setup Pin output for Audio Beacon
    gpio_init(BCN_PIN);
    gpio_set_dir(BCN_PIN, GPIO_OUT);

    // Setup Trigger Pin for Camera
    gpio_init(CAM_TRIGGER);
    gpio_set_dir(CAM_TRIGGER, GPIO_OUT);

    // Setup Xbee coms
    setup_xbee_coms(); 

    // Setup GPS Communication
    setup_gps_coms();


    uint8_t command = 0; //TODO Change back to 0 at the end
    int16_t value = 0; 

    // ! Functional Variable 
    bool CX_ON = false; //TODO Change
    bool BCN_ON = false;
    bool BCN_CHANGE = false; 
    bool SIM_ENABLE = false;
    bool SIM_ACTIVATE = false;
    bool SIMP_FLAG = false;

    double curr_press = 0.0; 
    double curr_alt = 0.0;
    double prev_alt = 0.0;
    uint16_t packet_count = 0; 
    char CMD_ECHO[10] = ""; 

    // ! Packet Variables
    // Flight States to be used in payload
    const char FLIGHT_STATES[7][20] = 
        {"LAUNCH_WAIT",     // * Waiting to be launched
         "ASCENT",          // * Directly after launch befor ~700 meters
         "ROCKET_DEPLOYED", // * Rocket Seperation Charge, Aero-brake deployed
         "INIT_DECENT",     // * Initial Decent -> 100 meters (@10-30 m/s)
         "HS_DEPLOYED",     // * Deploy heat shield & parahcute 
         "FINAL_DECENT",    // * Final Decent -> 0 m (@ 5m/s)
         "LANDED"           // * Landed, shut off communications
        };

    // Used to keep track of current states 
    uint8_t current_state = 0; 
    // Used to keep track of Flight mode 
    bool current_mode = true;
    // Used to keep track of heat shield deployment
    bool current_hs  = false; 
    // Used to keep track of heat shield deployment
    bool current_pc  = false; 

    // This will be the internal Mission Time Keeper, the current count will be 
    // offset given by the GCS. The IRQ is triggered every 1 second,
    // Should give the Payload enough time to function. 
    struct repeating_timer timer;
    add_repeating_timer_ms(1000, repeating_timer_callback, NULL, &timer);

    //Core 1 Thread Initialize 
    //multicore_launch_core1(core1_entry);

    while (1) {
        tight_loop_contents();

        // Send and receive data through UART (in a real application)
        if (uart_is_readable(UART_ID_XBEE)){

            char command_string[20];

            xbee_uart_rx(command_string);
           
            //Call the function and pass addresses of variables to store the values and parse TX
            //command_parse(&command,&value);

            //Switch statement for behavior of incoming transmission
            switch(command){
                // TODO Modify CMD_ECHO in UARt there
                case 0: // CX ON/OFF - Payload should turn on/off
                    if (value == 1) CX_ON = true;
                        // CX ON - Payload should turn on    
                    else if (value == 0)  CX_ON = false;
                        // CX OFF - Payload should turn off     
                    // gpio_put(CAM_TRIGGER, CX_ON); // TODO Use this statement to trigger camera on CX_on
                break; 

                case 1: // ST UTC/GPS - Set payload time to GS UTC/GPS time
                    if (value == -1){
                       // TODO  ST GPS - Set payload time to GPS time
                       // mission_time = gps_get_time func
                       
                    }
                    else{
                        // TODO ST UTC - Set payload time to GS UTC time -> value
                        //mission_time = value -> time generated from value
                    }
                    
                break;

                case 2: // SIM command - All sim commands go here
                    if (value == 2) SIM_ACTIVATE = true;
                        // SIM ACTIVATE - Set sim_activate to true
                    else if (value == 1) SIM_ENABLE = true;
                       // SIM ENABLE - Set sim_enable to true   
                    else SIM_ACTIVATE = false, SIM_ENABLE = false; 
                        // SIM DISABLE - Set bot sim_activate & enable to false   
                break;

                case 3: //SIMP pressure# - Set internal pressure value to #
                    // pressure used for calcultaion are equal to value
                    curr_press = value;
                    SIMP_FLAG = true; 
                break;

                 case 4: //CAL- Set current altitiude to 0
                    // TODO pressure = current pressure MAYBE??
                break;

                case 5: // BCN ON/OFF - Audio beacon on and off
                     if (value == 1) BCN_ON = true;
                        // BCN ON - Audio beacon on 
                    else BCN_ON = false; 
                        //  BCN OFF - Audio beacon off
                    BCN_CHANGE = true; // Make a BCN flag variable
                break;

                default:
                break;
            }

        }
        else { //*  This part of the Flight Software is invoked when there is no new transmission

            // ! If there is a change in BCN_ON,
            if (BCN_CHANGE){  
                // Then make the pin output to the value of BCN_ON
                gpio_put(BCN_PIN, BCN_ON);  
                // Change flag
                BCN_CHANGE = false; 
            }

            // ! This statement will stop the loop from continuing 
            if (CX_ON == false) continue;  

            // ! If in simulation mode
            if (SIM_ACTIVATE & SIM_ENABLE){ 
                // altitude calculation based on value
                //if SIMP_FLAG has been changed or true(there was a value loaded to curr_pressure)
                if (SIMP_FLAG == false) continue; 
                //Value should be assinged by this point (curr_pressure = value)
                else SIMP_FLAG = false;   
            }
            else{
              
                //TODO curr_press = pressure sensor value
            }
            // Regardless of Mode, altitude will be calculated from curr_pressure
            curr_alt = press_to_alt_bar(curr_press);

            // Add current altitude and state num to FIFO core1 for behavior 

            // ! If 1 second has passed, or in SIM Mode, create packet
            if ( uart_is_writable(UART_ID_XBEE) & (new_TX || (SIM_ACTIVATE & SIM_ENABLE))){
                //Reset Transmission Flag
                new_TX = false; 

                // Packet container with 70 character, might need more if necessary
                char packetTX[100];
                char buffer[20];

                // Container for GPS data
                char gps_data[120];

                //Get Data from GPS 
                uart_Rx_handler_gps(gps_data);

                //Parse GPS String and put it in a container
                //struct GGAData data;
                //parseGGAString(gps_info, &data);

                // * Team ID
                    // Convert the integer to a string
                    sprintf(packetTX, "%d", TEAM_ID);
                    strcat(packetTX,",");
                    
                // * Mission Time in UTC no ms
                    // TODO Write some function that will convert time in uint32_t into HH:MM:SS and put it into buffer
                    strcat(packetTX, buffer);
                    strcat(packetTX,",");

                // * Packet Count of the Payload 
                    // Packet count is incremented
                    packet_count ++; 
                    sprintf(buffer, "%d", packet_count); 
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Flight Mode -> F or S
                    if (current_mode) strcat(packetTX,"F,");
                        else strcat(packetTX,"S,");

                // * Flight State -> ex. LAUNCH_WAIT
                    // ! By the time you get here current_state num should be on FIFO back
                    strcat(packetTX,FLIGHT_STATES[current_state]);
                    strcat(packetTX,",");

                // * Altitude in 0.1 meters
                    //sprintf(buffer, "%.1f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * AIR_SPEED
                    //sprintf(buffer, "%.1f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Heat Shield Deployed P(deployed) N(Otherwise)
                    if (current_hs) strcat(packetTX,"P,");
                        else strcat(packetTX,"N,");

                // * Parachute Deployed C (deployed @100 m) and N(otherwise)
                    if (current_pc) strcat(packetTX,"C,");
                        else strcat(packetTX,"N,");

                // * Temperature using 0.1 degrees Celcius 
                    sprintf(buffer, "%d", 0);    // TODO Change "floatvalue" to function that generates item
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Pressure in 0.1 kPa
                    //sprintf(buffer, "%.1f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Voltage in 0.1 V
                    //sprintf(buffer, "%.1f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * GPS Time in UTC with a resolutions of one second
                    //strcat(packetTX, data.UTCTime);
                    strcat(packetTX,",");

                // * GPS Altitude in 0.1 m
                   // sprintf(buffer, "%.1f", data.altitude);
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * GPS Latitude in decimal degrees with 0.0001 degrees North Resolution
                    //sprintf(buffer, "%.4f", data.latitude);
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * GPS Longitude in decimal degress with 0.0001 degrees West resolution
                    //sprintf(buffer, "%.4f", data.longitude);
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");
                
                 // * GPS SATS, the amount of satellites the GPS is using
                    //sprintf(buffer, "%d", data.satellitesUsed);    
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Tilt X/Y direction 0.01 degree resolution. 0 = X/Y perpendicular to Z axis -> center of Earth
                    //sprintf(buffer, "%.2f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    //strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Rotation rate in degrees/sec with 0.1 deg/sec resolution
                    //sprintf(buffer, "%.1f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    //strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Last Command read
                    strcat(packetTX,CMD_ECHO);
                    strcat(packetTX,"\n"); 

                //Write packet string into UART => XBEE
               
                //uart_puts(UART_ID_XBEE, packetTX);
                // TODO Remove when done testing 
                //uart_puts(UART_ID_XBEE, gps_info);

                //Create a timmer that will trigger an IRQ after 1 second => 1Hz
                add_alarm_in_ms(1000, alarm_callback, NULL, false);
            }
        
            prev_alt = curr_alt; 
        }
    }
   
    return 0;
}
