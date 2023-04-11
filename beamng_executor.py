import time
import beamngpy
from beamngpy import BeamNGpy, Scenario, Vehicle
from beamng_test_case import BeamNGTestCase
from pathlib import Path

class BeamNGExecutor():

    def __init__(self, beamng_home: Path, beamng_user: Path, test_case: BeamNGTestCase,
        risk: float = 0.7, max_speed: float = 100.0) -> None:

        beamngpy.logging.basicConfig(filename="beamng.log")
        self.beamng_home = beamng_home
        self.beamng_user = beamng_user
        self.test_case = test_case
        self.goal_reached = False
        self.risk = risk
        self.max_speed = max_speed

    def execute(self):
        self._load()
        self._run()

    def _load(self):
        self.test_case.write_road_to_level()
         # Instantiate BeamNGpy instance running the simulator from the given path,
        # communicating over localhost:64256
        self.bng = BeamNGpy('localhost', 64256, home=self.beamng_home, user=self.beamng_user)
        # Launch BeamNG.tech
        self.bng.open(launch=True)
        
        self.vehicle = Vehicle('car', model='etk800', licence='OSM Testing', color='Blue')


        # Create a scenario in smallgrid called 'osm_testing'
        self.scenario = Scenario('smallgrid', 'osm_testing')


        # Add it to our scenario at this position and rotation
        pos, rot = self.test_case.vehicle_start_pose()

        self.scenario.add_vehicle(self.vehicle, pos=pos, rot=rot)
        # Place files defining our scenario for the simulator to read
        self.scenario.make(self.bng)

        self.bng.load_scenario(self.scenario) 

        self.vehicle.ai_set_aggression(self.risk)
        self.vehicle.ai_set_speed(self.max_speed, mode='limit')
        self.vehicle.ai_drive_in_lane(True)
        self.vehicle.ai_set_waypoint(self.test_case.waypoint_name)


    def _tick(self):
        #check if finished

        #update OOB stats
        print("tick")


    def _run(self, interval = 0.25):
        #masks some stupid beamngy error
        try:
            self.scenario.start()
        except TypeError:
            pass

        starttime = time.time()

        #tick every interval
        while not self.goal_reached:
            self._tick()
            time.sleep(interval - ((time.time() - starttime) % interval))


        input("Press enter to close it")
        self.bng.close()

