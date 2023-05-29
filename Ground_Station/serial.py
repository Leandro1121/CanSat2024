import serial
import queue
import threading 

shared_data = queue.Queue()
try:
    ser = serial.Serial(
        port = ports[int(port_num)].name,
        #port='/dev/tty.usbserial-D30AXZ1V',  # Update this with the correct serial port of your device
        baudrate=9600,  # Update this with the correct baud rate of your device
        timeout=1,  # Timeout value in seconds
        xonxoff=True
        # /dev/tty.usb* mac command
    )
    if ser.is_open:
        print('Serial open')
        # Start the thread to read data from the serial port
        t = threading.Thread(target=read_serial, args=(flight_states, states,
                                                        hc_bool_states, mast_bool_states,
                                                        pc_bool_states, flight_mode_states,))
        t.daemon = True
        t.start()
        after_conneciton = True
except Exception as e:
    after_conneciton = False
    print(e)


hc_bool_states = {
    'N': False,
    'P': True,
}
pc_bool_states = {
    'N': False,
    'C': True,
}
mast_bool_states = {
    'N': False,
    'M': True
}
flight_mode_states = {
    'F': False,
    'S': True
}
states = {
    "LAUNCH_WAIT": 0,
    "ASCENT": 1,
    "ROCKET_SEPARATION": 2,
    "DESCENT1": 3,
    "PROBE_RELEASE": 4,
    "DESCENT2": 5,
    "PARACHUTE_DEPLOY": 6,
    "DESCENT3": 7,
    "LANDED": 8,
    "LANDED_WAIT": 9
}

flight_states = {
    "start_payload": False,
    "flight_mode": False,
    "hc_bool": False,
    "pc_bool": False,
    "mast_bool": False,
    "state": 0,
    "packet_count": 0,
    "mission_time": 0

}

# Function to handle incoming data
def handle_data(data, flight_states,
                states, hc_bool_states, mast_bool_states, pc_bool_states, flight_mode_states):
    # Do something with the received data
    # @TODO Figure out start
    teamID = "1071"
    if data.find(teamID, 0, len(teamID)) == -1:
        package_count = flight_states["packet_count"]
        num_states = 0b000000
        num_states |= (flight_states["start_payload"] << 0)
        num_states |= (flight_states["hc_bool"] << 1)
        num_states |= (flight_states["pc_bool"] << 2)
        num_states |= (flight_states["mast_bool"] << 3)
        num_states |= (flight_states["flight_mode"] << 4)
        num_states |= (flight_states["state"] << 5)
        cmd = f"{teamID},5,0,{num_states},{package_count}"
        ser.write(cmd.encode('utf-8'))
        _VARS['window']['echo'].update('Command Echo: Satellite Ready')
    else:
        shared_data.put(data)
        data_cont = data.split(",")
        # Save necessary flight states and info in
        # case of defect
        try:
            flight_states["state"] = states[data_cont[4]]
            flight_states["hc_bool"] = hc_bool_states[data_cont[6]]
            flight_states["pc_bool"] = pc_bool_states[data_cont[7]]
            flight_states["mast_bool"] = mast_bool_states[data_cont[8]]
            flight_states["packet_count"] = data_cont[2]
            flight_states["flight_mode"] = flight_mode_states[data_cont[3]]
            temp_time = data_cont[1].split(':')
            flight_states["mission_time"] = int(temp_time[0]) * 3600 + int(temp_time[1]) * 60 + int(temp_time[2])

        except IndexError:
            pass

def read_serial(flight_states, states, hc_bool_states,
                mast_bool_states, pc_bool_states, flight_mode_states):
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').rstrip()
            # Call the handle_data function to process the received data
            handle_data(data, flight_states, states,
                        hc_bool_states, mast_bool_states,
                        pc_bool_states, flight_mode_states)

data = shared_data.get()
