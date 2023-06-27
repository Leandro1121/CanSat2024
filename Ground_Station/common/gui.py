from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.uix.widget import Widget
from kivy.config import Config
from kivy.uix.progressbar import ProgressBar
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner 
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.text import LabelBase
from kivy.graphics.context_instructions import Translate, Scale
from kivymd.uix.button import  MDIconButton
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDIcon
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield.textfield import MDTextField
from kivy_garden.mapview import MapView, MapLayer
from kivy_garden.graph import Graph, LinePlot, MeshLinePlot
from kivy.uix.textinput import TextInput
from kivymd.uix.chip import MDChip
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, DictProperty, StringProperty
from kivy.garden.matplotlib.backend_kivagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.dropdown import DropDown

from kivy.uix.image import Image
from kivymd.app import MDApp

import numpy as np
import json
import sys

from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivy_garden.mapview import MapLayer, MapMarker
from kivy.graphics import Color, Line
from kivy.graphics.context_instructions import Translate, Scale, PushMatrix, PopMatrix
from kivy_garden.mapview.utils import clamp
from kivy_garden.mapview.constants import \
    (MIN_LONGITUDE, MAX_LONGITUDE, MIN_LATITUDE, MAX_LATITUDE)
from math import radians, log, tan, cos, pi
import random

from gui_serial import SerialObject
from gui_serial import find_serial_port

 
# TODO Temperary remove when done testing 
import queue

def read_json(file_path = "ground_station_info"):
    """
    Read in json file with formats and different global variables
    """
    file_path_final = f'Team_Info/{file_path}.json'
    with open(file_path_final, mode="r") as j_object: 
        return json.load(j_object)
    
json_args_ = read_json()
port_chosen = ""

# ! ============= CanSat 2024 Team: Ground Control Station ==================
Config.set('graphics', 'resizable', False)

class HomePage(Screen, MDApp):
    ports = ListProperty()
    connection_status = BooleanProperty()
    status = StringProperty()
    status_icon = BooleanProperty(False)
    location = NumericProperty()
    

    def __init__(self, **kw):
        super().__init__(**kw)
        self.ports = find_serial_port()
        LabelBase.register(name='college',
                   fn_regular='Ground_Station/_resources/college/colleges.ttf')
        LabelBase.register(name='roboto',
                   fn_regular='Ground_Station/_resources/roboto/Roboto-Black.ttf')
        
        
    def AttemptConnection(self, _port):
        global port_chosen
        _port =  _port.split(" - ")[0]
        port_chosen = _port
        self.bird = SerialObject(port=_port, json_args= json_args_)
        self.connection_status = not self.bird.serial_connection
        if self.bird.serial_connection is True:
            port_info = self.bird.GetPortInfo()
            self.ids.port_info_label.text =  """
            Serial Name: {name}
            Baudrate: {baud}
            XONXOFF: {xonxoff}
            Stop bits: {stop}
            Parity Bits: {parity}""".format(name = port_info[0],
                                            baud = port_info[1], 
                                            xonxoff = port_info[2], 
                                            stop = port_info[3], 
                                            parity = port_info[4] )
            
            self.CheckStatusOfPayload()
            self.status_icon = True

    def RefreshPorts(self):
        self.ports = find_serial_port()
    
    def CheckStatusOfPayload(self):
        pass
        #self.bird.StartSerialObject()
        #self.bird.serial_data_container
       
        # self.ids.status_label.text = """
        # Payload Status:
        #     GPS: {gps}
        #     Gyro: {gyro}
        #     Radio: {radio}
        #     Altitude: {alt}
        #     Mechanical: {mech}
        # Initial Setup: 
        #     {setup}

        # """.format(gps="",
        #            gyro="",
        #            radio="",
        #            alt="",
        #            mech="",
        #            setup="")


            # self.ids.port_info_label.text = f"""
            # Serial Name: {port_info["name"].split("-")[1]}
            # Baudrate: {port_info["baudrate"]}
            # XONXOFF: {port_info["xonxoff"]}
            # Stopbits: {port_info["stopbits"]}
            # Parity Bits: {port_info["parity"]}"""

    
