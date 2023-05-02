import imp
import time
import beamngpy
from beamngpy import BeamNGpy, Scenario, Vehicle
from beamng_test_case import BeamNGTestCase
from pathlib import Path
import shapely
import numpy as np
import traceback
from abc import ABC, abstractmethod

class Executor(ABC):

    TIME_BUDGET = 60 #60secs
    GOAL_DISTANCE_THRESHOLD = 8 #if car is 8 meters from goal, the goal is reached

    @abstractmethod
    def _load(self):
        raise "Not Implemented"
    
    @abstractmethod
    def _run(self):
        raise "Not Implemented"
    
    def execute(self):
        self._load()
        self._run()

class BeamNGExecutor(Executor):

    def __init__(self, beamng_home: Path, beamng_user: Path, results_dir: Path, test_case: BeamNGTestCase, ai_on=True) -> None:

        beamngpy.logging.basicConfig(filename="beamng.log")
        self.beamng_home = beamng_home
        self.beamng_user = beamng_user
        self.results_dir = results_dir
        self.test_case = test_case
        self.ai_on = ai_on
        self.end = False
        

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
        # self.vehicle.ai_set_aggression(self.test_case.risk)
        self.vehicle.ai_set_speed(self.test_case.max_speed, mode='limit')
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
        # if oob > 0:
        #     from matplotlib import pyplot as plt
        #     plt.plot(
        #         *car.exterior.xy, "bo--",
        #         *lane.exterior.xy, "ro--",
        #         *diffrence.exterior.xy, "go--",
        #         )
        
        #     plt.show()
        #     input("Pres enter")
        return oob

    def _distance_to_goal(self):
        car = self._car_surface()
        goal = shapely.Point(self.test_case.waypoint_position)
        return car.distance(goal)
    
    def _has_no_time(self):
        now = time.time()
        elapsed = now-self.start_time
        return elapsed >= self.TIME_BUDGET
    
    def _goal_reached(self):
        d = self._distance_to_goal()
        return d < self.GOAL_DISTANCE_THRESHOLD
    
    def _check_end_conditions(self):
        if self._has_no_time():
            self.end = True
            self.test_case.execution_data['finish'] = "Out of time"
            self.test_case.execution_data['success'] = False
            print("Out of time, closing")

        if self._goal_reached():
            self.end = True
            self.test_case.execution_data['finish'] = "Goal Reached"
            self.test_case.execution_data['success'] = True
            print("Goal reached successfully quiting")

    def _read_execution_data(self):
        oob = self._oob_ratio()
        self.test_case.execution_data['out_of_bounds'].append(oob)
        msg = f"Oob: {oob:.2f}"

        self.vehicle.poll_sensors()
        if self.vehicle.state:
            pos = self.vehicle.state.get('pos')
            self.test_case.execution_data['position'].append(pos)

            vel = self.vehicle.state.get('vel')
            self.test_case.execution_data['velocity'].append(vel)

            msg += f", Position: {np.around(pos, 2)}, Velocity: {np.linalg.norm(vel):.2f} m/s"

        print(msg)

    def _tick(self):
        try:
            self._read_execution_data()
            self._check_end_conditions()
        except Exception as e:
            self.end = True
            self.test_case.execution_data['finish'] = f"Exception {e}"
            self.test_case.execution_data['success'] = False
            print(e.__repr__())

    def _run(self):
        #masks some stupid beamngy error
        try:
            self.scenario.start()
        except TypeError:
            pass

        self.start_time = time.time()
        while not self.end:
            self._tick()

            #tick every interval
            inter = self.test_case.interval
            time.sleep(inter - ((time.time() - self.start_time) % inter))

        self.test_case.save_execution_data(self.results_dir)
        self.bng.close()

