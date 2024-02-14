"""
# ! ***************************************************
*             The University of Florida               *
*             Space Systems Design Club               *
*                     CanSat 2024                     *
*                        Team:                        *
*                     Authored by:                    *
*    Leandro Sanchez,                                 *
# ! ***************************************************
"""
import os
import csv
import serial
import queue
import serial.tools.list_ports

from datetime import datetime
from threading import Thread
import time

def find_serial_port(): 
    # * Returns a list of comports available in the machine
    list_of_ports = []
    for item in serial.tools.list_ports.comports():
        list_of_ports.append(str(item))
    return list_of_ports
        

class SerialObject():
    # The class SerialObject is being defined.
    data_container = []
    new_data = False

    def __init__(
            self, 
            port,           
            BAUDERATE = 9600, 
            TIMEOUT = 1, 
            XONXOFF = True,
            team_member_id = "2062",
            comp = False,
            json_args = None,
            max_data_points = 500,
            **kwargs
        ):
        super(SerialObject, self).__init__(**kwargs)
        # ! This is the initialization function for a class that sets up a serial connection and creates a
        # ! container for collected data while recording it to a csv.
        
        # * :param port: The serial port to connect to

        # * :param BAUDERATE: The baud rate at which the serial communication will take place. It is set to
        # * a default value of 9600 if not specified, defaults to 9600 (optional)

        # * :param TIMEOUT: The TIMEOUT parameter is the time in seconds that the serial port will wait for
        # * data before timing out. If no data is received within this time, the port will return an empty
        # * string, defaults to 1 (optional)

        # * :param XONXOFF: XONXOFF is a boolean parameter that enables or disables software flow control
        # * using XON/XOFF characters. When enabled, the serial device will send XOFF to the sender when its
        # * receive buffer is almost full, and XON when the buffer is ready to receive more data. This helps
        # * prevent data, defaults to True (optional)

        # * :param team_member_id: A string representing the team member's ID, defaults to admin (optional)

        # * :param comp: The `comp` parameter is a boolean flag that indicates whether the program is
        # * saving a file for development or competition. It is used to determine the file path for saving
        # * flight recordings. If `comp` is `False`, the file path will include the team member ID and the
        # * current date, and, defaults to False (optional). Otherwise it will be named according to the specification
        # * of the cometions

        # * :param json_args: A dictionary containing information about the data to be collected from the
        # * serial port. It includes a list of collectable data items

        # * :param max_data_point: The maximum amount of data points the queueu will use. 

        # * :return: The function may return None or may not return anything, depending on the execution path.
        self.team_member = team_member_id                      # A recording will be made of everyone who uses 
                                                               # this program. 
        self.args = json_args
        if port:                                               # Initialize the Serial port that will be used
            self.is_on, self.first_start = False, False
            self.serial_connection = False
            self.max_data = max_data_points
            self.current_data_size = 0
            try: 
                self.serialPort = serial.Serial(
                                    port = port,
                                    baudrate=BAUDERATE,  
                                    timeout= TIMEOUT, 
                                    xonxoff=XONXOFF
                                    )
                self.serial_connection = True
            except serial.SerialException as b:
                print(f'Serial Port not available: Error:(0001) \n {b}')
                return
            except Exception as e:
                print(e)
                return
            finally:
                self.collectable_data = {}
                self.gps_single_container = []
                for item in self.args['collectable_data']:
                    self.collectable_data[item] = []
                
           # This code block is setting the file path for saving flight recordings. If `comp` is
           # `False`, the file path will include the team member ID and the current date, and if
           # `comp` is `True`, it will be named according to the specification of the competitionn
            if not os.path.isdir(r'Ground_Station/_flight_recordings'):
                os.mkdir(r'Ground_Station/_flight_recordings')
            if comp is False:
                self.file_path = f'Ground_Station/_flight_recordings/flight-record_{team_member_id}_.csv'
            else:
                self.file_path = r'Ground_Station/_flight_recordings/' # TODO Add correct name based on competition
        else: 
            print("Include a serial port")
            return
        
        
        

    def ReadSerialData(self):
        """
        This function reads serial data from a port and handles the incoming data.
        """
        # This code block is opening a file at the specified `self.file_path` location in write mode
        # (`'w'`). It then enters a while loop that continuously checks if there is any data waiting
        # to be read from the serial port. If there is data waiting, it reads the data from the serial
        # port, decodes it from bytes to a string using the `decode()` method, removes any trailing
        # whitespace using the `rstrip()` method, and passes the resulting string to the
        # `HandleIncomingData()` method for processing. The `with` statement ensures that the file is
        # properly closed after the loop is exited. 
        # ! CSV file will not close until end of program, but will add data into file after every read to ensure 
        # ! data is not lost
        try:
            # Protect file from fatal error
            with open(self.file_path, 'w', newline='') as self.file:
                while self.is_on:
                    try:
                        if self.serialPort.in_waiting > 0:
                            data = self.serialPort.readline().decode('utf-8').rstrip()
                            self.HandleIncomingData(data)                  
                    except Exception as e:
                        self.is_on = False
                        print(f'Serial device disconnected or lost communication Error: (0002) \n {e}')
        except Exception as n:
            print(n)

    def WriteSerialData(self,command = "", data_to_write = "", alt = True, full_command = None):
        """
        This function writes serial data to a port, with the option to include a command and team ID.
        
        * :param command: The command to be sent over the serial port. It could be a string or a number
        * depending on the protocol being used

        * :param data_to_write: The data that needs to be written to the serial port

        * :param alt: A boolean parameter that specifies whether to use an alternative format for writing
        * serial data. If set to True, the function will use the format
        * 'CMD,{teamId},{command},{data_to_write}' to write the data to the serial port. 
        * If set to False, it will use the format '{command, defaults to False (optional)
        """
        if full_command:
            self.serialPort.write(full_command.encode('utf-8'))
        if alt:
            self.serialPort.write(f'CMD,{self.args["team_ID"]},{command},{data_to_write}\n'.encode('utf-8'))
        else:
            self.serialPort.write(f'{command},{data_to_write}'.encode('utf-8'))

    def InitMicroController(self):
        # TODO Function for emergency reinitialization. 

        pass
    
    def ResetData(self):
        self.gps_single_container = []
        # TODO Find a way to completely erase all of the info in the container.
        for item in self.args['collectable_data']:
            self.collectable_data[item].clear()
        self.current_data_size = 0
    
    def get_serial_data(self):
        return self.data_container

    def HandleIncomingData(self, data = None):
        """
        This function handles incoming data by splitting it, putting it into a list, writing it to
        a CSV file, and flushing the file.
        
        * :param data: The data parameter is an optional input to the HandleIncomingData method. It is
        * expected to be a string containing comma-separated values that will be processed and stored in a
        * dictionary and a CSV file. If data is not provided or is an empty string, the method will not
        * execute any further
        """
        if data.startswith("1071"):

            self.data_container = data.split(",")

            for key, value in self.args['collectable_data'].items():
                
                self.collectable_data[key].append(float(self.data_container[value]))  
            
            temp = self.args['GPS']
            self.gps_single_container.append((float(self.data_container[temp["lat"]]),
                                              float(self.data_container[temp["lon"]])))
            
            self.new_data = not self.new_data
            self.current_data_size += 1  
            
            csv.writer(self.file).writerow(self.data_container)       # Make sure data is not lost in case of failure
            self.file.flush()
            os.fsync(self.file.fileno())
        else:
            pass

    def StartSerialObject(self):
        """
        This function starts a serial object and reads data from it in a separate thread if the serial
        port is open.
        """
        if not self.is_on: 
            # The above code is checking if a serial port is open. If it is open, it sets a flag
            # `is_on` to True and starts a new thread to read data from the serial port using the
            # `ReadSerialData` method. If the serial port is not open, it sets the `is_on` flag to
            # False.
            try:
                if self.serialPort.is_open:
                    
                    self.is_on = True
                    self.first_start = True
                    self.serial_read_thread =  Thread(
                                                target = self.ReadSerialData,
                                                daemon= True
                                                )
                    self.serial_read_thread.start()
                    
                else:
                    self.is_on = False
            except AttributeError as a:
                print(f'Serial Port was not correctly configured, Error: (0000)\n {a}')   
            except Exception as e:
                print(e)
                print("Serial Failed to start for reason:")

    def StopSerialObject(self, hard_stop = False):
        """
        The function stops a serial port and can either stop the whole program or just the thread.
        
        :param hard_stop: A boolean variable that determines whether to stop the whole program or just
        the thread. If it is set to True, the function will raise a BaseException, which will stop the
        entire program. If it is set to False, only the thread will be stopped, defaults to False
        (optional)
        """
        self.is_on = False
        self.serial_read_thread.join()
        self.current_data_size = 0
        if hard_stop:
            raise BaseException
        
    def GetPortInfo(self):

        # * The code below is defining a dictionary `serialPort_info` that contains information about a
        # * serial port. The information includes the name of the port, the baudrate, whether XON/XOFF
        # * flow control is enabled, the number of stop bits, and the parity setting. The code then
        # * returns this dictionary.

        serialPort_info = [
            self.serialPort.name,
            self.serialPort.baudrate,
            self.serialPort.xonxoff,
            self.serialPort.stopbits,
            self.serialPort.parity
        ]
        return serialPort_info
        
        
