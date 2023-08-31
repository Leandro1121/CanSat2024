import json

def read_json(file_path = "ground_station_info"):
    
    """
    Read in json file with formats and different global variables
    """
    file_path_final = f'Team_Info/{file_path}.json'
    with open(file_path_final, mode="r") as j_object: 
        return json.load(j_object)