from roads import OSMRoad, Road
from beamng_test_case import BeamNGTestCase
from pathlib import Path

from beamng_executor import BeamNGExecutor

if __name__ == "__main__":

    #SET UP
    #Set up paths
    MAIN_DIR = Path('C:\\Users\\tupol\\Documents\\Dissertation')
    BEAMNG_USER_PATH = MAIN_DIR / 'beamng_user' / '0.21'
    BEAMNG_HOME_PATH = MAIN_DIR / 'BeamNG.tech.v0.21.3.0'
    ROAD_FILE_PATH = BEAMNG_USER_PATH / 'levels' / "smallgrid" / 'main' / 'MissionGroup' / 'Roads' / 'items.level.json'

    road = OSMRoad(
        bbox=[49.978802, 19.847887, 50.100300, 20.038193],
        street_name="Zawiła",
        )
    test = BeamNGTestCase(road, ROAD_FILE_PATH, visualise=False)

    BeamNGExecutor(BEAMNG_HOME_PATH, BEAMNG_USER_PATH, test).execute()