/*
 * ICM-42688.h
 *
 *  Created on: Apr 27, 2024
 *      Author: leand
 */

#ifndef INC_ICM_42688_H_
#define INC_ICM_42688_H_

#include "stm32h7xx_hal.h"
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>

#define DEVICE_ADDR_ICM (0x68 << 1)


#define SENSOR_CONFIG0 0x03
#define SENSOR_OFFSET 0x77 //->0x7F
#define ACCEL_ODR 0x50
#define ACCEL_POWER 0x4E
#define ACCEL_MODE

#define PWR_MGMT0 0x4E
#define GYRO_CONFIG0 0x4F
#define ACCEL_CONFIG0 0x50

#define DATA_START 0x1D

#define PWR_SET_ICM 0b00011111
#define GYRO_SETTING 0b00000110
#define ACCEL_SETTING 0b00000110


typedef struct ICM_data {

    double GYRO_X;
    double GYRO_Y;
    double GYRO_Z;
    double ACCEL_X;
    double ACCEL_Y;
    double ACCEL_Z;
    double TEMP;
    void (*collect_data)(struct ICM_data *, I2C_HandleTypeDef*);
} ICM_data;




void setup_ICM (I2C_HandleTypeDef* hi2c);
void collect_data (struct ICM_data *sensor, I2C_HandleTypeDef* hi2c);
ICM_data *ICM_sensor_create() ;

#endif /* INC_ICM_42688_H_ */
