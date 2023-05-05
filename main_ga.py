from roads import OSMRoad, Road
from beamng_test_case import BeamNGTestCase
from pathlib import Path
import json
from beamng_executor import BeamNGExecutor
import time
import random
import pygad
import numpy as np

MAIN_DIR = Path('C:\\Users\\tupol\\Documents\\Dissertation')
BEAMNG_USER_PATH = MAIN_DIR / 'beamng_user' / '0.21'
BEAMNG_HOME_PATH = MAIN_DIR / 'BeamNG.tech.v0.21.3.0'
ROAD_FILE_PATH = BEAMNG_USER_PATH / 'levels' / "smallgrid" / 'main' / 'MissionGroup' / 'Roads' / 'items.level.json'
RESULTS_PATH = Path('results') / 'ga'
MAX_SPEED = 13.4112 # 30mph Uk speed limit for residential roads
MAX_ROAD_LENGTH = 2000 #meters
MIN_ROAD_LENGTH = 100 #meters
NUM_GA_POINTS = 10

#evaluates execution
def score(execution_data: dict) -> float:
    if not execution_data['success']:
        return -1
    
    oobs = execution_data['out_of_bounds']
    length = execution_data['length']
    OOBS_RATION_VALUE = 100
    score = (sum(oobs) / length) * OOBS_RATION_VALUE
    return score

def fitness_func(ga_instance, solution, solution_idx):
    print(f"Evaluating road: {solution_idx}")
    points = np.array(solution).reshape(NUM_GA_POINTS, 3)
    road = Road(
            points=points,
            name=f"GA road"
        )
    
    test = BeamNGTestCase(road, ROAD_FILE_PATH, max_speed=MAX_SPEED, visualise=True)
    if not test.is_valid():
        return -1
    
    BeamNGExecutor(beamng_home=BEAMNG_HOME_PATH,
                beamng_user=BEAMNG_USER_PATH,
                results_dir=RESULTS_PATH,
                test_case=test,
                ai_on=True).execute()
    
    fitness = score(test.execution_data)
    print(f"Fitness value: {fitness}")
    return fitness
    

def rand_population():
    sol = []
    for i in range(NUM_GA_POINTS):   
        x = random.randint(0+(10*i), 10+(10*i))
        y = random.randint(0+(10*i), 10+(10*i)) 
        z = random.randint(1, 5)
        sol += [x, y, z]

    return sol

if __name__ == "__main__":

    sol_per_pop = 8
    initial_population = [
        rand_population() for _ in range(sol_per_pop)]
    print(initial_population)

    ga_instance = pygad.GA(num_generations=50,
                        num_parents_mating=4,
                        fitness_func=fitness_func,
                        sol_per_pop=sol_per_pop,
                        num_genes=NUM_GA_POINTS * 3, #XYZ,
                        mutation_percent_genes=10,
                        fitness_batch_size=1,#execute one test at a time
                        init_range_high=500,
                        init_range_low=-500,
                        initial_population=initial_population,
                        ) 
    ga_instance.run()