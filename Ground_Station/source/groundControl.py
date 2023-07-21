from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy_garden.mapview import MapView, MapMarker, MapSource
from kivy_garden.graph import Graph, LinePlot
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.properties import NumericProperty,ListProperty, \
                            BooleanProperty, DictProperty, \
                            StringProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg, \
                                                NavigationToolbar2Kivy
import matplotlib.animation as animation
import matplotlib.pyplot as plt 
from matplotlib import cm 
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.style as mplstyle
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.core.text import LabelBase

from kivy.clock import Clock
from tools.map_overlay import LineMapLayer

from tools.gui_serial import SerialObject
from tools.gui_serial import find_serial_port
import os, shutil
import json
import numpy as np
from datetime import datetime

def read_json(file_path = "ground_station_info"):
    
    """
    Read in json file with formats and different global variables
    """
    file_path_final = f'Team_Info/{file_path}.json'
    with open(file_path_final, mode="r") as j_object: 
        return json.load(j_object)
    
json_args_ = read_json()
flight_vals = json_args_['flight_vals']
collectables = json_args_['collectable_data']
x_data_analysis_container = []
y_data_analysis_container = []
z_data_analysis_container = []
fig= plt.figure(facecolor=(1, 1, 1, 0.7), figsize=(100,10))
ax = plt.axes(111,projection= "3d")
current_checked_port = "" 


class GroundControlApp(MDApp):
    
    def build(self):
        team_name = "NA"
        team_ID = 1067
        self.title = f'{team_name}-{team_ID}-Ground Control Station'
        self.icon = "../_static/icon.png"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        LabelBase.register(name='graph',
                   fn_regular='Ground_Station\_resources\VCR_OSD_MONO_1.001.ttf')
        
        

