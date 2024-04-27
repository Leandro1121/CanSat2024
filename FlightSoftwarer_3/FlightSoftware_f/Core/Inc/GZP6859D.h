/*
 * GZP6859D.h
 *
 *      Author: Brayden Bevels
 */

#ifndef INC_GZP6859D_H_
#define INC_GZP6859D_H_

#include "stm32h7xx_hal.h"
//#include "stm32h7xx_hal_i2c.h"
#include "stdint.h"
#include <math.h>
#include <stdlib.h>

#define GZP_I2C_ADDR (0x6D << 1)

#define K_VAL 64

//GZP register locations:
#define CMD 0x30
#define REQUEST_CMD 0x0A //start conversion for both pressure and temp

//system config
#define SYS_CFG 0xA5

//Starting device addr for reading 3 pressure bytes and 2 temp bytes
#define START_ADDR 0x06

////functions
//return status struct if issues with hal
void GZP_SET_REG(I2C_HandleTypeDef* hi2c, uint8_t reg_addr, uint8_t input);
uint8_t GZP_READ_REG(I2C_HandleTypeDef* hi2c, uint8_t reg_addr);

//CALL GZP_READ_DATA FIRST! then read pressure and temp
void GZP_READ_DATA(I2C_HandleTypeDef* hi2c, uint8_t* combined);
double GZP_READ_PRESSURE(uint8_t* combined); //kPa
double GZP_READ_TEMP(uint8_t* combined); //C


#endif /* INC_GZP6859D_H_ */
