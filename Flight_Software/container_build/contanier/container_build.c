#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/spi.h"
#include "hardware/i2c.h"
#include "hardware/timer.h"
#include "hardware/irq.h"
#include "hardware/adc.h"
#include "strings.h"
#include <string.h>
#include "math.h"
#include "pico/multicore.h"
// Main sensor libraries
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

//defined I2C struture within PICO
#define I2C_MPL3115A2_ID i2c0 //MPL3115A2 is i2c block 0
#define I2C_BNO055_ID i2c0 //BNO055 is i2c block 1, defined within pico and the provided I2C structure

#define I2C_BAUD_RATE 100000 //same as uart for now, can be adjusted

//Unique addresses of each component, slave address for communication
#define I2C_MPL3115A2_ADDR 0x60
#define I2C_BNO055_ADDR 0x28

// Trigger Pins Numbers
#define BCN_PIN 13 // Change later
#define CAM_TRIGGER 12

// Altitude Calculations variables
#define GRAVITY_CONSTANT 9.80665  // Standard gravity constant in m/s^2
#define MOLAR_MASS_AIR 0.0289644  // Molar mass of dry air in kg/mol
#define UNIVERSAL_GAS_CONSTANT 8.31447  // Universal gas constant in J/(mol·K)
#define SEA_LEVEL_STANDARD_TEMPERATURE 288.15  // Standard sea level temperature in K
#define SEA_LEVEL_STANDARD_PRESSURE 101325.0  // Standard sea level pressure in Pa

// Pin for ADC to measure voltage through a voltage divider to protect
#define ADC_Voltage 26
#define current_divider_val 0.6667

// Pinout for SPI system in SD card reader 
#define SD_CS 5
#define SD

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

// ! XBEE Functions 
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
uint8_t xbee_uart_rx(char (*command_container)[10] ){
    //Collecting all incoming data from uart
    uint8_t i,j = 0;
    while (1) {
        // While there is something in the UART system, Add it to array of characters
        char c = uart_getc(UART_ID_XBEE);
        if (c == ','){
            i++;
            j = 0;
        } 
        else if (c == '\n') break; 
        else  command_container[i][j++] = c;
    }

    if (strcmp(command_container[2], "SIMP") == 0) return 3;
    else if (strcmp(command_container[2], "CX") == 0) return 0;
    else if (strcmp(command_container[2], "ST") == 0) return 1;
    else if (strcmp(command_container[2], "SIM") == 0) return 2;
    else if (strcmp(command_container[2], "CAL") == 0) return 4;
    else if (strcmp(command_container[2], "BCN") == 0) return 5;
    else return 8;

}

// ! GPS Functions
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
bool uart_Rx_handler_gps(char (*gps_info)[12]){
    // ! Good for only one sentence
    bool fix = true; 
    // Initialize a counter variables
    uint8_t j,i = 0;
    // If the uart is ready to read
    if (uart_is_readable(UART_ID_GPS)) {
        // This never actually returns to false becuase 
        //there is always data 
        char c = uart_getc(UART_ID_GPS);
        // We don't save the start character $
        while (i < 17) {
            // Save new charcter in c for checking
            c = uart_getc(UART_ID_GPS);
            if (c == ','){
                i++;
                j = 0;
            } 
            else if (c == '\n') break; 
            else  gps_info[i][j++] = c;
        }
    } 
    // Check if there is some kind of fix
    if (strcmp(gps_info[7], "0") == 0) fix = false ; 
    // TODO Write a function for check sum

    return fix;

    //Check if there is a fix 
}

// ! Altitude Conversion Formula
double press_to_alt_bar(double pressure) {
    return ((SEA_LEVEL_STANDARD_TEMPERATURE / GRAVITY_CONSTANT) * log(SEA_LEVEL_STANDARD_PRESSURE / pressure));
}