class HomePage(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #TODO Setup front page

class GCSPage(MDScreen):
    setup_dialog = None
    opt_cmd_dialog = None
    sim_dialog = None
    start_dialog = None
    cal_dialog = None
    bird = None
    
    mission_time_curr = StringProperty(datetime.now())
    # ! Zoom Values
    zoom_alt = NumericProperty(1)
    zoom_temp = NumericProperty(1)
    zoom_gyro = NumericProperty(1)
    zoom_voltage = NumericProperty(1)
    # ! Navbar Tool Properties
    disable_tools = BooleanProperty(True)
    list_size = NumericProperty(0)
    # ! Graphing Properties
    x_max = NumericProperty(60)
    new_data = BooleanProperty(False)
    my_coordinates = [[29,-82]]
    # ! Graph Plots
    alt_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    volt_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    gyro_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    temp_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
    
    def __init__(self, *args, **kwargs):
        super(GCSPage, self).__init__(*args, **kwargs)
        
    def update(self, instance):
        self.ids.mission_time_curr.text = "Mission Time Current:[color=ff0000]{}[/color]"\
            .format(datetime.utcnow().strftime("%H:%M:%S"))
        try:
            self.new_data = self.bird.new_data_to_graph
        except:
            pass
    
    def backend_binds(self):
        self.bind(list_size=self.auto_size)
        self.bind(new_data= self.plot_update)
    
    def on_pre_enter(self):
        self.backend_binds()
        self.format_flight_vals()
        
        #self.ids.gps_map.map_source = MapSource(max_zoom = 15, min_zoom = 7)
            
    def on_enter(self):
        Clock.schedule_interval(self.update, 1)
        
        self.gps_plot = LineMapLayer(coordinates=self.my_coordinates, color=[1, 0, 0, 1])
        self.ids.gps_map.add_layer(self.gps_plot, mode="scatter")
        
        
    def on_exit(self):
        Clock.unschedule(self.update)
        if self.bird:
            if len(self.bird.gps_single_container) > 0:
                global x_data_analysis_container
                global y_data_analysis_container
                global z_data_analysis_container
                gps_data = self.bird.gps_single_container
                x_data_analysis_container = [lat for (lat,_) in gps_data]
                y_data_analysis_container = [lon for (_,lon) in gps_data]
                z_data_analysis_container = [alt for alt in self.bird.collectable_data['Altitude']]
                
            
            
            

    def auto_size(self, instance, value):
        if self.list_size >= self.x_max - (self.x_max/4):
            self.x_max += round(self.x_max/2)
            
    def plot_update(self, instance, value):
        
        if self.new_data is False: return
        
        data = self.bird.get_serial_data()
        # TODO Modify for Current Year competition
        self.ids.packet_count.text = \
            "Packet Count: [color=ff0000]{}[/color]".format(data[flight_vals['packet_count']])

        self.ids.flight_mode.text = \
            "Flight Mode: [color=ff0000]{}[/color]".format(data[flight_vals['flight_mode']])
        
        self.ids.flight_state.text = \
            "Flight State: [color=ff0000]{}[/color]".format(data[flight_vals['flight_state']])
       
        self.ids.gps_sats.text = \
            "GPS Sats: [color=ff0000]{}[/color]".format(data[flight_vals['GPS_sats']])
        
        self.alt_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['Altitude'])]
        self.ids.alt.add_plot(self.alt_plot)
        
        self.gyro_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['GYRO'])]
        self.ids.gyro.add_plot(self.gyro_plot)
        
        self.volt_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['voltage'])]
        self.ids.voltage.add_plot(self.volt_plot)
        
        self.temp_plot.points = [(x, y) for x, y in enumerate(self.bird.collectable_data['temperature'])]
        self.ids.temp.add_plot(self.temp_plot)
        
        self.my_coordinates.append(self.bird.gps_single_container[-1])
        self.ids.current_loc.text = \
            "Payload Location: [color=ffff00]{}[/color]" \
                .format(self.my_coordinates[-1])
        self.ids.gps_map.trigger_update(True)
        
        self.list_size += 1
        self.new_data, self.bird.new_data_to_graph = False, False
        
   
    def on_touch_up(self, touch):
        if self.ids.gps_map.collide_point(*touch.pos):
            temp_loc=self.ids.gps_map.get_latlon_at(touch.x,
                                                    touch.y,
                                                    zoom = self.ids.gps_map.zoom)
            temp_loc = [round(item,4) for item in temp_loc]
            self.ids.selected_loc.text = \
                "Selected Location: [color=ff0000]{}[/color]".\
                    format(temp_loc)
            
    def format_flight_vals(self):
        
        # TODO Add the initialization of the flight values
        self.ids.mission_time_start.markup = True
        self.ids.current_loc.markup = True
        self.ids.selected_loc.markup = True
        
        self.ids.mission_time_curr.markup = True
        self.ids.mission_time_curr.text = "Mission Time Current:[color=ff0000]{}[/color]"\
            .format(datetime.utcnow().strftime("%H:%M:%S"))
        
        self.ids.packet_count.markup = True
        self.ids.packet_count.text = "Packet Count: [color=ff0000]{}[/color]".format(0)
        
        self.ids.flight_mode.markup = True
        self.ids.flight_mode.text = "Flight Mode: [color=ff0000]{}[/color]".format("F")
        
        self.ids.flight_state.markup = True
        self.ids.flight_state.text = "Flight State: [color=ff0000]{}[/color]".format("NA")
        
        self.ids.gps_sats.markup = True
        self.ids.gps_sats.text = "GPS Sats: [color=ff0000]{}[/color]".format(0)
        
        self.ids.status.markup = True
        self.ids.status.text = "Status: [color=ff0000]{}[/color]".format("Not Ready")
        
    # ! Dialog Tools
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
        print("start")
    def st_time_dialog_helper(self,instance):
        print("time")
    def st_gps_dialog_helper(self,instance):
        print("gps")
        
    # * ====================== Transmission Dialog ===============
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
        self.ids.mission_time_start.text = "Mission Time Start: [color=ff0000]{}[/color]"\
            .format(datetime.utcnow().strftime("%H:%M:%S.%f")[:-4])
        self.ids.gps_map.add_marker(MapMarker(lon=-82, lat=29 ))  
        self.bird.StartSerialObject()
        self.bird.WriteSerialData(command="CX", data_to_write="ON")
        self.ids.analysis_tool.disabled = True
        self.ids.home_icon.disabled = True
        self.start_dialog.dismiss()
    def end_dialog_helper(self,instance):
        self.bird.StopSerialObject()
        self.bird.WriteSerialData(command="CX", data_to_write="OFF")
        self.ids.analysis_tool.disabled = False
        self.ids.home_icon.disabled = False
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
                        on_release= self.sim_enable_helper
                    ),
                    MDRaisedButton(
                        text="ACTIVATE",
                        theme_text_color="Custom",
                        on_release= self.sim_activate_helper
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
        self.bird.WriteSerialData("SIM", "ENABLE")
    def sim_activate_helper(self,instance):
        self.bird.WriteSerialData("SIM", "ACTIVATE")
    def sim_disable_helper(self,instance):
        self.bird.WriteSerialData("SIM", "DISABLE")
        self.sim_dialog.dismiss()
        
    # * ============== Optional Command Dialog and tools ============     
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
        self.bird.WriteSerialData(value)
        
    # * ================== Setup Dialog and tools =================== 
           
    def setup_dialog_func(self):
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
        self.setup_dialog.dismiss()
        
            
    # *==================================================================================
    
    # ! ============================== Zoom Functions ===============================
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
        self.ids.label_gyro.text = "Time (sec) - ({}x)".format(int(self.zoom_gyro))
        
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
        self.ids.label_voltage.text = "Time (sec) - ({}x)".format(int(self.zoom_voltage))
       
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
        global current_checked_port
        current_checked_port = self.text.split(" - ")[0]
        return super().on_touch_up(touch)
# ! ==============================================================================       

   
class AnalysisPage(MDScreen):
    file_path = 'Ground_Station\_summary\summary.txt'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_file(self):
        try:
            with open(self.file_path, 'r') as file:
                self.ids.summary_label.text = file.read()
        except FileNotFoundError as e:
            pass
        
        
    def on_enter(self):
        self.get_file()
        self.ids.summary_label.font_name = 'graph'
        self.ids.summary_title.font_name = 'graph'
        
    def on_pre_enter(self):
        ax.plot3D(x_data_analysis_container,
                y_data_analysis_container,
                z_data_analysis_container,
                color = 'red')
        print(x_data_analysis_container)
        
       
        
        
class AltitudeFigure(MDBoxLayout):
    graph = ObjectProperty(None)
    def __init__(self, *args, **kwargs):
        super(AltitudeFigure, self).__init__(*args, **kwargs)
        global ax
        global fig
    
        self.orientation = "vertical"
        
        ax.set_title("Flight Summary", color = 'white')
        ax.set_xlabel("Latitude", color = 'white' )
        ax.set_ylabel("Longitude", color = 'white')
        ax.set_zlabel("Altitude", color = 'white')
        ax.set_xlim3d(0, 1)
        ax.set_ylim3d(0, 1)
        ax.set_zlim3d(0, 1)
        ax.set_autoscale_on(True)
        fig.set_facecolor([0,0,0,0.5])
        ax.set_facecolor([0,0,0,0.5])
        

        ax.tick_params(axis='x',colors='white')
        ax.tick_params(axis='y',colors='white')
        ax.tick_params(axis='z',colors='white')

        plt.legend(['Container', 'Payload'])
        plt.grid(True, linestyle='--')
        plt.tick_params(labelsize=10, color = 'white')
        plt.rc('font', family='robot')
        canvas = FigureCanvasKivyAgg(plt.gcf())
        self.add_widget(canvas)

class WindowManager(MDScreenManager):
    pass

if __name__ == "__main__":
    file_path = 'cache'
    clear_cache = True
    if clear_cache:
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    
    GroundControlApp().run()
# ! =================================