class GCS_Page(MDScreen):
    zoom_temp = NumericProperty(1)
    zoom_gps = NumericProperty(1)
    zoom_altitude = NumericProperty(1)
    zoom_voltage = NumericProperty(1)
    zoom_gyro = NumericProperty(1)

    mission_time_x = NumericProperty(500)
    altitude_y = ListProperty()
    flight_state = StringProperty()

    #Window.fullscreen = 'auto'
    start_dialog = None
    sim_dialog = None
    cal_dialog = None
    optional_command = None

    sim_activate = True
    sim_enable = False


    def __init__(self, **kw):
        super(GCS_Page, self).__init__(**kw)
        self.layout_config()

    def start_screen(self, instance):
        pass    
    
    def layout_config(self):
        boxlayout = MDBoxLayout(orientation="vertical")

        temp1 = MDBoxLayout(orientation="horizontal", size_hint= (1, 0.2))

        self.flight_vars_container = MDGridLayout(cols=5, 
                                                rows= 2, 
                                                size_hint=(1,1),
                                                spacing=5,
                                               )
       
        temp1.add_widget(self.flight_vars_container)
        self.FlightVariables()
        boxlayout.add_widget(temp1)
        


        pb = ProgressBar(max=1000, value = self.mission_time_x, size_hint=(1,0.05))
        #boxlayout.add_widget(pb)

        self.toolbar = MDTopAppBar(
            title= "Team Name - Command Center",
            md_bg_color = "#121212",
            type= "top",
            right_action_items= [["home", lambda x: print(""), "Home Page"],
                                 ["remote-desktop", lambda x: self.optional_commands(), "Optional Commands"],
                                 ["rocket-launch",lambda x: self.start_dialogue(), "Start Payload"],
                                 ["cached", lambda x: self.cal_dialogue(), "Calibrate Payload"],
                                 ["airplane", lambda x: self.simulation_dialogue(), "Simulation Mode"],
                                 ["google-analytics", lambda x: print(""), "Analyze Data"],
                                 ["export", lambda x: print(""), "Export GUI"]],
            use_overflow = True,
        )
       
        
        boxlayout.add_widget(self.toolbar)
        self.toolbar.add_widget(pb)

        self.layout1 = GridLayout(cols=2, rows= 1, padding=0, spacing= 0)
        self.GPSGraph()
        self.GyroGraph()
        boxlayout.add_widget(self.layout1)
        self.layout = GridLayout(cols=3, rows= 1, padding=10, spacing= 5)
        self.AltitudeGraph()
        self.VoltageGraph()
        self.TemperatureGraph()
        boxlayout.add_widget(self.layout)
        # gen_box_layout.add_widget(boxlayout)
        self.add_widget(boxlayout)

    def FlightVariables(self):

        self.mission_time_start = Label(text = "Mission Time Start:{}".format("Na"), font_name = "roboto")
        self.flight_vars_container.add_widget(self.mission_time_start)

        self.mission_time_cur = Label(text = "Mission Time Current:{}".format("Na"),font_name = "roboto")
        self.flight_vars_container.add_widget(self.mission_time_cur)

        self.packet_count_label = Label(text = "Packet Count:{}".format("Na"),font_name = "roboto")
        self.flight_vars_container.add_widget(self.packet_count_label)

        self.flight_mode = Label(text = "Flight Mode:{}".format("NA"),font_name = "roboto")
        self.flight_vars_container.add_widget(self.flight_mode)

        self.flight_state_l = Label(text = "Flight State:{}".format(self.flight_state),font_name = "roboto")
        self.flight_vars_container.add_widget(self.flight_state_l)

        self.gps_sats = Label(text = "GPS SATs:{}".format("NA"),font_name = "roboto")
        self.flight_vars_container.add_widget(self.gps_sats)


        self.objective1 = Label(text = "Objective1:{}".format("NA"),pos_hint = {"center_x": 1, "center_y": 0.4})
        self.flight_vars_container.add_widget(self.objective1)

        self.objective2 = Label(text = "Objective2:{}".format("NA"),font_name = "roboto")
        self.flight_vars_container.add_widget(self.objective2)

        self.objective3 = Label(text = "Objective3:{}".format("NA"),font_name = "roboto")
        self.flight_vars_container.add_widget(self.objective3)

        
    
    def StartGraphing(self, instance):
        self.bird_g = SerialObject(port=port_chosen, json_args= json_args_)
        #self.bird_g.StartSerialObject()
    
    def simulation_dialogue(self):
        if not self.sim_dialog:
            self.sim_dialog = MDDialog(
                title='[color=FAF9F6]Simulation Control[/color]',
                text='[color=0073CF]Change the Simulation stuff\
                        [/color]',
                opposite_colors = True,
                md_bg_color = "#121212",
                buttons=[
                    MDFlatButton(
                        text="ENABLE",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_press = self.sim_enable_,
                        disabled = self.sim_enable
                    ),
                    MDFlatButton(
                        text="ACTIVATE",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_press = self.sim_activate_btn,
                    ),
                    MDFlatButton(
                        text="DISABLE",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_press = self.sim_disable_all,
                        on_release = self.sim_dismiss,
                    ),
                ],
            )
        self.sim_dialog.open()

    def sim_dismiss(self, instance):
        self.sim_dialog.dismiss()
    
    def sim_disable_all(self,instance):
        pass
            # TODO add what it will do here write command

    def sim_enable_(self,instance):
        pass
            # TODO add what it will do here write command

    def sim_activate_btn(self, instance):
        pass
        # TODO send command
    
    def start_dialogue(self):
        if not self.start_dialog:
            self.start_dialog = MDDialog(
                title='[color=FAF9F6]Start Ground Control Software[/color]',
                opposite_colors = True,
                md_bg_color = "#121212",
                buttons=[
                    MDFlatButton(
                        text="START CANSAT",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_release = self.start_dismiss,
                        on_press = self.StartCansat
                    ),
                    MDFlatButton(
                        text="STOP CANSAT",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_release = self.start_dismiss,
                        on_press = self.StopCansat
                    ),
                ],
            )
        self.start_dialog.open()

    def start_dismiss(self, instance):
        self.start_dialog.dismiss()

    def StartCansat(self, instance):
        pass
    def StopCansat(self, instance):
        pass
    
    def cal_dialogue(self):
        if not self.cal_dialog:
            self.cal_dialog = MDDialog(
                title='[color=FAF9F6]Calibration Controls[/color]',
                text='[color=0073CF]Change the Calibraition stuff\
                        [/color]',
                opposite_colors = True,
                md_bg_color = "#121212",
                buttons=[
                    MDFlatButton(
                        text="Send",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_release = self.cal_dismiss
                    ),

                ],
            )
        self.cal_dialog.open()
    

    def cal_dismiss(self,instance):
        self.cal_dialog.dismiss()

    def optional_commands(self):
        if not self.optional_command:
            self.optional_command = MDDialog(
                title='[color=FAF9F6]Optional Commands[/color]',
                opposite_colors = True,
                md_bg_color = "#121212",
                buttons=[
                    MDFlatButton(
                        text="Send",
                        theme_text_color="Custom",
                        text_color= "#FAF9F6",
                        on_release = self.optional_dismiss,
                        pos_hint = {"center_x": 0, "center_y": 0}
                    ),

                ],
            )
        self.text_field  = MDTextField(hint_text = "Enter Command",
                                  mode = "round",
                                  helper_text = "CMD,1071,XX,XXXX",
                                  size_hint = (0.5,0.5),
                                  pos_hint = {"center_x": 0.5, "center_y": 0.4},
                                  opposite_colors = True
                                 )
        self.optional_command.add_widget(self.text_field)
            
        self.optional_command.open()
    
    def optional_dismiss(self,instance):
        self.optional_command.dismiss()

    def GPSGraph(self):
        background_container = RelativeLayout()

        self.temp_box_layout = BoxLayout(size_hint=(0.805,0.84),
                                    pos_hint= {'top':0.969,'right':0.95})
        
        self.gps_background_image = MapView(zoom=7, 
                                            lat=51.046284, 
                                            lon=1.541179,
                                            on_touch_up = self.update_graph_bounds
                                            ) 

        my_coordinates = [[51.505807, -0.128513], [51.126251, 1.327067],
                          [50.959086, 1.827652], [48.85519, 2.35021]]
        lml = LineMapLayer(coordinates=my_coordinates, color=[1, 1, 0, 1])
        self.gps_background_image.add_layer(layer=lml,
                                            mode = "scatter")
        
        bounds = self.gps_background_image.get_bbox()
        self.gps_background_image.pause_on_action = True


        self.temp_box_layout.add_widget(self.gps_background_image)

        background_container.add_widget(self.temp_box_layout)

        self.gps_x_label = "Longitude {}".format("East" if bounds[0] > 0 else "West")
        self.gps_y_label = "Latitude {}".format("North" if bounds[1]> 0 else "South")

        self.gps_graph = Graph(
                                xlabel = self.gps_x_label, 
                                ylabel = self.gps_y_label,
                                xmin=round(bounds[1],2),
                                xmax=round(bounds[3],2),
                                ymin=round(bounds[0],2), 
                                ymax=round(bounds[2],2),
                                border_color=[0, 0, 0, 1,],
                                tick_color=[0,0,0,1],
                                x_grid = True,
                                y_grid = True,
                                draw_border = True,
                                x_grid_label = True, 
                                y_grid_label= True,
                                x_ticks_major= round((bounds[3]-bounds[1])/4,2),
                                y_ticks_major = round((bounds[2]-bounds[0])/4,2),
                                y_ticks_minor = 10,
                                x_ticks_minor = 10,
                                background_color = (0,0,0,0.2)
                                )
        background_container.add_widget(self.gps_graph)

        
        self.layout1.add_widget(background_container)

    def TemperatureGraph(self):
        # The above code is defining a graph with specified properties such as labels, borders, grids,
       # and ticks. However, some of the properties are commented out. It also creates a LinePlot with
       # a specified color and line width, and adds it to the graph. The LinePlot is populated with
       # data points from a queue in a dictionary.
        general_container = BoxLayout(orientation = 'vertical',
                                  size_hint=(1,1)
                                  )
       

        self.temp_scrollview = ScrollView(do_scroll_x= True,
                                        do_scroll_y= True,
                                        size_hint= (1, 0.5),
                                        scroll_type= ['content'],
                                        bar_width= 4,
                                        bar_color= (1,1,1,1),
                                        )
        self.temp_graph_container  = BoxLayout(orientation = 'vertical',
                                                size_hint=(1,1),
                                                )
                                

        self.temp_graph = Graph(
                                #xlabel = "Time (s)", 
                                ylabel = "Temperature (C)",
                                xmin=0,
                                xmax= self.mission_time_x+50,
                                ymin= 0, 
                                ymax= 32,
                                border_color=[0, 1, 1, 1,],
                                tick_color=[0,1,1,0.7],
                                x_grid = True,
                                y_grid = True,
                                draw_border = True,
                                x_grid_label = True, 
                                y_grid_label= True,
                                x_ticks_major= 100, #round(self.mission_time_x), 
                                y_ticks_major = 8,
                                background_color = [0,0,0,0.7],
                                )
        
        button_container = BoxLayout(
                            size_hint= (1, 0.05),
                            orientation= 'horizontal'
                            )
        
        self.temp_zoom_label = Label(text= "Time (sec) - ({zoom}x)".format(zoom = self.zoom_temp))
        
        button_zoom_inc = MDIconButton(
                                icon = "plus-box",
                                size_hint = (0.1,1),
                                icon_size = "24sp",
                                theme_icon_color = "Custom",
                                icon_color = "#FAF9F6",
                                on_release= self.zoom_inc_temp,
                                )
        
       

        button_zoom_dec = MDIconButton(
                                icon = "minus-box",
                                size_hint = (0.1,1),
                                icon_size = "24sp",
                                theme_icon_color = "Custom",
                                icon_color = "#FAF9F6",
                                on_release=self.zoom_dec_temp)

    
        
        button_container.add_widget(button_zoom_inc)
        button_container.add_widget(self.temp_zoom_label)
        button_container.add_widget(button_zoom_dec)
        
        
        self.temp_graph_container.add_widget(self.temp_graph)
        self.temp_scrollview.add_widget(self.temp_graph_container)
        general_container.add_widget(self.temp_scrollview)
        general_container.add_widget(button_container)
        self.layout.add_widget(general_container)
        
        self.temp_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
        self.temp_plot.points = [( x, x) for x in range(self.mission_time_x)]
        self.temp_graph.add_plot(self.temp_plot)
        


    
    def VoltageGraph(self):
        # The above code is defining a graph with specified properties such as labels, borders, grids,
       # and ticks. However, some of the properties are commented out. It also creates a LinePlot with
       # a specified color and line width, and adds it to the graph. The LinePlot is populated with
       # data points from a queue in a dictionary.
        general_container = BoxLayout(orientation = 'vertical',
                                  size_hint=(1,1)
                                  )
       

        self.voltage_scrollview = ScrollView(do_scroll_x= True,
                                        do_scroll_y= True,
                                        size_hint= (1, 0.5),
                                        scroll_type= ['content'],
                                        bar_width= 4,
                                        bar_color= (1,1,1,1),
                                        )
        self.voltage_graph_container  = BoxLayout(orientation = 'vertical',
                                                size_hint=(1,1),
                                                )
        self.voltage_graph = Graph( 
                                ylabel = "Voltage",
                                xmin=0,#min(self.mission_time_x),
                                xmax= self.mission_time_x + 50,#max(self.mission_time_x),
                                ymin= 0, 
                                ymax= 10,#max(self.voltage_y)+100,
                                border_color=[0, 1, 1, 1,],
                                tick_color=[0,1,1,0.7],
                                x_grid = True,
                                y_grid = True,
                                draw_border = True,
                                x_grid_label = True, 
                                y_grid_label= True,
                                x_ticks_major= 100, #round(self.mission_time_x), 
                                y_ticks_major = 2,
                                x_ticks_minor = 10,
                                y_ticks_minor = 10,
                                background_color = (0,0,0,0.7)
                                )
        
        
        button_container = BoxLayout(
                            size_hint= (1, 0.05),
                            orientation= 'horizontal'
                            )
        
        self.voltage_zoom_label = Label(text= "Time (sec) - ({zoom}x)".format(zoom = self.zoom_voltage))
        
        button_zoom_inc = MDIconButton(
                                icon = "plus-box",
                                size_hint = (0.1,1),
                                icon_size = "24sp",
                                theme_icon_color = "Custom",
                                icon_color = "#FAF9F6",
                                on_release= self.zoom_inc_voltage,
                                )
        
       
        button_zoom_dec = MDIconButton(
                                icon = "minus-box",
                                size_hint = (0.1,1),
                                icon_size = "24sp",
                                theme_icon_color = "Custom",
                                icon_color = "#FAF9F6",
                                on_release=self.zoom_dec_voltage
                                )

    
        
        button_container.add_widget(button_zoom_inc)
        button_container.add_widget(self.voltage_zoom_label)
        button_container.add_widget(button_zoom_dec)
        
        
        self.voltage_graph_container.add_widget(self.voltage_graph)
        self.voltage_scrollview.add_widget(self.voltage_graph_container)
        general_container.add_widget(self.voltage_scrollview)
        general_container.add_widget(button_container)
        self.layout.add_widget(general_container)
        self.voltage_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
        self.voltage_plot.points = [(x, np.sin(x / 10.)) for x in range(0, 101)]
        self.voltage_graph.add_plot(self.voltage_plot)
    
    def GyroGraph(self):
        # The above code is defining a graph with specified properties such as labels, borders, grids,
       # and ticks. However, some of the properties are commented out. It also creates a LinePlot with
       # a specified color and line width, and adds it to the graph. The LinePlot is populated with
       # data points from a queue in a dictionary.
        general_container = BoxLayout(
                                    orientation = 'vertical',
                                    size_hint=(1,1),
                                    )
       

        self.gyro_scrollview = ScrollView(
                                        do_scroll_x= True,
                                        do_scroll_y= True,
                                        size_hint= (1, 0.5),
                                        scroll_type= ['content'],
                                        bar_width= 4,
                                        bar_color= (1,1,1,1),
                                        )
        self.gyro_graph_container  = BoxLayout(orientation = 'vertical',
                                                size_hint=(1,1),
                                                )
        self.gyro_graph = Graph( 
                                ylabel = "Tilt",
                                xmin=0,
                                xmax= self.mission_time_x + 50,
                                ymin= 0, 
                                ymax= 10,
                                border_color=[0, 1, 1, 1,],
                                tick_color=[0,1,1,0.7],
                                x_grid = True,
                                y_grid = True,
                                draw_border = True,
                                x_grid_label = True, 
                                y_grid_label= True,
                                x_ticks_major= 100,
                                y_ticks_major = 2,
                                x_ticks_minor = 10,
                                y_ticks_minor = 10,
                                background_color = (0,0,0,0.7)
                                )
        
        
        button_container = BoxLayout(
                            size_hint= (1, 0.05),
                            orientation= 'horizontal',
                            background_color= (0,0,0,1)
                            )
        
        self.gyro_zoom_label = Label(text= "Time (sec) - ({zoom}x)".format(zoom = self.zoom_gyro),
                                     )
        
        button_zoom_inc = MDIconButton(
                                icon = "plus-box",
                                size_hint = (0.07,1),
                                icon_size = "30sp",
                                theme_icon_color = "Custom",
                                icon_color = "#FAF9F6",
                                on_release= self.zoom_inc_gyro
                                )
        
       
        button_zoom_dec = MDIconButton(
                                icon = "minus-box",
                                size_hint = (0.07,1),
                                icon_size = "30sp",
                                theme_icon_color = "Custom",
                                icon_color = "#FAF9F6",
                                on_release=self.zoom_dec_gyro
                                )

    
        
        button_container.add_widget(button_zoom_inc)
        button_container.add_widget(self.gyro_zoom_label)
        button_container.add_widget(button_zoom_dec)
        
        
        self.gyro_graph_container.add_widget(self.gyro_graph)
        self.gyro_scrollview.add_widget(self.gyro_graph_container)
        general_container.add_widget(self.gyro_scrollview)
        general_container.add_widget(button_container)
        self.layout1.add_widget(general_container)
        self.gyro_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
        self.gyro_plot.points = [(x, np.sin(x / 10.)) for x in range(0, 101)]
        self.gyro_graph.add_plot(self.gyro_plot)

    def AltitudeGraph(self):
       # The above code is defining a graph with specified properties such as labels, borders, grids,
       # and ticks. However, some of the properties are commented out. It also creates a LinePlot with
       # a specified color and line width, and adds it to the graph. The LinePlot is populated with
       # data points from a queue in a dictionary.
        general_container = BoxLayout(orientation = 'vertical',
                                  size_hint=(1,1)
                                  )
       
        
        # self.altitude_scrollview = ScrollView(do_scroll_x= True,
        #                                 do_scroll_y= True,
        #                                 size_hint= (1, 0.5),
        #                                 scroll_type= ['content'],
        #                                 bar_width= 4,
        #                                 bar_color= (1,1,1,1),
        #                                 )
        # self.altitude_graph_container  = BoxLayout(orientation = 'vertical',
        #                                         size_hint=(1,1),
        #                                         )
        # self.altitude_graph = Graph(
        #                         #xlabel = "Time", 
        #                         ylabel = "Altitude",
        #                         xmin=0,#min(self.mission_time_x),
        #                         xmax= self.mission_time_x + 50,#max(self.mission_time_x),
        #                         ymin= 0, 
        #                         ymax= 700,#max(self.altitude_y)+100,
        #                         border_color=[0, 1, 1, 1,],
        #                         tick_color=[0,1,1,0.7],
        #                         x_grid = True,
        #                         y_grid = True,
        #                         draw_border = True,
        #                         x_grid_label = True, 
        #                         y_grid_label= True,
        #                         x_ticks_major= 100, #round(self.mission_time_x), 
        #                         y_ticks_major = 100,
        #                         x_ticks_minor = 10,
        #                         y_ticks_minor = 10,
        #                         background_color = (0,0,0,0.7)
        #                         )
        
        
        # button_container = BoxLayout(
        #                     size_hint= (1, 0.05),
        #                     orientation= 'horizontal'
        #                     )
        
        # self.altitude_zoom_label = Label(text= "Time (sec) - ({zoom}x)".format(zoom = self.zoom_altitude))
        
        # button_zoom_inc = MDIconButton(
        #                         icon = "plus-box",
        #                         size_hint = (0.1,1),
        #                         icon_size = "24sp",
        #                         theme_icon_color = "Custom",
        #                         icon_color = "#FAF9F6",
        #                         on_release= self.zoom_inc_altitude,
        #                         )
        
       
        # button_zoom_dec = MDIconButton(
        #                         icon = "minus-box",
        #                         size_hint = (0.1,1),
        #                         icon_size = "24sp",
        #                         theme_icon_color = "Custom",
        #                         icon_color = "#FAF9F6",
        #                         on_release=self.zoom_dec_altitude
        #                         )

    
        
        # button_container.add_widget(button_zoom_inc)
        # button_container.add_widget(self.altitude_zoom_label)
        # button_container.add_widget(button_zoom_dec)
        
        
        # self.altitude_graph_container.add_widget(self.altitude_graph)
        # self.altitude_scrollview.add_widget(self.altitude_graph_container)
        # general_container.add_widget(self.altitude_scrollview)
        # general_container.add_widget(button_container)
        self.layout.add_widget(general_container)
        
        self.altitude_plot = LinePlot(color = [1, 1, 0, 1], line_width=1.5)
        self.altitude_plot.points = [(self.mission_time_x[x], self.altitude_y[x]) for x in range(0)]
        self.altitude_graph.add_plot(self.altitude_plot)

    # ! Update Graphs and Flight Variables 
    def update_plot (self, freq):
        for key in self.temp_data:
            self.plot.points = [(self.temp_data["mission_time"].queue[x], self.temp_data[key].queue[x]) for x in range(self.sample)]

    # ! Zoom Functions
    def zoom_inc_temp(self,instance):
        if self.zoom_temp < 8:
            self.zoom_temp *= 2
            self.temp_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_temp)
            self.temp_graph_container.size_hint_x = None
            self.temp_graph_container.width = self.zoom_temp * self.temp_scrollview.width
            self.temp_graph.x_ticks_major /= 2
    def zoom_dec_temp(self,instance):
        if self.zoom_temp > 1:
            self.zoom_temp /= 2
            self.temp_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_temp)
            self.temp_graph_container.width = self.zoom_temp * self.temp_scrollview.width
            self.temp_graph.x_ticks_major *= 2
    
    def update_graph_bounds(self, instance, args):
        bounds = self.gps_background_image.get_bbox()
        self.gps_graph.xmax = round(bounds[1],2)
        self.gps_graph.xmax = round(bounds[3],2)
        self.gps_graph.ymax = round(bounds[0],2)
        self.gps_graph.ymax = round(bounds[2],2)
        self.gps_graph.x_ticks_major = round((bounds[3]-bounds[1])/4,2)
        self.gps_graph.y_ticks_major = round((bounds[2]-bounds[0])/4,2)

    def zoom_inc_altitude(self,instance):
        if self.zoom_altitude < 8:
            self.zoom_altitude *= 2
            self.altitude_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_altitude)
            self.altitude_graph_container.size_hint_x = None
            self.altitude_graph_container.width = self.zoom_altitude * self.altitude_scrollview.width
            self.altitude_graph.x_ticks_major /= 2
            #self.altitude_graph.x_ticks_minor /= 2
            
    def zoom_dec_altitude(self,instance):
        if self.zoom_altitude > 1:
            self.zoom_altitude /= 2
            self.altitude_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_altitude)
            self.altitude_graph_container.width = self.zoom_altitude * self.altitude_scrollview.width
            self.altitude_graph.x_ticks_major *= 2
    
    def zoom_inc_voltage(self,instance):
        if self.zoom_voltage < 8:
            self.zoom_voltage *= 2
            self.voltage_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_voltage)
            self.voltage_graph_container.size_hint_x = None
            self.voltage_graph_container.width = self.zoom_voltage * self.voltage_scrollview.width
            self.voltage_graph.x_ticks_major /= 2
            #self.voltage_graph.x_ticks_minor /= 2
            
    def zoom_dec_voltage(self,instance):
        if self.zoom_voltage > 1:
            self.zoom_voltage /= 2
            self.voltage_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_voltage)
            self.voltage_graph_container.width = self.zoom_voltage * self.voltage_scrollview.width
            self.voltage_graph.x_ticks_major *= 2

    def zoom_inc_gyro(self,instance):
        if self.zoom_gyro < 8:
            self.zoom_gyro *= 2
            self.gyro_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_gyro)
            self.gyro_graph_container.size_hint_x = None
            self.gyro_graph_container.width = self.zoom_gyro * self.gyro_scrollview.width
            self.gyro_graph.x_ticks_major /= 2
            #self.gyro_graph.x_ticks_minor /= 2
            
    def zoom_dec_gyro(self,instance):
        if self.zoom_gyro > 1:
            self.zoom_gyro /= 2
            self.gyro_zoom_label.text = "Time (sec) - ({zoom}x)".format(zoom = self.zoom_gyro)
            self.gyro_graph_container.width = self.zoom_gyro * self.gyro_scrollview.width
            self.gyro_graph.x_ticks_major *= 2
    
