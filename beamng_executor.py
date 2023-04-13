import imp
import time
import beamngpy
from beamngpy import BeamNGpy, Scenario, Vehicle
from beamng_test_case import BeamNGTestCase
from pathlib import Path
import shapely

class BeamNGExecutor():

    def __init__(self, beamng_home: Path, beamng_user: Path, results_dir: Path, test_case: BeamNGTestCase, ai_on=True) -> None:

        beamngpy.logging.basicConfig(filename="beamng.log")
        self.beamng_home = beamng_home
        self.beamng_user = beamng_user
        self.results_dir = results_dir
        self.test_case = test_case
        self.ai_on = ai_on
        self.goal_reached = False
        
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

        if self.ai_on:
            self.vehicle_ai_setup()

    def vehicle_ai_setup(self):
        self.vehicle.ai_set_aggression(self.test_case.risk)
        self.vehicle.ai_set_speed(self.max_speed, mode='limit')
        self.vehicle.ai_drive_in_lane(True)
        self.vehicle.ai_set_waypoint(self.test_case.waypoint_name)

    def _car_surface(self) -> shapely.Polygon:
        car_box = self.vehicle.get_bbox()
        surface_points = [
            car_box['front_bottom_left'],
            car_box['front_bottom_right'],
            car_box['rear_bottom_right'],
            car_box['rear_bottom_left'],
        ]
        p = shapely.Polygon(surface_points)
        return p

    def _oob_ratio(self):
        car = self._car_surface()
        
        lane = self.test_case.road.right_lane_polygon
        diffrence = car.difference(lane)
        oob = diffrence.area/car.area
        # from matplotlib import pyplot as plt
        # plt.plot(
        #     *car.exterior.xy, "bo--",
        #     *lane.exterior.xy, "ro--",
        #     *diffrence.exterior.xy, "go--",
        #     )
        
        # oob = diffrence.area/car.area
        
        # plt.show()
        # input("Pres enter")
        return oob



    def _tick(self):
        #check if finished

        #update OOB stats
        oob = self._oob_ratio()
        print(oob)
        self.test_case.execution_data['out_of_bounds'].append(oob)

    def _run(self):
        #masks some stupid beamngy error
        try:
            self.scenario.start()
        except TypeError:
            pass

        starttime = time.time()
        # while not self.goal_reached:
        for _ in range(100):
            self._tick()

            #tick every interval
            inter = self.test_case.interval
            time.sleep(inter - ((time.time() - starttime) % inter))

        self.test_case.save_execution_data(self.results_dir)
        input("Press enter to close it")
        self.bng.close()

