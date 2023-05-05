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
RESULTS_PATH = Path('results') / 'ga_osm'
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
    gen_counter = ga_instance.generations_completed
    test_name = f"GA road {gen_counter}-{solution_idx}"

    print(f"Evaluating road: {test_name}")
    points = np.array(solution).reshape(NUM_GA_POINTS, 3)
    road = Road(
            points=points,
            name=test_name
        )
    
    test = BeamNGTestCase(road, ROAD_FILE_PATH, max_speed=MAX_SPEED, visualise=False)
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
    

def initial_osm_population(path, k): #returns array of sol_per_pop arrays, each innter array has #NUM_GA_POINTS * 3 poins
    with open(path, "r") as f:
        test_cases = json.load(f)

    bbox = test_cases['bbox']
    streets = test_cases['streets']
    random_streets = random.sample(streets, k)
    initial_pop = []
    for street in random_streets:
        #generate a road that has NUM_GA_POINTS
        road = OSMRoad(bbox=bbox, street_name=street, max_points=NUM_GA_POINTS)
        initial_road = road.points.flatten().tolist()
        initial_pop.append(initial_road)

    return initial_pop

def on_new_generation(ga_instance):
    print("Generation : ", ga_instance.generations_completed)
    print("Fitness of the best solution :", ga_instance.best_solution()[1])

if __name__ == "__main__":

    sol_per_pop = 20
    initial_population = initial_osm_population("streets.json", sol_per_pop)
    print(initial_population)

    ga_instance = pygad.GA(num_generations=50,
                        num_parents_mating=sol_per_pop//2,
                        fitness_func=fitness_func,
                        sol_per_pop=sol_per_pop,
                        num_genes=NUM_GA_POINTS * 3, #XYZ,
                        mutation_percent_genes=10,
                        fitness_batch_size=1, #execute one test at a time
                        initial_population=initial_population,
                        on_generation=on_new_generation,
                        ) 
    ga_instance.run()