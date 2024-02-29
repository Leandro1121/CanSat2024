"""
# ! ***************************************************
*             The University of Florida               *
*             Space Systems Design Club               *
*                     CanSat 2024                     *
*                Team: 2024 The Swamp                 *
*                     Authored by:                    *
*    Leandro Sanchez,                                 *
# ! ***************************************************
"""
import os
import shutil
from tools.json_FR import read_json
from tools.gttsx_tool import sound_gen

# ! Kivy MD
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.app import MDApp
from kivy.core.text import LabelBase

# ! Screen Pages
from _pages.home_page import HomePage
from _pages.gcs_page import GCSPage
from _pages.analysis_page import AnalysisPage

"""
**************************************************
The purpose of this file is to set the themes and supporting
structures of the applications while any backend work will be 
done on the individual pages in another folder.
******************************************************
"""
json_args_ = read_json()

class GroundControlApp(MDApp):
    
    def build(self):
        team_name = json_args_["team_NAME"]
        team_ID = json_args_["team_ID"]
        self.title = f'{team_name}-{team_ID}-Ground Control Station'
        self.icon = "../_static/icon.png"
        self.theme_cls.theme_style = json_args_["theme_style"]
        self.theme_cls.primary_palette = json_args_["primary_palette"]
        LabelBase.register(name='graph',
                   fn_regular='Ground_Station\_resources\VCR_OSD_MONO_1.001.ttf')

class WindowManager(MDScreenManager):
    pass

if __name__ == "__main__":
    file_path = 'cache'
    # * The code block you provided is responsible for clearing the GPS cache directory before running the
    # * application.
    clear_cache = False
    if clear_cache:
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            
    # * The sound_gen function creates all the voice overs for the flight states.
    # * If no internet, the function will stop itself. 
    # * States and sounds located in TEAMS_INFO folder json file.

    #sound_gen(json_args_['flight_states'])
    # ! Main function that runs app 
    GroundControlApp().run()
   
# ! =================================