class SimulationObject:
    command_array = []
    bird = None
    internal_thread = None
    kill_thread = False
    launch = False
    def __init__(
            self, 
            bird:SerialObject = None,
            simulation_param = r"Ground_Station\_sim_file\cansat_2023_simp.txt",
            internal_thread = None,
            **kwargs
        ):
        super(SimulationObject, self).__init__(**kwargs)
        self.bird = bird
        
        # Break Down .txt file and store in command_array for transmission.
        with open(simulation_param,'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith("CMD"):
                self.command_array.append(line.replace('$', "2062"))
                
    def ActivateSimObj(self):
       # The above code is creating a new thread and starting it. The thread is created with the
       # target function `self.SimObj_main` and is set as a daemon thread.
        try:
            if self.internal_thread is None:
                # ! If there is no thread, create a thread to control flow of program.
                self.internal_thread =  Thread(
                                                target = self.SimObj_main,
                                                daemon= True
                                                )
                self.internal_thread.start()
                
        except Exception as e:
            print(e)
            
    def SimObj_launch(self, status:bool = False):
        self.launch = status
     
    def SimObj_main(self):
        # Wait for launch command to be issued
        while(not self.launch): pass
        
        for command in self.command_array:
            # Allows us to stop sim mode at any point and kill the thread when we choose
            while(not self.launch and not self.kill_thread): pass
        
            if not self.kill_thread:
                if self.bird is not None:
                    print(command) #TODO Change this to a bird write command
                    time.sleep(2)  # Instead of time_sleep, ideally we check for new_data       
            else:
                break

    def Kill_SimObj(self):
        self.kill_thread = True
        self.internal_thread.join() 
    
    def __del__(self):
        print('Sim Object Deleted')
        

        
        
   