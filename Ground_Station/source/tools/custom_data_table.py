from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout

from kivymd.uix.datatables import MDDataTable
from kivymd.uix.boxlayout import MDBoxLayout
import csv

# TODO Customize to fit our needs:
class CustomDataTable(MDBoxLayout):
    
    row_data = []
    
    mainDict = {
        "team_id": [],
        "mission_time": [],
        "packet_count": [],
        "flight_mode": [],
        "flight_state": [],
        "altitude": [],
        "air_speed": [],
        "hs_deployed": [],
        "pc_deployed": [],
        "temperature": [],
        "voltage": [],
        "pressure": [],
        "GPS_time": [],
        "GPS_altitude": [],
        "GPS_latitude": [],
        "GPS_longitude": [],
        "GPS_sats": [],
        "tilt_x": [],
        "tilt_y": [],
        "rot_z": [],
        "CMD_ECHO": [],
        }

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.parseData(r"Ground_Station\_flight_recordings\_flight-record_admin_.csv")
        self.showData()
        # while 1:
        #     pass
        
        data_tables = MDDataTable(
            size_hint=(0.9, 0.6),
            column_data=[
                ("Packet Number", dp(20)),
                ("Flight State", dp(30)),
                ("Altitude", dp(50), self.sort_on_col_3)
            ],
            row_data= self.row_data
                #The number of elements must match the length
                #of the `column_data` list.
                #just make columns mimic the showdata function
                # (
                #     "1",
                #     ("alert", [255 / 256, 165 / 256, 0, 1], "No Signal"),
                #     "Astrid: NE shared managed",
                #     "Medium",
                #     "Triaged",
                #     "0:33", 
                #     "Chase Nguyen",
                
        )
        self.add_widget(data_tables)
        

    def sort_on_col_3(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][3]
            )
        )

    def sort_on_col_2(self, data):
        return zip(
            *sorted(
                enumerate(data),
                key=lambda l: l[1][-1]
            )
        )
    #Definition of Parsing Function
    def parseData(self,dataFile:str):
        #Opens CSV File given in argument as a readfile
        with open(f"{dataFile}", 'r') as csvfile:
            #initializes the reading of the csvfile
            csvreader = csv.reader(csvfile)
            #Iterates through each row of the csv file
            for row in csvreader:
                i = 0
                #Iterates through each key in the Dict
                #(DICTIONARY MUST EXACTLY COPY DATA IN CSV)
                for key in self.mainDict:
                    self.mainDict[key].append(row[i])
                    i += 1

    def showData(self):
        i = 0
        self.row_data.append((self.mainDict["packet_count"][i], 
                              self.mainDict["flight_state"][i], 
                              self.mainDict["altitude"][i], 
                              ))
        for i in range(len(self.mainDict["flight_state"]) - 1):

            if self.mainDict["flight_state"][i] == self.mainDict["flight_state"][i + 1]:
                continue
            else:
                self.row_data.append((self.mainDict["packet_count"][i + 1], 
                                      self.mainDict["flight_state"][i + 1], 
                                      self.mainDict["altitude"][i + 1]
                                      ))