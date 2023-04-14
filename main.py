from roads import OSMRoad, Road
from beamng_test_case import BeamNGTestCase
from pathlib import Path
import json
from beamng_executor import BeamNGExecutor
import time

if __name__ == "__main__":

    #SET UP
    #Set up paths
    MAIN_DIR = Path('C:\\Users\\tupol\\Documents\\Dissertation')
    BEAMNG_USER_PATH = MAIN_DIR / 'beamng_user' / '0.21'
    BEAMNG_HOME_PATH = MAIN_DIR / 'BeamNG.tech.v0.21.3.0'
    ROAD_FILE_PATH = BEAMNG_USER_PATH / 'levels' / "smallgrid" / 'main' / 'MissionGroup' / 'Roads' / 'items.level.json'
    RESULTS_PATH = Path('results')
    MAX_SPEED = 26.8224 # 60mph Uk speed limit

    with open("streets.json", "r") as f:
        test_cases = json.load(f)

    bbox = test_cases['bbox']
    for street_name in test_cases['streets'][1:2]:

        print(f"Testing {street_name}")
        time.sleep(1)

        road = OSMRoad(
            bbox=bbox,
            street_name=street_name,
            )
        test = BeamNGTestCase(road, ROAD_FILE_PATH, max_speed=MAX_SPEED, visualise=True)

        BeamNGExecutor(beamng_home=BEAMNG_HOME_PATH,
                    beamng_user=BEAMNG_USER_PATH,
                    results_dir=RESULTS_PATH,
                    test_case=test,
                    ai_on=True).execute()