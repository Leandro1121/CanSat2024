# CanSat2024
## 2024 CanSat Competition under the SSDC Club
1. **Download Anaconda**
2. **Create and Activate Environments**
    - conda create -n CanSatEnv python=3.11
    - conda activate CanSatenv
    - conda install pip
3. **Run the requirments file** 
    - pip install -r requirements.txt
    - pip3 install -r requirements.txt
4. **Instructions Before Pushing to Repo**
    - pip freeze > requirements.txt
    - This downloads current versions of any packages

**Trouble Shooting Problems I've encountered:**
from kivy.garden.matplotlib.etc is not found, run
    garden install matplotlib --kivy
