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
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.list import OneLineAvatarIconListItem

from kivy_garden.mapview import MapMarker, MapSource
from kivy_garden.graph import LinePlot

from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

from tools.map_overlay import LineMapLayer
from tools.gui_serial import SerialObject, SimulationObject
from tools.gui_serial import find_serial_port
from tools.json_FR import read_json

from datetime import datetime

json_args_ = read_json()
flight_vals = json_args_['flight_vals']
collectables = json_args_['collectable_data']
current_checked_port = None

class GCSPage(MDScreen):
    # ! Dialog Start values must be set to None to be initialized, otherwise when
    # ! when selecting from nav bar, buttons will fail
    setup_dialog = None
    opt_cmd_dialog = None
    sim_dialog = None
    start_dialog = None
    cal_dialog = None
    bird = None
    new_data = BooleanProperty(False)
    graph_offset = NumericProperty(0)
    audio_on = False
    mission_time_curr = StringProperty(datetime.now())
    sim_mode_active = False
    sim_mode_enabled = False
    sim_mode_active_gui = True
    sim_mode_enabled_gui = False
    SimObj = None
    # ! Zoom Values
    zoom_alt = NumericProperty(1)
    zoom_temp = NumericProperty(1)
    zoom_air_speed = NumericProperty(1)
    zoom_voltage = NumericProperty(1)
    zoom_gyro = NumericProperty(1)
    # ! Navbar Tool Properties
    disable_tools = BooleanProperty(True)
    list_size = NumericProperty(0)
    # ! Individual Tool Disabling
    reset_tool = BooleanProperty(True)
    audio_tool = BooleanProperty(False)
    sim_tool = BooleanProperty(False)
    cal_tool = BooleanProperty(False)
    # ! Graphing Properties
    x_max = NumericProperty(60)
    my_coordinates = []
    gps_plot = None
    # ! Graph Plots
    alt_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    volt_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    air_speed_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    
    temp_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    
    rotz_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    tiltx_plot = LinePlot(color = [1, 0, 1, 1], line_width=1.5)
    tilty_plot =  LinePlot(color = [0, 1, 1, 1], line_width=1.5)
    
    def __init__(self, *args, **kwargs):
        super(GCSPage, self).__init__(*args, **kwargs)
        
    def update(self, instance):
        self.ids.mission_time_curr.text = "Mission Time:[color=ff0000]{}[/color]"\
            .format(datetime.utcnow().strftime("%H:%M:%S"))
        if self.bird:
            # * Check to see offset between GUI and backend Serial proccessing.
            # * Data change triggers event, unless something happans 
            # * Event should normally not be triggered 
            self.graph_offset = self.bird.current_data_size - self.list_size
            # * If there is a change in value an event is triggered -> on_new_data
            self.new_data = self.bird.new_data
        
    def backend_binds(self):
        # ! Binding methods to any action that can't be bound in the 
        # ! the kivy LANG file
        self.bind(list_size=self.auto_size)
        
    def on_pre_enter(self):
        # ! Actions the page has to do before going into
        self.backend_binds()
        self.format_flight_vals()
        self.ids.gps_map.map_source = MapSource(max_zoom = 15, min_zoom = 2)
            
    def on_enter(self):
        # ! When entering, Initialize the page to refresh at 2 Hz
        Clock.schedule_interval(self.update, 0.5)

        # ! Create the Plot for the GPS once you have netered the page.
        # ! Reasoning: The LineMapLayer must take a set of coordinates
        # ! which get initialized after the kivy LANG file
        
    
    def play_sound(self, flight_state:str):
        # TODO: Convert this into an event connecting it to the flight states as an event
        # ! This function plays the sound when the flight state changes.
        sound = SoundLoader.load(f'Ground_Station\_recorded_audio\{flight_state}.mp3')
        if sound:
            print("Sound found at %s" % sound.source)
            print("Sound is %.3f seconds" % sound.length)
            sound.play()    
        
    def on_exit(self):
        # ! Removing the refreshing of the gcs pages
        Clock.unschedule(self.update)  
            
    def auto_size(self, instance, value):
        # ! This function keeps the graphs as small as possible
        # TODO: Decide if we want to keep all the data or keep a certain number if it
        if self.list_size >= self.x_max - (self.x_max/4):
            self.x_max += round(self.x_max/2)
            
    def on_graph_offset(self, instance, value):
        # ! Setting an acceptable offset as 5
        """
        The main purpose behind this function is if the app hangs up, the serial connection 
        in the background continues to collect data and both will be out of sync,
        Once the app returns to normal function, this app will be called and the entire plot will be redone 
        to ensure that all plots are correct
        """
        if value >= 3:
            self.alt_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['altitude'])]
            self.air_speed_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['air_speed'])]
            self.volt_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['voltage'])]
            self.temp_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['temperature'])]
            self.rotz_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['rot_z'])]
            self.tiltx_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['tilt_x'])]
            self.tilty_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['tilt_y'])]
            
            self.list_size = self.bird.current_data_size
            self.plot_data()
            
    def on_new_data(self, instance, value):
        # ! Call helper function to modify all plotted variables 
        self.modify_header_flight_vars(data = self.bird.get_serial_data())
        
        self.alt_plot.points.append((self.list_size,self.bird.collectable_data['altitude'][-1]))
        self.air_speed_plot.points.append((self.list_size,self.bird.collectable_data['air_speed'][-1]))
        self.volt_plot.points.append((self.list_size,self.bird.collectable_data['voltage'][-1]))
        self.tiltx_plot.points.append((self.list_size,self.bird.collectable_data['tilt_x'][-1]))
        self.tilty_plot.points.append((self.list_size,self.bird.collectable_data['tilt_y'][-1]))
        self.rotz_plot.points.append((self.list_size,self.bird.collectable_data['rot_z'][-1]))
        self.temp_plot.points.append((self.list_size,self.bird.collectable_data['temperature'][-1]))
        self.my_coordinates.append(self.bird.gps_single_container[-1])
        self.ids.current_loc.text = \
            "Payload Location: [color=ffff00]{}[/color]" \
                .format(self.my_coordinates[-1])
                
        if self.gps_plot is None: self.create_maplayer()  
        
        self.list_size += 1
        self.plot_data()
        
        if self.sim_mode_active and self.sim_mode_enabled:
            self.SIM_MODE()
            
    def create_maplayer(self):
        # ! Creates Map Layer and Map Maker of the first spot used for graphing at the first instance of
        # ! new data
        self.gps_plot = LineMapLayer(coordinates=self.my_coordinates,
                                     color=[1, 0, 0, 1])
        self.ids.gps_map.add_layer(self.gps_plot, mode="scatter")
        self.ids.gps_map.add_marker(MapMarker(lat=self.my_coordinates[-1][0],
                                              lon=self.my_coordinates[-1][1]))  
        
    def plot_data(self):
        # ! RePlot and/or Trigger GPS to Update
        self.ids.alt.add_plot(self.alt_plot)
        self.ids.gyro.add_plot(self.tiltx_plot, self.tilty_plot)
        self.ids.air_speed.add_plot(self.air_speed_plot)
        self.ids.temp.add_plot(self.temp_plot)
        self.ids.gps_map.trigger_update(True)
        self.ids.voltage.add_plot(self.volt_plot)
        
    def reset(self):
        # ! This function resets all plots and backend serial containers
        if self.bird:
            self.bird.ResetData()
            self.ids.alt.remove_plot(self.alt_plot)
            #self.ids.gyro.remove_plot(self.gyro_plot)
            self.ids.air_speed.remove_plot(self.air_speed_plot)
            self.ids.temp.remove_plot(self.temp_plot)
            self.ids.gps_map.trigger_update(True)
            self.ids.voltage.remove_plot(self.volt_plot)
           
      
    def modify_header_flight_vars(self, data:dict):
        # ! This Method modifies all headers in the GCS
        self.ids.packet_count.text = \
            "Packet Count: [color=ff0000]{}[/color]".format(data[flight_vals['packet_count']])

        self.ids.flight_mode.text = \
            "Flight Mode: [color=ff0000]{}[/color]".format(data[flight_vals['flight_mode']])
        
        self.ids.flight_state.text = \
            "Flight State: [color=ff0000]{}[/color]".format(data[flight_vals['flight_state']])
       
        self.ids.gps_time.text = \
            "GPS Mission Time: [color=ff0000]{}[/color]".format(data[flight_vals['GPS_time']])
        
        self.ids.pc_release.text = \
            "PC Release: [color=ff0000]{}[/color]".format(data[flight_vals['pc_deployed']])

        self.ids.hs_release.text = \
            "HS Release: [color=ff0000]{}[/color]".format(data[flight_vals['hs_deployed']])
        
        self.ids.cmd_echo.text = \
            "CMD ECHO: [color=ff0000]{}[/color]".format(data[flight_vals['CMD_ECHO']])
       
        self.ids.gps_sats.text = \
            "GPS Sats: [color=ff0000]{}[/color]".format(data[flight_vals['GPS_sats']])
            
   
    def on_touch_up(self, touch):
        # ! Getting Selected Coordinates
        if self.ids.gps_map.collide_point(*touch.pos):
            temp_loc=self.ids.gps_map.get_latlon_at(touch.x,
                                                    touch.y,
                                                    zoom = self.ids.gps_map.zoom)
            temp_loc = [round(item,4) for item in temp_loc]
            self.ids.selected_loc.text = \
                "Selected Location: [color=ff0000]{}[/color]".\
                    format(temp_loc)
            
    def format_flight_vals(self):
        # ! This function is called once to format variables
        # ! Reasoning: The change of font and using this kind of markup format
        # ! causes problems for kivy LANG, the work around is to do it here. 
        
        self.ids.mission_time_start.markup = True
        self.ids.current_loc.markup = True
        self.ids.selected_loc.markup = True 
        self.ids.gps_time.markup = True
        
        self.ids.mission_time_curr.markup = True
        self.ids.mission_time_curr.text = "Mission Time:[color=ff0000]{}[/color]"\
            .format(datetime.utcnow().strftime("%H:%M:%S"))
        
        self.ids.packet_count.markup = True
        self.ids.packet_count.text = "Packet Count: [color=ff0000]{}[/color]".format(0)
        
        self.ids.flight_mode.markup = True
        self.ids.flight_mode.text = "Flight Mode: [color=ff0000]{}[/color]".format("F")
        
        self.ids.flight_state.markup = True
        self.ids.flight_state.text = "Flight State: [color=ff0000]{}[/color]".format("NA")
        
        self.ids.sim_mode.markup = True
        self.ids.sim_mode.text = "SIM Mode: [color=ff0000]{}[/color]".format("DISABLED")
        
        self.ids.gps_sats.markup = True
        self.ids.gps_sats.text = "GPS Sats: [color=ff0000]{}[/color]".format(0)
        
        self.ids.pc_release.markup = True
        self.ids.pc_release.text = "PC Release: [color=ff0000]{}[/color]".format("N")
        
        self.ids.hs_release.markup = True
        self.ids.hs_release.text = "HS Release: [color=ff0000]{}[/color]".format("N")
        
        self.ids.cmd_echo.markup = True
        self.ids.cmd_echo.text = "CMD ECHO: [color=ff0000]{}[/color]".format("NA")
        
        self.ids.status.markup = True
        self.ids.status.text = "Status: [color=ff0000]{}[/color]".format("Not Ready")
        
    # ! Dialog Tools- These dialogs are used to give the applications it's functionality
    
    # * Calibrate Dialog - Calibrate the necessary parts of the Container and Payload
    
    def cal_dialog_func(self):  
        if not self.cal_dialog: 
            self.cal_dialog = MDDialog(
                title="Calibrate Payload",
                text="""
                [color=ff0000]CAL[/color]: Calibrate Altitude\n 
                [color=ff0000]ST-Time[/color]: Calibrate using GCS Time\n 
                [color=ff0000]ST-GPS[/color]: Calibrate using GPS Time 
                """,
                buttons=[
                    MDRaisedButton(
                        text="CAL",
                        theme_text_color="Custom",
                        on_release= self.cal_dialog_helper
                    ),
                    MDRaisedButton(
                        text="ST-Time",
                        theme_text_color="Custom",
                        on_release= self.st_time_dialog_helper
                    ),
                    MDRaisedButton(
                        text="ST-GPS",
                        theme_text_color="Custom",
                        on_release= self.st_gps_dialog_helper
                    ),
                ],
            )
        self.cal_dialog.open()
    def cal_dialog_helper(self,instance):
        # TODO: Send the command to calibrate device
        self.bird.WriteSerialData(command="CAL")
        print("Calibrate")
    def st_time_dialog_helper(self,instance):
        # TODO: Send the command to callibrate mission time based on current mission time
        self.bird.WriteSerialData(command="ST", data_to_write= datetime.utcnow().strftime("%H:%M:%S"))
        print("time")
    def st_gps_dialog_helper(self,instance):
        # TODO: Send the command to callibrate the payload based on gps time 
        self.bird.WriteSerialData(command="ST", data_to_write="-1")
        print("gps")
        
    # * Launch Dialog - Used to start and end transmission of the Container and Payload
    def start_dialog_func(self):  
        if not self.start_dialog: 
            self.start_dialog = MDDialog(
                title="Start Launch",
                text="These are the settings to activate payload transmisson",
                buttons=[
                    MDRaisedButton(
                        text="START",
                        theme_text_color="Custom",
                        on_release= self.start_dialog_helper
                    ),
                    MDFlatButton(
                        text="END",
                        theme_text_color="Custom",
                        on_release= self.end_dialog_helper
                    ),
                ],
            )
        self.start_dialog.open()
        
    def start_dialog_helper(self,instance):
        # ! Function Starts Recording Data
        self.ids.mission_time_start.text = "Mission Time Start: [color=ff0000]{}[/color]"\
            .format(datetime.utcnow().strftime("%H:%M:%S.%f")[:-4])
        # TODO Comment this out when not testing out
        #self.bird.StartSerialObject()
        self.bird.WriteSerialData(command="CX", data_to_write="ON")
        if self.sim_mode_enabled and self.sim_mode_active: self.SimObj.SimObj_launch(True)
        self.ids.analysis_tool.disabled = True
        self.ids.home_icon.disabled = True
        self.audio_tool, self.reset_tool, self.cal_tool, self.sim_tool = True, True, True, True
        self.start_dialog.dismiss()
        
    def end_dialog_helper(self,instance):
        # ! Function to end recording Data
        self.bird.StopSerialObject()
        # TODO: Make sure this command is untimately correct for payload
        self.bird.WriteSerialData(command="CX", data_to_write="OFF")
        self.audio_tool, self.reset_tool, self.cal_tool, self.sim_tool = False, False, False, False
        
        # * Add a marker to where the Payload landed
        self.ids.gps_map.add_marker(MapMarker(lat=self.my_coordinates[-1][0],
                                              lon=self.my_coordinates[-1][1]))
        self.ids.analysis_tool.disabled = False
        self.ids.home_icon.disabled = False
        if self.sim_mode_enabled and self.sim_mode_active: self.SimObj.SimObj_launch(False)
        self.start_dialog.dismiss()
        
    # * ================== SIM Dialog and tools =====================
    def sim_dialog_func(self):  
        if not self.sim_dialog: 
            self.sim_dialog = MDDialog(
                title="Simulation Mode",
                text="These are the settings to activate simulation mode",
                buttons=[
                    
                    MDRaisedButton(
                        text="ENABLE",
                        theme_text_color="Custom",
                        on_release= self.sim_enable_helper,
                        disabled= self.sim_mode_enabled_gui
                    ),
                    MDRaisedButton(
                        text="ACTIVATE",
                        theme_text_color="Custom",
                        on_release= self.sim_activate_helper,
                        disabled = self.sim_mode_active_gui
                    ),
                    MDFlatButton(
                        text="DISABLE",
                        theme_text_color="Custom",
                        on_release= self.sim_disable_helper
                    ),
                ],
            )
        self.sim_dialog.open()
        
    def sim_enable_helper(self,instance):
        #self.bird.WriteSerialData("SIM", "ENABLE") TODO uncomment
        self.ids.sim_mode.text = "SIM Mode: [color=ffff00]{}[/color]".format("ENABLED")
        self.sim_mode_enabled = True
        self.SimObj = SimulationObject()
        
        self.bird.WriteSerialData(command="SIM", data_to_write="ENABLE")
        # TODO: Write command that is necessary to send enable message
    def sim_activate_helper(self,instance):
        # self.bird.WriteSerialData("SIM", "ACTIVATE") TODO uncomment
        self.ids.sim_mode.text = "SIM Mode: [color=00ff00]{}[/color]".format("ACTIVATED")
        self.sim_mode_active = True
        if self.SimObj is not None: self.SimObj.ActivateSimObj();
    
        self.bird.WriteSerialData(command="SIM", data_to_write="ACTIVATE")
        # TODO: Write command that is necessary to send activate message
    def sim_disable_helper(self,instance):
        # self.bird.WriteSerialData("SIM", "DISABLE") TODO uncomment
        self.ids.sim_mode.text = "SIM Mode: [color=ff0000]{}[/color]".format("DISABLED")
        self.sim_mode_active, self.sim_mode_enabled = False,False
        if self.SimObj is not None:
            self.SimObj.Kill_SimObj()
            del self.SimObj
        self.bird.WriteSerialData(command="SIM", data_to_write="DISABLE")
        # TODO: Write command that is necessary to send disable message
        self.sim_dialog.dismiss()
        
    # * Optional Command Dialog - Send optional commands
    def optional_cmd_dialog_func(self):
        content_cls = Content()
        if not self.opt_cmd_dialog:
            self.opt_cmd_dialog = MDDialog(
                title="Optional Command:",
                type="custom",
                content_cls=content_cls,
                buttons= [
                    MDRaisedButton(
                        text= "SEND",
                        on_release= lambda x:self.get_data(x,content_cls)
                    )
                ]
            )
        self.opt_cmd_dialog.open()
        
    def get_data(self, instance, content_cls):
        textfield = content_cls.ids.command_field
        value = textfield._get_text()
        # TODO: Make sure the command is written correctly 
        self.bird.WriteSerialData(value)
        
    # * ================== Setup Dialog and tools =================== 
           
    def setup_dialog_func(self):
        self.setup_dialog = None
        if not self.setup_dialog:
            self.setup_dialog = MDDialog(
                title="Select CanSat Connection",
                type="confirmation",
                items=self.open_ports(),
                buttons=[
                    MDRaisedButton(
                        text="Connect",
                        theme_text_color="Custom",
                        on_release = self.establish_connection
                    ),
                ],
            )
        self.setup_dialog.on_enter = self.setup_dialog.update_items(self.open_ports())
        self.setup_dialog.open()
            
    def open_ports(self):
        # ! Finds all the open ports on the computer 
        ports_list = find_serial_port()
        item_list = []
        for item in ports_list:
            item_list.append(ItemConfirm(text= item))
        return item_list
    
    def establish_connection(self, instance):
        if self.bird is None:
            self.bird = SerialObject(port=current_checked_port, json_args=json_args_)
            self.ids.status.text = "Status: [color=00ff00]{}[/color]".format("Ready")
            self.disable_tools = False
        elif self.bird.serial_connection is False:
            self.bird = SerialObject(port=current_checked_port, json_args=json_args_)
        # TODO: Uncomment this because the app is supposed to start looking for data as soon as it opens
        #self.bird.StartSerialObject()
        self.setup_dialog.dismiss()
        
    # ! Audio and Light Function
    def audio(self):
        if  not self.audio_on:
            # TODO Write some command to turn audio on
            self.audio_on = True
        else: 
            # TODO Write some command to turn audio off
            self.audio_on = False
    # *==================================================================================
    
    # ! ============================== Zoom Functions ===============================
    # * The below zoom functions all work exaclty the same, they change the major ticks of the 
    # * graphs along with the label and scroll container width. 
    def temp_zoom(self, action):
        if action == "+":
            if self.zoom_temp < 8:
                self.zoom_temp *= 2
                self.ids.temp.x_ticks_major /= 2
        else:
            if self.zoom_temp > 1:
                self.zoom_temp /= 2
                self.ids.temp.x_ticks_major *= 2
        self.ids.temp_cont.size_hint_x = None
        self.ids.temp_cont.width = self.zoom_temp * self.ids.scroll_temp.width        
        self.ids.label_temp.text = "Time (sec) - ({}x)".format(int(self.zoom_temp))

    def alt_zoom(self, action):
        if action == "+":
            if self.zoom_alt < 8:
                self.zoom_alt *= 2
                self.ids.alt.x_ticks_major /= 2
        else:
            if self.zoom_alt > 1:
                self.zoom_alt /= 2
                self.ids.alt.x_ticks_major *= 2
        self.ids.alt_cont.size_hint_x = None
        self.ids.alt_cont.width = self.zoom_alt * self.ids.scroll_alt.width        
        self.ids.label_alt.text = "Time (sec) - ({}x)".format(int(self.zoom_alt))

    def air_speed_zoom(self, action):
        if action == "+":
            if self.zoom_air_speed < 8:
                self.zoom_air_speed *= 2
                self.ids.air_speed.x_ticks_major /= 2
        else:
            if self.zoom_air_speed > 1:
                self.zoom_air_speed /= 2
                self.ids.air_speed.x_ticks_major *= 2
        self.ids.air_speed_cont.size_hint_x = None
        self.ids.air_speed_cont.width = self.zoom_air_speed * self.ids.scroll_air_speed.width        
        self.ids.label_air_speed.text = "Time (sec) - ({}x)".format(int(self.zoom_air_speed))
    
    def voltage_zoom(self, action):
        if action == "+":
            if self.zoom_voltage < 8:
                self.zoom_voltage *= 2
                self.ids.voltage.x_ticks_major /= 2
        else:
            if self.zoom_voltage > 1:
                self.zoom_voltage /= 2
                self.ids.voltage.x_ticks_major *= 2
        self.ids.voltage_cont.size_hint_x = None
        self.ids.voltage_cont.width = self.zoom_voltage * self.ids.scroll_voltage.width        
        #self.ids.label_voltage.text = "Time (sec) - ({}x)".format(int(self.zoom_voltage))
    def gyro_zoom(self, action):
        if action == "+":
            if self.zoom_gyro < 8:
                self.zoom_gyro *= 2
                self.ids.gyro.x_ticks_major /= 2
        else:
            if self.zoom_gyro > 1:
                self.zoom_gyro /= 2
                self.ids.gyro.x_ticks_major *= 2
        self.ids.gyro_cont.size_hint_x = None
        self.ids.gyro_cont.width = self.zoom_gyro * self.ids.scroll_gyro.width        
        #self.ids.label_gyro.text = "Time (sec) - ({}x)".format(int(self.zoom_gyro))
    
    
# ! Dialog classes (Don't Edit)
        
class Content(MDBoxLayout):
    pass    

class ItemConfirm(OneLineAvatarIconListItem):
    divider = None
    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False
                
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
        # The touch has occurred inside the widgets area. Do stuff!
            current_checked_port = self.text.split(" - ")[0]
        return super().on_touch_up(touch)