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
# TODO: Remove any unnessary dependencies
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
                            StringProperty, ObjectProperty, BoundedNumericProperty
from kivymd.app import MDApp
from kivymd.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivymd.uix.filemanager import MDFileManager
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg, \
                                                NavigationToolbar2Kivy
from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
import matplotlib.animation as animation
import matplotlib.pyplot as plt 
from matplotlib import cm 
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.style as mplstyle
from kivymd.uix.list import OneLineAvatarIconListItem
from kivy.core.text import LabelBase

from kivy.clock import Clock
from tools.map_overlay import LineMapLayer
from kivymd.toast import toast

from tools.gui_serial import SerialObject
from tools.gui_serial import find_serial_port
import os, shutil
import csv 
import json
import numpy as np
from datetime import datetime
from tools.custom_data_table import CustomDataTable
from kivy.core.audio import SoundLoader
from kivy.graphics import Line,Color
import webbrowser
import csv

x_data_analysis_container = []
y_data_analysis_container = []
z_data_analysis_container = []
fig= plt.figure(facecolor=(1, 1, 1, 0.7), figsize=(100,10))
ax = plt.axes(111,projection= "3d")
current_checked_port = "" 
volts_value = 50 
 
 
class AnalysisPage(MDScreen):
    manager = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager, select_path=self.select_path
        )
        
    # ! For more modification -> https://kivymd.readthedocs.io/en/1.1.1/components/filemanager/
    def file_manager_open(self):
        self.file_manager.show(os.path.expanduser("~"))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''
        self.exit_manager()
        toast(path)

    def set_graph_values(self):
        filename = r'Ground_Station\_flight_recordings\flight-record_admin_.csv'
        with open(filename, 'r') as csvfile:
            datareader = csv.reader(csvfile)
            for row in datareader:
                x_data_analysis_container.append(float(row[14]))
                y_data_analysis_container.append(float(row[15]))
                z_data_analysis_container.append(float(row[5]))

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()
    
    def store_flight_data(self, file:str ): 
        # TODO Finish this function -> dict("Item", [])
        filepath = file
        flight_data = []
        with open(filepath, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)
        
            # extracting each data row one by one
            for row in csvreader:
                flight_data.append(row)
                
        return flight_data
    
                
    #TODO Write function to add data containers for Matplotlib graph to: 
    """x_data_analysis_container = []
        y_data_analysis_container = []
        z_data_analysis_container = []"""           
        

        
    def on_enter(self):
        # * This function is for things you want to do when you open up kivy
        self.flight_data = self.store_flight_data(r"Ground_Station\_flight_recordings\flight-record_admin_.csv")
        #self.get_file()
        #self.ids.summary_label.font_name = 'graph'
        #self.ids.summary_title.font_name = 'graph'
        
    def on_pre_enter(self):
        self.set_graph_values()
        ax.plot3D(x_data_analysis_container,
                y_data_analysis_container,
                z_data_analysis_container,
                color = 'red')
        #self.ids.table_placeholder.add_widget(CustomDataTable())
         
class AltitudeFigure(MDBoxLayout):
    graph = ObjectProperty(None)
    def __init__(self, *args, **kwargs):
        #TODO All configurations for the matplot graph are done in this class
        super(AltitudeFigure, self).__init__(*args, **kwargs)
        global ax
        global fig
    
        self.orientation = "vertical"
        
        ax.set_title("Flight Summary", color = 'white')
        ax.set_xlabel("Latitude", color = 'white')
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
        canvas = FigureCanvasKivyAgg(plt.gcf()) # ! Don't remove
        self.add_widget(canvas) # ! Don't remove
        
        #  if self.bird:
        #     # ! 3D Graph
        #     if len(self.bird.gps_single_container) > 0:
        #         global x_data_analysis_container
        #         global y_data_analysis_container
        #         global z_data_analysis_container
        #         gps_data = self.bird.gps_single_container
        #         x_data_analysis_container = [lat for (lat,_) in gps_data]
        #         y_data_analysis_container = [lon for (_,lon) in gps_data]
        #         z_data_analysis_container = [alt for alt in self.bird.collectable_data['altitude']]