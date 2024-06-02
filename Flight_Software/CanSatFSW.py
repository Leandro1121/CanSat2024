import sensor, image, time, pyb, mjpeg
import uasyncio as asyncio
import machine
import ustruct
import uctypes
import math
from math import log
from pyb import LED  # Import the LED class from the pyb module


## **********************/ UART 1 Setup for XBEE/ ****************************

# Create UART objects
xbee = machine.UART(1, baudrate=9600)
xbee.init(9600, bits=8, parity=None, stop=1)

##**********************/ UART 3 Setup for GPS/ ******************************

PMTK_SET_NMEA_OUTPUT_GGAONLY = "$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29\r\n"
# Create UART objects
gps = machine.UART(3, baudrate=9600)
gps.init(9600, bits=8, parity=None, stop=1)
time.sleep_ms(100)
gps.write(PMTK_SET_NMEA_OUTPUT_GGAONLY)

# *********************/ I2C Setup for rest of Sensors **********************

i2c = machine.I2C(4,freq=400000)

## ***********************/ Peripheral Setup / *************************************

## **********************/ ICM-42688 /**************************************
# ! Need to space write commands apart by 250 ms
ICM_addr = 104
DATA_START = 29
time.sleep_ms(250)
i2c.writeto_mem(ICM_addr, 80, b'\x06') # Modify ACCEL_CONFIG0
time.sleep_ms(250)
i2c.writeto_mem(ICM_addr, 79, b'\x06') # Modify GYRO_CONFIG0
time.sleep_ms(250)
i2c.writeto_mem(ICM_addr, 78, b'\x1F') # Modify PWR_MNMT
time.sleep_ms(250)
## **********************/ BMP-388 /****************************************
BMP_addr = 119
class BMP388CalibData:
    def fill_calibration_params(self, buffer):
        # Assign buffer values to NVM_PARAMs
        self.NVM_PAR_T1 = (buffer[1] << 8) | buffer[0]
        self.NVM_PAR_T2 = (buffer[3] << 8) | buffer[2]
        self.NVM_PAR_T3 = buffer[4]

        self.NVM_PAR_P1 = (buffer[6] << 8) | buffer[5]
        self.NVM_PAR_P2 = (buffer[8] << 8) | buffer[7]
        self.NVM_PAR_P3 = buffer[9]
        self.NVM_PAR_P4 = buffer[10]
        self.NVM_PAR_P5 = (buffer[12] << 8) | buffer[11]
        self.NVM_PAR_P6 = (buffer[14] << 8) | buffer[13]
        self.NVM_PAR_P7 = buffer[15]
        self.NVM_PAR_P8 = buffer[16]
        self.NVM_PAR_P9 = (buffer[18] << 8) | buffer[17]
        self.NVM_PAR_P10 = buffer[19]
        self.NVM_PAR_P11 = buffer[20]


class BMP388Data:
    def set_coeff(self, calib_data):
        self.PAR_T1 = calib_data.NVM_PAR_T1 / pow(2.0, -8.0)
        self.PAR_T2 = calib_data.NVM_PAR_T2 / pow(2.0, 30.0)
        self.PAR_T3 = calib_data.NVM_PAR_T3 / pow(2.0, 48.0)

        self.PAR_P1 = (calib_data.NVM_PAR_P1 - pow(2.0, 14.0)) / pow(2.0, 20.0)
        self.PAR_P2 = (calib_data.NVM_PAR_P2 - pow(2.0, 14.0)) / pow(2.0, 29.0)
        self.PAR_P3 = calib_data.NVM_PAR_P3 / pow(2.0, 32.0)
        self.PAR_P4 = calib_data.NVM_PAR_P4 / pow(2.0, 37.0)
        self.PAR_P5 = calib_data.NVM_PAR_P5 / pow(2.0, -3.0)
        self.PAR_P6 = calib_data.NVM_PAR_P6 / pow(2.0, 6.0)
        self.PAR_P7 = calib_data.NVM_PAR_P7 / pow(2.0, 8.0)
        self.PAR_P8 = calib_data.NVM_PAR_P8 / pow(2.0, 15.0)
        self.PAR_P9 = calib_data.NVM_PAR_P9 / pow(2.0, 48.0)
        self.PAR_P10 = calib_data.NVM_PAR_P10 / pow(2.0, 48.0)
        self.PAR_P11 = calib_data.NVM_PAR_P11 / pow(2.0, 65.0)


