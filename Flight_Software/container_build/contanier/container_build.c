#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/timer.h"
#include "strings.h"
#include "math.h"
// Main sensor libraries
#include "h_files/bmp280_i2c.h"
#include "h_files/bno055.h" 
#include "h_files/power_status.h"
#include "h_files/helper_funcs.h"

// General UART Settings 
#define BAUD_RATE 9600
#define DATA_BITS 8
#define STOP_BITS 1
#define PARITY    UART_PARITY_NONE

//Defines related to GPS UART System
#define UART_ID_GPS uart1

// Defines related to Xbee communication through UART
#define UART_TX_PIN_XBEE 0
#define UART_RX_PIN_XBEE 1
#define UART_ID_XBEE uart0

#define BCN_PIN 5 // Change later
#define CAM_TRIGGER 6

#define GRAVITY_CONSTANT 9.80665  // Standard gravity constant in m/s^2
#define MOLAR_MASS_AIR 0.0289644  // Molar mass of dry air in kg/mol
#define UNIVERSAL_GAS_CONSTANT 8.31447  // Universal gas constant in J/(mol·K)
#define SEA_LEVEL_STANDARD_TEMPERATURE 288.15  // Standard sea level temperature in K
#define SEA_LEVEL_STANDARD_PRESSURE 101325.0  // Standard sea level pressure in Pa

volatile bool new_TX = true;
volatile bool new_RX = false;
//Interrupt function
void uart_Rx_handler(){
    //Add function for when there is a usart transmission
    new_RX = true;  
}

// Interrupt to set transmssion at 1Hz
int64_t  alarm_callback(alarm_id_t id, void *user_data)
{
    // Set new transmission flag to true
    new_TX = true;

    return 0;

}
volatile uint64_t mission_time = 0; 
// Internal Mission Time Keeper
bool repeating_timer_callback(struct repeating_timer *t) {
    mission_time ++; 
    return true;
}

// setup functions 
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

    // Set up a RX interrupt
    // We need to set up the handler first
    // Select correct interrupt for the UART we are using
    int UART_IRQ = UART_ID_XBEE == uart0 ? UART0_IRQ : UART1_IRQ;

    // And set up and enable the interrupt handlers
    irq_set_exclusive_handler(UART_IRQ, uart_Rx_handler);
    irq_set_enabled(UART_IRQ, true);

    // Now enable the UART to send interrupts - RX only
    uart_set_irq_enables(UART_ID_XBEE, true, false);
    
}


double press_to_alt_bar(double pressure) {
    return ((SEA_LEVEL_STANDARD_TEMPERATURE / GRAVITY_CONSTANT) * log(SEA_LEVEL_STANDARD_PRESSURE / pressure));
}
void setup_bmp280(){

}
void setup_bno055(){

}
void setup_powersource(){ // 

}

// void setup_gps(){
//     // Initialize UART with desired baud rate
//     uart_init(UART_ID_XBEE, BAUD_RATE);
    
//     // Set UART pins (UART0 defaults to GPIO1 and GPIO3)
//     uart_set_gpio(UART_ID_XBEE, 1, 0);  // GPIO 1 (TX)
//     uart_set_gpio(UART_ID_XBEE, 0, 1);  // GPIO 2 (RX)

//     // Enable UART
//     uart_set_hw_flow(UART_ID_XBEE, false, false); // Disable hardware flow control
//     uart_set_format(UART_ID_XBEE, 8, 1, UART_PARITY_NONE);
//     uart_set_fifo_enabled(UART_ID_XBEE, false);   // Disable FIFO for now

//     // Print a message through UART
//     printf("UART configured on GPIO1 (TX) and GPIO2 (RX) with baud rate %d.\n", BAUD_RATE);

//     // ! Establish UART connection
//     //Create containers
//     //Store Data
//     //have it for future use. 
// }

void command_parse(uint8_t *command, int16_t *value2, char *command_string) { // TODO Add TX variable you will be parseing 
    // TODO Parse function in here
}

void command_intake(char *command_string) {
    //Collecting all incoming data from uart
    uint8_t i = 0; 
    while (uart_is_readable(UART_ID_XBEE)) {
        // While there is something in the UART system, Add it to array of characters
        command_string[i] = uart_getc(UART_ID_XBEE);
        // Increment place holder.
        i ++; 
    }
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
     
     // setup_gps();       //Setup GPS 
    
    uint8_t command = 0; 
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
    char command_string[21]; 

    // This will be the internal Mission Time Keeper, the current count will be 
    // offset given by the GCS. The IRQ is triggered every 1 second,
    // Should give the Payload enough time to function. 
    struct repeating_timer timer;
    add_repeating_timer_ms(1000, repeating_timer_callback, NULL, &timer);

    
    while (1) {
        // Send and receive data through UART (in a real application)
        if (new_RX){
            //Reset Tx Flag
            new_RX = false;

            //Collect incoming data
            command_intake(command_string);
           
            // Call the function and pass addresses of variables to store the values and parse TX
            command_parse(&command,&value, command_string);

            //Switch statement for behavior of incoming transmission
            switch(command){
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

            // ! This statement will stop the loop from continuing 
            if (CX_ON == false) continue;  

            // ! If there is a change in BCN_ON,
            if (BCN_CHANGE){  
                // Then make the pin output to the value of BCN_ON
                gpio_put(BCN_PIN, BCN_ON);  
                // Change flag
                BCN_CHANGE = false; 
            }

            // ! If in simulation mode
            if (SIM_ACTIVATE & SIM_ENABLE){ 
                // altitude calculation based on value
                //if SIMP_FLAG has been changed or true(there was a value loaded to curr_pressure)
                if (SIMP_FLAG == false) continue; 
                //Value should be assinged by this point (curr_pressure = value)
                else SIMP_FLAG = false;   
            }
            else{
                continue;
                //TODO curr_press = pressure sensor value
            }
            // Regardless of Mode, altitude will be calculated from curr_pressure
            curr_alt = press_to_alt_bar(curr_press);

            // ! Regardless of Time passed, evaluate behavior
            // TODO Behavior of payload use (curr_alt and prev_alt) to set states etc...

            // ! If 1 second has passed, or in SIM Mode, create packet
            if (new_TX || (SIM_ACTIVATE & SIM_ENABLE)){
                new_TX = false; 
               
                // Packet count is incremented
                packet_count ++; 
                char str[10]; 
                sprintf(str, "%d", mission_time); // Convert the integer to a string

                //Write packet string into UART => XBEE
                if (uart_is_writable(UART_ID_XBEE)) {
                    uart_puts(UART_ID_XBEE, "\nTesting Uart every 1 second at time\n");
                    uart_puts(UART_ID_XBEE, str);
                }
                 //Create a timmer that will trigger an IRQ after 1 second => 1Hz
                add_alarm_in_ms(1000, alarm_callback, NULL, false);
            }
        

            prev_alt = curr_alt; 


        }
    }

    return 0;
}