// ! MPL3115A2 Functions
bool setup_MPL3115A2(){
    // ! Call BNO055 first to set up I2C functionality
    //Check to see if device is connected properly 

    uint8_t reg = 0x0C;
    uint8_t chipID[1];
    i2c_write_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, &reg, 1, true);
    i2c_read_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, chipID, 1, false);

    //uart_putc(UART_ID_XBEE, chipID[0]+65);
    //sleep_ms(50000);

    if (chipID[0] != 0xC4) return false; 

    //Enable the Baramoter 
    uint8_t data[2] = {0x26, 0x38};
    i2c_write_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, data, 2, true);

    // Enable Data Flags
    data[0] = 0x13;
    data[1] = 0x07;
    i2c_write_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, data, 2, true);
    sleep_ms(1);

    // Activate
    data[0] = 0x26;
    data[1] = 0x39;
    i2c_write_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, data, 2, true);
    sleep_ms(1);
    
    return true;
}
void MPL3115A2_collect_data(double *data){

    // Regester where data starts
    uint8_t reg_val = 0x01;
    // Container to hold data
    uint8_t data_read [5];
    // Full size of pressure value is 20 bits -> MSB | LSB | DECIMAL Portion
    uint32_t pressure;
    // Full size of pressure value is 12 bits -> MSB | DECIMAL Portion
    int16_t temp;
    double f_pressure, f_temp; 
  
    i2c_write_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, &reg_val, 1, true);
    i2c_read_blocking(I2C_MPL3115A2_ID, I2C_MPL3115A2_ADDR, data_read, 5, false);

    //Fixed floating point numbers
    pressure = ((data_read[0]<< 16)| data_read[1]<<8 | data_read[2]);
    temp = ((data_read[3] << 8 | data_read[4])) ;

    f_pressure = pressure;
    f_temp = temp;

    data[0] = f_pressure/64; // ! Pa -> kPA
    data[1] = f_temp/256;

}
void MPL3115A2_calibrate(){
    // Use this function to calibrate for air pressure
    // TODO 
}

// !BNO055 Functions
bool setup_bno055(){

    i2c_init(I2C_BNO055_ID, I2C_BAUD_RATE);

    //Set SDA and SCL pins to provided GPIO pins
    gpio_set_function(PICO_DEFAULT_I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(PICO_DEFAULT_I2C_SCL_PIN, GPIO_FUNC_I2C);

    //Must use internal pull up resistors for proper communication
    gpio_pull_up(PICO_DEFAULT_I2C_SCL_PIN);
    gpio_pull_up(PICO_DEFAULT_I2C_SDA_PIN); 

    //Check to see if device is connected properly
    sleep_ms(1000);
    uint8_t reg = 0x00;
    uint8_t chipID[1];
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, &reg, 1, true);
    i2c_read_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, chipID, 1, false);

    if (chipID[0] != 0xA0) return false; 

    //Use internal oscillators
    uint8_t data[2] = {0x3F, 0x40};
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, data, 2, true);

    // Configure Power Mode
    data[0] = 0x3E;
    data[1] = 0x00;
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, data, 2, true);
    sleep_ms(50);

    // Defaul Axis Configuration
    data[0] = 0x41;
    data[1] = 0x24;
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, data, 2, true);

    // Default Axis Signs  look at page 24 for recongiguration of axis
    // Currently dot on chip = y points up
    data[0] = 0x42;
    data[1] = 0x00;
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, data, 2, true);

    // Set units to m/s^2 - Defaults
    data[0] = 0x3B;
    data[1] = 0b0001000;
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, data, 2, true);
    sleep_ms(30);

    // Set operation to 
    data[0] = 0x3D;
    data[1] = 0x0C;
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, data, 2, true);
    sleep_ms(100);

    return true;
}
void bno055_collect_data(double *data){
    // Gyro Variables 
    uint8_t tilt[4]; // Store data from the 6 acceleration registers
    uint8_t rot[2]; 

    int16_t tiltX, tiltY, rotz; // Combined 3 axis data
    
    double f_tiltX, f_tiltY, f_rotz;

    uint8_t val = 0x1C;   // Start address for Euler Angles
    uint8_t val2 = 0x18;  // Start address for Z Gyro Rotaion

    //Collect Euler Data 
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, &val, 1, true);
    i2c_read_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, tilt, 4, false);

    tiltX = ((tilt[1]<<8) | tilt[0]);
    tiltY = ((tilt[3]<<8) | tilt[2]);

    f_tiltX = tiltX;
    f_tiltY = tiltY;

    f_tiltX = f_tiltX/10;
    f_tiltY = f_tiltY/10;

    // Collect Gyro Rotational Data 
    i2c_write_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, &val2, 1, true);
    i2c_read_blocking(I2C_BNO055_ID, I2C_BNO055_ADDR, rot, 2, false);

    rotz = ((rot[1]<<8) | rot[0]);

    f_rotz = rotz;
    f_rotz = f_rotz/100;

    data[0] = f_tiltX;
    data[1] = f_tiltY;
    data[2] = f_rotz;

}
// ! ADC Voltage Functions
void voltage_init(){
    // Inititalize ADC for Voltage Measurement
    adc_init();
    adc_gpio_init(ADC_Voltage);
    adc_select_input(0);
}
double calc_volts(uint16_t adc_value){
    const float conversion_factor = 3.3f / (1 << 12);
    return (adc_value * conversion_factor) / current_divider_val;
}