class BMP388Sensor:
    def __init__(self):
        self.raw_calib = BMP388CalibData()
        self.data = BMP388Data()

    def fill_calibration_params(self, buffer):
        self.raw_calib.fill_calibration_params(buffer)

    def set_coeff(self, calib_data):
        self.data.set_coeff(calib_data)

    def get_compensated(self, hi2c):
        # Collect data from registers
        temp = hi2c.readfrom_mem(BMP_addr, 0x04, 6)
        uncomp_temp = (temp[5] << 16) | (temp[4] << 8) | temp[3]

        partial_data1 = (uncomp_temp - self.data.PAR_T1)
        partial_data2 = (partial_data1 * self.data.PAR_T2)
        self.data.T_LIN = partial_data2 + (partial_data1 * partial_data1) * self.data.PAR_T3

        self.get_pressure_compensated(hi2c, temp)

    def get_pressure_compensated(self, hi2c, buffer):
        uncomp_press = (buffer[2] << 16) | (buffer[1] << 8) | buffer[0]

        partial_data1 = self.data.PAR_P6 * self.data.T_LIN
        partial_data2 = self.data.PAR_P7 * (self.data.T_LIN * self.data.T_LIN)
        partial_data3 = self.data.PAR_P8 * (self.data.T_LIN * self.data.T_LIN * self.data.T_LIN)
        partial_out1 = self.data.PAR_P5 + partial_data1 + partial_data2 + partial_data3

        partial_data1 = self.data.PAR_P2 * self.data.T_LIN
        partial_data2 = self.data.PAR_P3 * (self.data.T_LIN * self.data.T_LIN)
        partial_data3 = self.data.PAR_P4 * (self.data.T_LIN * self.data.T_LIN * self.data.T_LIN)
        partial_out2 = (float(uncomp_press) * (self.data.PAR_P1 + partial_data1 + partial_data2 + partial_data3))

        partial_data1 = (float(uncomp_press) * float(uncomp_press))
        partial_data2 = self.data.PAR_P9 + self.data.PAR_P10 * self.data.T_LIN
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + ((float(uncomp_press) * float(uncomp_press) * float(uncomp_press)) * self.data.PAR_P11)
        self.data.P_LIN = partial_out1 + partial_out2 + partial_data4 - cal_offset

    def calibrate_sensor(self, hi2c):
        buffer = bytearray(21)

        i2c.readfrom_mem_into(BMP_addr, 49, buffer)
        time.sleep_ms(250)

        self.fill_calibration_params(buffer)
        self.set_coeff(self.raw_calib)

        i2c.writeto_mem(BMP_addr, 126, b'\xB6') # Soft Reset
        time.sleep_ms(250)
        i2c.writeto_mem(BMP_addr, 31, b'\x04') # Modify IIR Filter
        time.sleep_ms(250)
        i2c.writeto_mem(BMP_addr, 29, b'\x02') # Modify ODR Setting
        time.sleep_ms(250)
        i2c.writeto_mem(BMP_addr, 28, b'\x03') # Modify OSR Setting
        time.sleep_ms(250)


bmp = BMP388Sensor()
bmp.calibrate_sensor(i2c)
i2c.writeto_mem(BMP_addr, 27, b'\x33') # Turn Sensor On
time.sleep_ms(250)

#bmp.get_compensated(i2c)
#bmp.data.T_LIN -> for temperature
#bmp.data.P_Lin -> for pressure

## **********************/ GZP6859 /****************************************
GZP_addr = 109
K_VAL = 64
def gzp_read_pressure(combined):
    pressure_adc = ((combined[0] << 16) | (combined[1] << 8) | combined[2])
    check_sign = 1 << 23

    # Convert ADC to kPa units
    # bit 23 is 0, positive
    if (pressure_adc & check_sign) != check_sign:
        return pressure_adc / K_VAL

    return (pressure_adc - (2 ** 24)) / K_VAL

def gzp_read_temp(combined):
    temp_adc = ((combined[3] << 8) | combined[4])
    check_sign = 1 << 15

    # Convert ADC to C units
    # bit 15 is 0, positive
    if (temp_adc & check_sign) != check_sign:
        return temp_adc / 256  # from GZP6859D datasheet
    else:
        return (temp_adc - (2 ** 16)) / 256  # ""

def gzp_calc_speed():
    combined = bytearray(5)
    # Collect Data
    i2c.writeto_mem(GZP_addr, 48, b'\x0A')
    time.sleep_ms(20)
    i2c.readfrom_mem_into(GZP_addr, 6, combined)
    R = 287  # J/kg/K
    P = gzp_read_pressure(combined)
    T = gzp_read_temp(combined)
    # air density = pressure / (temp * specific gas constant)
    # kg/m^3 = (Pa or N/m^2) / (K * J/kg/K)
    p = P / (T * R)
    velocity = (2 * P) / p
    return math.sqrt(velocity)  # sqrt(2P/p)

## **********************/ On-board components /****************************
# LED's
status_fault = LED(1)
status_received = LED(2)
status_ready  = LED(3)

# Buzzer
buzzer = pyb.Pin("G3", pyb.Pin.OUT)
# Voltmeter
adc = machine.ADC("A5")

