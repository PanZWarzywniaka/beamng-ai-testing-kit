from roads import OSMRoad, Road
from beamng_test_case import BeamNGTestCase
from pathlib import Path
import json
from beamng_executor import BeamNGExecutor
import time
import random


def get_k_random_streets_from_file(path: Path, k: int):
    with open(path, "r") as f:
        test_cases = json.load(f)

    bbox = test_cases['bbox']
    streets = test_cases['streets']
    random_streets = random.sample(streets, k)
    return bbox, random_streets

if __name__ == "__main__":

    #SET UP
    #Set up paths
    MAIN_DIR = Path('C:\\Users\\tupol\\Documents\\Dissertation')
    BEAMNG_USER_PATH = MAIN_DIR / 'beamng_user' / '0.21'
    BEAMNG_HOME_PATH = MAIN_DIR / 'BeamNG.tech.v0.21.3.0'
    ROAD_FILE_PATH = BEAMNG_USER_PATH / 'levels' / "smallgrid" / 'main' / 'MissionGroup' / 'Roads' / 'items.level.json'
    RESULTS_PATH = Path('results') / 'osm'
    MAX_SPEED = 26.8224 # 60mph Uk speed limit
    K_TESTS = 5

    bbox, streets = get_k_random_streets_from_file("streets.json", K_TESTS)

    for i, street_name in enumerate(streets):

        print(f"{i+1}/{K_TESTS}: {street_name}")
        time.sleep(1)

        road = OSMRoad(
            bbox=bbox,
            street_name=street_name,
            )
        test = BeamNGTestCase(road, ROAD_FILE_PATH, max_speed=MAX_SPEED, visualise=False)

        BeamNGExecutor(beamng_home=BEAMNG_HOME_PATH,
                    beamng_user=BEAMNG_USER_PATH,
                    results_dir=RESULTS_PATH,
                    test_case=test,
                    ai_on=True).execute()