class LineMapLayer(MapLayer):
    def __init__(self, coordinates=[[0, 0], [0, 0]], color=[0, 0, 1, 1], **kwargs):
        super().__init__(**kwargs)
        self._coordinates = coordinates
        self.color = color
        self._line_points = None
        self._line_points_offset = (0, 0)
        self.zoom = 0
        self.lon = 0
        self.lat = 0
        self.ms = 0

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates):
        self._coordinates = coordinates
        self.invalidate_line_points()
        self.clear_and_redraw()

    @property
    def line_points(self):
        if self._line_points is None:
            self.calc_line_points()
        return self._line_points

    @property
    def line_points_offset(self):
        if self._line_points is None:
            self.calc_line_points()
        return self._line_points_offset

    def calc_line_points(self):
        # Offset all points by the coordinates of the first point,
        # to keep coordinates closer to zero.
        # (and therefore avoid some float precision issues when drawing lines)
        self._line_points_offset = (self.get_x(self.coordinates[0][1]),
                                    self.get_y(self.coordinates[0][0]))
        # Since lat is not a linear transform we must compute manually
        self._line_points = [(self.get_x(lon) - self._line_points_offset[0],
                              self.get_y(lat) - self._line_points_offset[1])
                             for lat, lon in self.coordinates]

    def invalidate_line_points(self):
        self._line_points = None
        self._line_points_offset = (0, 0)

    def get_x(self, lon):
        """Get the x position on the map using this map source's projection
        (0, 0) is located at the top left.
        """
        return clamp(lon, MIN_LONGITUDE, MAX_LONGITUDE) * self.ms / 360.0

    def get_y(self, lat):
        """Get the y position on the map using this map source's projection
        (0, 0) is located at the top left.
        """
        lat = radians(clamp(-lat, MIN_LATITUDE, MAX_LATITUDE))
        return (1.0 - log(tan(lat) + 1.0 / cos(lat)) / pi) * self.ms / 2.0

    # Function called when the MapView is moved
    def reposition(self):
        map_view = self.parent

        # Must redraw when the zoom changes
        # as the scatter transform resets for the new tiles
        if self.zoom != map_view.zoom or \
                   self.lon != round(map_view.lon, 7) or \
                   self.lat != round(map_view.lat, 7):
            map_source = map_view.map_source
            self.ms = pow(2.0, map_view.zoom) * map_source.dp_tile_size
            self.invalidate_line_points()
            self.clear_and_redraw()

    def clear_and_redraw(self, *args):
        with self.canvas:
            # Clear old line
            self.canvas.clear()

        self._draw_line()

    def _draw_line(self, *args):
        map_view = self.parent
        self.zoom = map_view.zoom
        self.lon = map_view.lon
        self.lat = map_view.lat

        # When zooming we must undo the current scatter transform
        # or the animation distorts it
        scatter = map_view._scatter
        sx, sy, ss = scatter.x, scatter.y, scatter.scale

        # Account for map source tile size and map view zoom
        vx, vy, vs = map_view.viewport_pos[0], map_view.viewport_pos[1], map_view.scale

        with self.canvas:

            # Save the current coordinate space context
            PushMatrix()

            # Offset by the MapView's position in the window (always 0,0 ?)
            Translate(*map_view.pos)

            # Undo the scatter animation transform
            Scale(1 / ss, 1 / ss, 1)
            Translate(-sx, -sy)

            # Apply the get window xy from transforms
            Scale(vs, vs, 1)
            Translate(-vx, -vy)

            # Apply what we can factor out of the mapsource long, lat to x, y conversion
            Translate(self.ms / 2, 0)

            # Translate by the offset of the line points
            # (this keeps the points closer to the origin)
            Translate(*self.line_points_offset)

            Color(*self.color)
            Line(points=self.line_points, width=2)

            # Retrieve the last saved coordinate space context
            PopMatrix()


         
       
class RawDataDisplay(Screen):
    pass
class WindowManager(ScreenManager):
     pass

class GroundControlStationApp(MDApp):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        team_name = "NA"
        team_ID = 1067
        self.title = f'{team_name}-{team_ID}-Ground Control Station'
        json_args_ = read_json()
        self.icon = "../_static/icon.png"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"


if __name__ == "__main__":
    
    GroundControlStationApp().run()
# ! =========================================================================