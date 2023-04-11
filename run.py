import beamngpy
from beamngpy import BeamNGpy, Scenario, Vehicle
from roads import OSMRoad, Road
from beamng_test_case import BeamNGTestCase
from pathlib import Path

if __name__ == "__main__":

    #Set up paths
    MAIN_DIR = Path('C:\\Users\\tupol\\Documents\\Dissertation')
    BEAMNG_USER_PATH = MAIN_DIR / 'beamng_user' / '0.21'
    BEAMNG_HOME_PATH = MAIN_DIR / 'BeamNG.tech.v0.21.3.0'
    ROAD_FILE_PATH = BEAMNG_USER_PATH / 'levels' / "smallgrid" / 'main' / 'MissionGroup' / 'Roads' / 'items.level.json'

    RISK_VALUE = 0.7

    road = OSMRoad(
        bbox=[49.978802, 19.847887, 50.100300, 20.038193],
        street_name="Zawiła",
        )

    test = BeamNGTestCase(road, ROAD_FILE_PATH, visualise=True)

    test.write_road_to_level()

    # Instantiate BeamNGpy instance running the simulator from the given path,
    # communicating over localhost:64256
    bng = BeamNGpy('localhost', 64256, home=BEAMNG_HOME_PATH, user=BEAMNG_USER_PATH)
    # Launch BeamNG.tech
    bng.open(launch=True)
    beamngpy.logging.basicConfig(filename="beamng.log")
    vehicle = Vehicle('car', model='etk800', licence='OSM Testing', color='Blue')


    # Create a scenario in smallgrid called 'osm_testing'
    scenario = Scenario('smallgrid', 'osm_testing')


    # Add it to our scenario at this position and rotation
    pos, rot = test.vehicle_start_pose()

    scenario.add_vehicle(vehicle, pos=pos, rot=rot)
    # Place files defining our scenario for the simulator to read
    scenario.make(bng)

    bng.load_scenario(scenario)
    try:
        scenario.start()
    except Exception:
        pass
    input("Loading scenario done press enter enable AI")
    vehicle.ai_set_aggression(RISK_VALUE)
    vehicle.ai_set_speed(1000, mode='limit')
    vehicle.ai_drive_in_lane(True)
    vehicle.ai_set_waypoint(test.waypoint_name)

    input("Press enter to close it")
    bng.close()