# **********************/ Camera Setup with SD /*************************************
sd=pyb.SDCard()
if sd.present():
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)

    m = mjpeg.Mjpeg('flight_recording.mjpeg')
clock = time.clock()
#*************************************************************#
#Constants
TEAM_ID = "2062"
#*************************************************************#
# Variables that we need for functionality
alt_pressure = 0.0
altitude = 0
state_num = 0
packet = 0
record = False
mode = "F"
#***********************/ None Async Funcs /********************************#
def calculate_altitude(pressure, sea_level_pressure=101325.0):
    altitude = (1 - (pressure / sea_level_pressure) ** (1 / 5.255)) * 44330.0
    return altitude
# **************************************************************************#
# Behavior of payload
state = ["LAUNCH_WAIT","ASCENT", "HS_RELEASE", "DECENT", "PC_RELEASE", "DECENT_F", "LANDED"]
state_num = 0
pers_count = 0
hs = ["N","P"]
pc = ["N","C"]
hs_deployed = False
pc_deployed = False
prev_altitude = 0
def det_state():
    global state_num, hs_deployed, pc_deployed, prev_altitude
    # This function determines state number from current altitude and flight

    # If ascending
    if (altitude > 30 or (altitude - prev_altitude > 10)) and state_num == 0:
        state_num += 1

    elif (state_num == 1): # Ascent
        if altitude > 700 or (altitude - prev_altitude < 0):
            state_num += 1
        else: # What will the payload do will Ascending
            pass

    elif (state_num == 2): # HS_Release
        hs_deployed = True # Delay maybe?
        state_num += 1

    elif (state_num == 3): # Decent
        if altitude < 130:
            state_num += 1
        else: # What will the payload do will Decending
            pass

    elif (state_num == 4): # PC_Deploy
        state_num += 1
        pc_deployed = True

    elif (state_num == 5): # Decent
        if altitude < 10 or (altitude - prev_altitude < 10):
            state_num += 1
        else: # What will the payload do will Decending 2
            pass
    elif (state_num == 6):
        pass

    prev_altitude = altitude



# *********************/ Async Funcs /***************************************#
async def send_packet():
    # Collect GPS data
    while not gps.any(): pass
    try:
        gps_data = gps.read().decode('utf-8').split(",")
        gps_time = float(gps_data[1])
        gps_lat  = 0
        gps_long = 0
        gps_sats = 0
        gps_alt  = 0
        try:
            gps_lat_DMC  = float(gps_data[2])
            gps_lat_dec = math.floor(gps_lat_DMC / 100)
            gps_lat = gps_lat_dec + (gps_lat_DMC - gps_lat_dec*100)/60

            gps_long_DMC  = float(gps_data[4])
            gps_long_dec = math.floor(gps_long_DMC / 100)
            gps_long = (gps_long_dec + (gps_long_DMC - gps_long_dec*100)/60) * -1

            gps_sats = int(gps_data[7])
            gps_alt  = int(gps_data[9])
        except:
            pass

        await asyncio.sleep_ms(100)  # Let the event loop run

        # Collect Voltage Data
        volt = (adc.read_u16() * 0.33 / (1 << 12)) / 0.6667
        await asyncio.sleep_ms(100)  # Let the event loop run


        # Collect Orientation Data
        raw = i2c.readfrom_mem(ICM_addr, DATA_START, 14)

        tilt_x = float(((raw[8]  << 8) | raw[9]))   *0.001
        tilt_y = float(((raw[10] << 8) | raw[11]))  *0.001
        rot_z  = float(((raw[6] << 8)  | raw[7]))   *0.01
        await asyncio.sleep_ms(100)  # Let the event loop run

        # Collect Air Speed Data
        air_speed = gzp_calc_speed()
        await asyncio.sleep_ms(100)  # Let the event loop run

        # Modify Internal Time
        current_sec = pyb.millis() / 1000 # Add the offset
        hour = math.floor(current_sec/3600)
        minute = math.floor((current_sec - hour * 3600) / 60)
        sec  = math.floor(current_sec - (hour * 3600) - (minute * 60))
        mission_time = ("{:02d}:{:02d}:{:02d}").format(hour, minute, sec)
        await asyncio.sleep_ms(100)  # Let the event loop run

        # Modify GPS Time
        gps_hour = math.floor(gps_time/10000)
        gps_minute = math.floor((gps_time - gps_hour * 10000 )/100 )
        gps_sec = math.floor((gps_time - gps_hour * 10000 - gps_minute * 100))
        gps_time_output = ("{:02d}:{:02d}:{:02d}").format(gps_hour,gps_minute,gps_sec)
        await asyncio.sleep_ms(100)  # Let the event loop run

        # BMP Temperature
        temp = bmp.data.T_LIN

        # Increment packet count

        tx_packet =("{},{},{},{},{},{:.1f},{:.1f},{},{},{:.1f},{:.1f},{:.1f},"
                    "{},{:.1f},{:.4f},{:.4f},{},{:.1f},{:.1f},{:.1f},{}\n"
        ).format(TEAM_ID, mission_time, packet, mode[flight_mode], state[state_num],
                 altitude, air_speed, hs[hs_deployed], pc[pc_deployed], temp, alt_pressure, volt,
                 gps_time_output, gps_alt, gps_lat, gps_long, gps_sats,tilt_x, tilt_y,
                 rot_z, CMD_ECHO
                 )
        print(tx_packet)
        xbee.write(tx_packet)
        await asyncio.sleep_ms(100)

    except Exception as e:
        print("Failure:", e)
        return False
    return True
