#ifndef GZP6859_H_
#define GZP6859_H_

#include "stm32h7xx_hal_i2c.h"
#include "stdint.h"

#define GZP_I2C_ADDR 0x36
#define RATE 100000
#define SDA_pin 4
#define SCL_pin 5

#define K_VAL 64

//GZP register locations:
//command
#define CMD 0x30
#define REQUEST_CMD 0x02 //start conversion for both pressure and temp

//system config
#define SYS_CFG 0xA5

//Starting device addr for reading 3 pressure bytes and 2 temp bytes
#define START_ADDR (uint16_t) (0x06 | 0x01)

//global vars
//extern Hal_StatusTypeDef status; //might not be used
extern uint8_t* combined;

//functions
void GZP_INIT(I2C_HandleTypeDef* hi2c_);
//return status struct if issues with hal
void GZP_SET_REG(uint8_t reg_addr, uint8_t input);
uint8_t GZP_READ_REG(uint8_t reg_addr);

//CALL GZP_READ_DATA FIRST! then read pressure and temp
void GZP_READ_DATA(void);
float GZP_READ_PRESSURE() //kPa
float GZP_READ_TEMP() //C
