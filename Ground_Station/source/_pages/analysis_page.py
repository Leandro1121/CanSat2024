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
        self.file_name = None
        
    # ! For more modification -> https://kivymd.readthedocs.io/en/1.1.1/components/filemanager/
    def file_manager_open(self):
        self.file_manager.show(r"Ground_Station\_flight_recordings")  # output manager to the screen
        self.manager_open = True

    def select_path(self, path: str):
        '''
        It will be called when you click on the file name
        or the catalog selection button.

        :param path: path to the selected directory or file;
        '''
        self.exit_manager()
        toast(path)
        self.set_graph_values(path)
        self.ids.main_layout.clear_widgets()
           
        #self.ids.table_placeholder.add_widget(CustomDataTable())
        self.ids.main_layout.add_widget(AltitudeFigure())
        

    def set_graph_values(self, filename):
    
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
        
    #def on_enter(self):
        
         
class AltitudeFigure(MDBoxLayout):
    graph = ObjectProperty(None)
    def __init__(self, *args, **kwargs):
        #TODO All configurations for the matplot graph are done in this class
        super(AltitudeFigure, self).__init__(*args, **kwargs)
        global ax
        global fig
    
        self.orientation = "vertical"
        
        ax.set_title("Flight Summary", color = 'red')
        ax.set_xlabel("Latitude", color = 'orange' )
        ax.set_ylabel("Longitude", color = 'yellow')
        ax.set_zlabel("Altitude", color = 'green')

        ax.set_xlim3d(0, 1)
        ax.set_ylim3d(0, 1)
        ax.set_zlim3d(0, 1)
        ax.set_autoscale_on(True)
        fig.set_facecolor([0,0,0,0.5])
        ax.set_facecolor([0,0,0,0.5])
        

        ax.tick_params(axis='x',colors='orange')
        ax.tick_params(axis='y',colors='yellow')
        ax.tick_params(axis='z',colors='green')

        plt.legend(['Payload'])
        plt.grid(True, linestyle='--')
        plt.tick_params(labelsize=8, color = 'white')
        plt.rc('font', family='robot')
        canvas = FigureCanvasKivyAgg(plt.gcf()) # ! Don't remove
        self.add_widget(canvas) # ! Don't remove
    
        ax.plot3D(x_data_analysis_container,
                y_data_analysis_container,
                z_data_analysis_container,
                color = 'red')
        
        plt.savefig(r"Ground_Station\_pfr_material\flight_ansys.png", bbox_inches='tight')