// ! SPI System for SD card reader


// * -------------------------------------------------------------------------------------*//
// ! Behavioral Multicore Functions
volatile double prev_alt = 0; 

void core1_interrupt_handler(){
    double core1_altitude;
    uint8_t core1_state;  
    while(multicore_fifo_rvalid()){
        core1_altitude = multicore_fifo_pop_blocking();
        core1_state = multicore_fifo_pop_blocking(); 
        core1_altitude /= 100; 
        // TODO Behavior Here
    }
    prev_alt = core1_altitude;
    multicore_fifo_push_blocking(core1_state);

    multicore_fifo_clear_irq();

}
// Core 1 Main entry Code
void core1_entry(){
    multicore_fifo_clear_irq();
    irq_set_exclusive_handler(SIO_IRQ_PROC1, core1_interrupt_handler);
    irq_set_enabled(SIO_IRQ_PROC1, true);
    // ! This function acts like a main function and 
    // ! all data will be handeled through the interrupt
    while(1){
        tight_loop_contents();
    }
}
//*--------------------------------------------------------------------------------------*//
// ! Core 0 Main Code
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

    //Setup BNO055
    bool bno055_setup = setup_bno055();

     //Setup MPL3115A2
    bool MPL3115A2_setup = setup_MPL3115A2();

    // Initialize Current Divider for voltage
    voltage_init();

    //Core 1 Thread Initialize 
    multicore_launch_core1(core1_entry);

    uint8_t command = 0; 

    // ! Functional Variable 
    bool CX_ON = false;
    bool BCN_ON = false;
    bool BCN_CHANGE = false; 
    bool SIM_ENABLE = false;
    bool SIM_ACTIVATE = false;
    bool SIMP_FLAG = false;

    double curr_press = 0.0; 
    double curr_alt = 0.0;
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

    while (1) {
        tight_loop_contents();

        double  MPL3115A2_data[2];

        // Send and receive data through UART (in a real application)
        if (uart_is_readable(UART_ID_XBEE)){

            char command_container [4][10] = {"","","",""};
            command = xbee_uart_rx(command_container);

            // TODO Mash two ends of command conatiner 
            // Feedback to make sure commands reached payload;
            uart_putc(UART_ID_XBEE, '1');
           
            //Switch statement for behavior of incoming transmission
            switch(command){
                
                case 0: // CX ON/OFF - Payload should turn on/off
                    if (strcmp(command_container[3],"ON") == 0) CX_ON = true;
                        // CX ON - Payload should turn on    
                    else  CX_ON = false;
                        // CX OFF - Payload should turn off     
                    gpio_put(CAM_TRIGGER, CX_ON);
                break; 

                case 1:{ // ST UTC/GPS - Set payload time to GS UTC/GPS time
                    int hour, min, sec = 0; 
                    if ((strcmp(command_container[3],"-1") == 0)){
                        // Container for GPS data
                            char gps_data[15][12];
                        //Get Data from GPS 
                            uart_Rx_handler_gps(gps_data);
                        // Break apart time from gps
                            double fractionalSeconds;
                        
                            sscanf(gps_data[3], "%2d%2d%2d.%f", &hour, &min, &sec, &fractionalSeconds);
                       
                    }
                    else sscanf(command_container[3], "%d:%d:%d", &hour, &min, &sec);

                    mission_time = (hour * 3600) + (min * 60) + (sec);
                }    
                break;

                case 2: // SIM command - All sim commands go here
                    if ((strcmp(command_container[3],"ACTIVATE") == 0)) SIM_ACTIVATE = true;
                        // SIM ACTIVATE - Set sim_activate to true
                    else if ((strcmp(command_container[3],"ENABLE") == 0)) SIM_ENABLE = true;
                       // SIM ENABLE - Set sim_enable to true   
                    else SIM_ACTIVATE = false, SIM_ENABLE = false; 
                        // SIM DISABLE - Set bot sim_activate & enable to false   
                break;

                case 3: //SIMP pressure# - Set internal pressure value to #
                    // pressure used for calcultaion are equal to value
                    //curr_press = value;
                    SIMP_FLAG = true; 
                break;

                 case 4: //CAL- Set current altitiude to 0
                    // TODO set pressure offset in chip
                    
                break;

                case 5: // BCN ON/OFF - Audio beacon on and off
                     if (strcmp(command_container[3],"ON") == 0) BCN_ON = true;
                        // BCN ON - Audio beacon on 
                    else BCN_ON = false; 
                        //  BCN OFF - Audio beacon off
                    BCN_CHANGE = true; // Make a BCN flag variable
                break;

                default:
                break;
            }
            // Set CMD_ECHO to last command
            sprintf(CMD_ECHO, "%s_%s", command_container[2],command_container[3]); 

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
              
               //Collect BMP 280 Data
                MPL3115A2_collect_data(MPL3115A2_data);
                curr_press = MPL3115A2_data[0];

            }
            // Regardless of Mode, altitude will be calculated from curr_pressure
            if (MPL3115A2_setup) curr_alt = press_to_alt_bar(curr_press);
            else curr_alt = 0.0;

            // Add current altitude and state num to FIFO core1 for behavior 
            multicore_fifo_push_blocking(curr_alt * 100);
            multicore_fifo_push_blocking(current_state); 

            // ! If 1 second has passed, or in SIM Mode, create packet
            if ( uart_is_writable(UART_ID_XBEE) & (new_TX || (SIM_ACTIVATE & SIM_ENABLE))){
                //Reset Transmission Flag
                new_TX = false; 

                // Packet container with 70 character, might need more if necessary
                char packetTX[150];
                char buffer[20];

                // Container for GPS data
                char gps_data[17][12] = {"","","","","","","","","","","","","","",""};

                //Get Data from GPS 
                bool fix = uart_Rx_handler_gps(gps_data);

                //Collect Euler & Gyro Data
                double bno55_data[0];
                bno055_collect_data(bno55_data);

                //Vollect Voltage values 
                uint16_t adc_result = adc_read();
                double voltage = calc_volts(adc_result);

                // Collect all values back from FIFO
                if (multicore_fifo_rvalid()) current_state = multicore_fifo_pop_blocking();

                // * Team ID
                    // Convert the integer to a string
                    sprintf(packetTX, "%d", TEAM_ID);
                    strcat(packetTX,",");
                    
                // * Mission Time in UTC no ms
                    uint8_t hour =(uint8_t) floor(mission_time / 3600);
                    uint8_t min = (uint8_t) floor((mission_time - hour * 3600) / 60);
                    uint8_t sec  = mission_time - (hour * 3600) - (min * 60); 
                    snprintf(buffer, 9, "%02d:%02d:%02d", hour,min,sec);
                    strcat(packetTX, buffer);
                    strcat(packetTX,",");

                // * Packet Count of the Payload 
                    // Packet count is incremented
                    sprintf(buffer, "%d", packet_count++); 
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
                    sprintf(buffer, "%.1f", curr_alt); 
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * AIR_SPEED
                    sprintf(buffer, "%.1f", 0.0);    // TODO Change "floatvalue" to function that generates item
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Heat Shield Deployed P(deployed) N(Otherwise)
                    if (current_hs) strcat(packetTX,"P,");
                        else strcat(packetTX,"N,");

                // * Parachute Deployed C (deployed @100 m) and N(otherwise)
                    if (current_pc) strcat(packetTX,"C,");
                        else strcat(packetTX,"N,");

                // * Temperature using 0.1 degrees Celcius
                    double temp_curr;
                    if (MPL3115A2_setup) temp_curr = MPL3115A2_data[1];
                    else temp_curr = 0.0; 
                    sprintf(buffer, "%.1f", temp_curr);  
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Voltage in 0.1 V
                    sprintf(buffer, "%.1f", voltage);  
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Pressure in 0.1 kPa
                    double pres_curr;
                    if (MPL3115A2_setup) pres_curr = curr_press/1000;
                    else pres_curr = 0.0; 
                    sprintf(buffer, "%.1f", pres_curr); 
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * GPS Time in UTC with a resolutions of one second
                    if (fix){
                        int hour, min, sec; 
                        double fractionalSeconds; 
                        scanf(gps_data[2], "%2d%2d%2d.%f", &hour, &min, &sec, &fractionalSeconds);
                        sprintf(buffer, "%02d:%02d:%02d", hour, min, sec);
                        strcat(packetTX, buffer);
                    } 
                    else strcat(packetTX, "00:00:00");
                    strcat(packetTX,",");

                // * GPS Altitude in 0.1 m
                    if (fix) strcat(packetTX, gps_data[10]);
                    else strcat(packetTX, "0.0");
                    strcat(packetTX,",");

                // * GPS Latitude in decimal degrees with 0.0001 degrees North Resolution
                    if (fix){
                        double temp_lat; 
                        scanf(gps_data[3], "%f", &temp_lat);
                        sprintf(buffer, "%.4f", temp_lat/100);
                        strcat(packetTX, buffer);
                    } 
                    else strcat(packetTX, "0.0000");
                    strcat(packetTX,",");

                // * GPS Longitude in decimal degress with 0.0001 degrees West resolution
                     if (fix){
                        double temp_lon; 
                        scanf(gps_data[5], "%f", &temp_lon);
                        sprintf(buffer, "%.4f", temp_lon/100);
                        strcat(packetTX, buffer);
                    } 
                    else strcat(packetTX, "0.0000");
                    strcat(packetTX,",");
                
                 // * GPS SATS, the amount of satellites the GPS is using
                    if (fix) strcat(packetTX, gps_data[8]);
                    else strcat(packetTX, "0");    
                    strcat(packetTX,",");

                // * Tilt X/Y direction 0.01 degree resolution. 0 = X/Y perpendicular to Z axis -> center of Earth
                    
                    if (bno055_setup) sprintf(buffer, "%.2f", bno55_data[0]);   
                    else sprintf(buffer, "%.2f", 0.0);
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                    if (bno055_setup) sprintf(buffer, "%.2f", bno55_data[1]);  
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Rotation rate in degrees/sec with 0.1 deg/sec resolution
                    if (bno055_setup) sprintf(buffer, "%.1f", bno55_data[2]);   
                    else sprintf(buffer, "%.1f", 0.0);
                    strcat(packetTX,buffer);
                    strcat(packetTX,",");

                // * Last Command read
                    strcat(packetTX,CMD_ECHO);
                    strcat(packetTX,"\n"); 

                //Write packet string into UART => XBEE
               
                uart_puts(UART_ID_XBEE, packetTX);
                // TODO Remove when done testing 
                //uart_puts(UART_ID_XBEE, gps_info);

                //Create a timmer that will trigger an IRQ after 1 second => 1Hz
                add_alarm_in_ms(1000, alarm_callback, NULL, false);
            }
            else {
                // ! If we don' need to send a message, we still need to extract the last data from FIFO 
                // ! to make sure only the most current data is available
                while(multicore_fifo_rvalid()){
                    // * We don't need this data, we only need to remove it. 
                    multicore_fifo_pop_blocking();
                }
            }
        }
    }
   
    return 0;
}
