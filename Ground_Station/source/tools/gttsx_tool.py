from gtts import gTTS
import os

def sound_gen(commands:dict):
    file_path = 'Ground_Station\_recorded_audio'
    current_wd = os.getcwd()
    os.chdir(file_path)
    try:
        for key, value in commands.items():
            gtts = gTTS(value, slow=False, lang="es",tld = "us" )
            gtts.save(f'{key}.mp3')
    except:
        print("Internet Connection Needed")
    finally:
        os.chdir(current_wd)