# ***************************************************************************#
async def record_video():
    while sd.present():
        if record:
            clock.tick()
            m.add_frame(sensor.snapshot())
        await asyncio.sleep_ms(33)  # 30 frames per second

#*********************************************************#
# Function modifies globals based on incoming XBEE Packet
CX_ON = False
BCN_ON = False
SIM_ACTIVATE = False
SIM_ENABLE = False
CAL = False
SLEEP_PERIOD = 100
CMD_ECHO = ""
cal_offset = 131757 - 101325.0
SIMP_FLAG = False
async def collect_command():
    global alt_pressure, CX_ON, CMD_ECHO, SIM_ACTIVATE, SIM_ENABLE, BCN_ON
    while True:
        try:
            if xbee.any():
                command = xbee.read().decode('utf-8').split(",")
                print(command)
                if len(command) < 2:
                    continue
                if command[1] == TEAM_ID:
                    if command[2] == "SIMP":
                        alt_pressure = uint16_t(command[3])
                        CMD_ECHO = "SIMP_" + command[3]
                        SIMP_FLAG = True
                    elif command[2] == "CX":
                        CX_ON = True if command[3] == "ON" else False
                        CMD_ECHO = "CX_ON" if command[3] == "ON" else "CX_OFF"
                    elif command[2] == "BCN":
                        BCN_ON = True if command[3] == "ON" else False
                        CMD_ECHO = "BCN_ON" if command[3] == "ON" else "BCN_OFF"
                    elif command[2] == "SIM":
                        if command[3] == "ACTIVATE":
                            SIM_ACTIVATE = True
                            CMD_ECHO = "SIM_ACTIVATE"
                        elif command[3] == "ENABLE":
                            SIM_ENABLE = True
                            CMD_ECHO = "SIM_ENABLE"
                        else:
                            SIM_ACTIVATE, SIM_ENABLE = False, False
                            CMD_ECHO = "SIM_DISABLE"
                    elif command[2] == "CAL":
                        CAL = True
                        CMD_ECHO = "CAL"
                    elif command[2] == "ST":
                        if command[3] == "GPS":
                            pass
                        else:
                            pass
                status_received.toggle()
                time.sleep_ms(10)
                status_received.toggle()

            await asyncio.sleep_ms(SLEEP_PERIOD)
        except Exception as e:
            print(e)
#***********************/ Main Flight Software *******************************#
flight_mode = True
mode= ["S", "F"]

async def FS_main():
    global alt_pressure, altitude, record, packet, CAL, flight_mode, cal_offset, SLEEP_PERIOD
    while True:
        # Buzzer Manual Input
        buzzer.value(BCN_ON)
        # Calibration of sensors
        if CAL:
            bmp.get_compensated(i2c)
            cal_offset = bmp.data.P_LIN - 101325.0
            CAL = False
        # Main Flight or Simulation Functions
        if CX_ON:
            # Decide where to get altitude data from
            record = True
            SLEEP_PERIOD = 500
            bmp.get_compensated(i2c)
            if SIM_ACTIVATE and SIM_ENABLE: # Get pressure from SIMP Command
                flight_mode = False
                # Alt pressure gets set in command
                while not SIMP_FLAG:
                    await asyncio.sleep_ms(100)
                SIMP_FLAG = False
            else:
                flight_mode = True
                alt_pressure = bmp.data.P_LIN

            # Calculate Altitude
            altitude = calculate_altitude(alt_pressure)
            # Convert to kPa
            alt_pressure = alt_pressure/1000
            # Determine State
            det_state()
            await asyncio.sleep_ms(100)
            # Send Package
            packet += 1
            if not await asyncio.create_task(send_packet()):
                packet -= 1
        else:
           record = False
           status_ready.toggle()
           await asyncio.sleep_ms(500)

# *******************************************************************************
async def main(): # Scheduler for FSW
   command_collect = asyncio.create_task(collect_command())
   fs = asyncio.create_task(FS_main())
   video_task = asyncio.create_task(record_video())

   await command_collect
   await fs
   await video_task



# Run the main coroutine
asyncio.run(main())

