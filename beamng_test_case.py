from roads import Road
import uuid
import numpy as np
import json
from pathlib import Path


class BeamNGTestCase:

    HARD_SHOULDER_WIDTH = 1 #meter, in the UK for non-motorway roads

    def __init__(self, r: Road, file_path: Path, visualise:bool = False,
    interval:float = 0.1, risk: float = 0.5, max_speed: float = 100.0) -> None:
        self.road = r
        self.file_path = file_path
        self.waypoint_name = "GoalWaypoint"

        self.interval = interval
        self.risk = risk
        self.max_speed = max_speed
        self.execution_data = {}
        self._init_execution_data()

        if visualise:
            self.road._show()
    
    def _init_execution_data(self):
        self.execution_data['name'] = self.road.name
        self.execution_data['length'] = self.road.line_string.length
        self.execution_data['n_points'] = self.road.n_points
        self.execution_data['points'] = self.road.points.tolist()

        
        self.execution_data['tick_interval'] = self.interval
        self.execution_data['speed_limit'] = self.max_speed
        self.execution_data['risk_value'] = self.risk

        #filled by executor
        self.execution_data['finish'] = "Not finished"
        self.execution_data['out_of_bounds'] = []
        self.execution_data['position'] = []
        self.execution_data['velocity'] = []

    def save_execution_data(self, dir: Path):
        target_path = dir / f"{self.road.name}.json"
        with open(target_path, 'w') as f:
            json.dump(self.execution_data, f)

    @property
    def decal_road_json(self):

        road_width_column = np.full(self.road.n_points, self.road.width)
        nodes = np.column_stack((self.road.points, road_width_column))

        return {"class": "DecalRoad",
            "persistentId": str(uuid.uuid4()), 
            "__parent": "Roads", 
            "position": [0, 0, 0], 
            "Material": "tig_road_rubber_sticky", 
            "drivability": 1, 
            "improvedSpline": True, 
            "nodes": nodes.tolist(), 
            "order_simset": 7, 
            "overObjects": True
        }
    @property
    def mesh_road_json(self):

        #withd of the road plus hard shoulder from both sides
        mesh_road_width = self.road.width + 2*self.HARD_SHOULDER_WIDTH 
        road_width_column = np.full(self.road.n_points, mesh_road_width)
        road_height_column = self.road.points[:,2] #match heigth with Z
        
        other_params_columns = np.repeat([[0.0, 0.0, 1.0]], self.road.n_points, axis=0)
        nodes = np.column_stack((self.road.points, road_width_column, road_height_column, other_params_columns))
        return {
            "name": "NewMeshRoad",
            "class": "MeshRoad",
            "persistentId": str(uuid.uuid4()),
            "__parent": "Roads",
            "bottomMaterial": "track_editor_grid",
            "nodes": nodes.tolist(), 
            "order_simset": 8,
            "sideMaterial": "track_editor_grid", 
            "topMaterial": "track_editor_grid"
        }

    @property
    def waypoint_position(self) -> list:
        #x,y,z
        second_to_last = self.road.points[-2]
        last_point = self.road.points[-1]
        dir = last_point-second_to_last
        _, r = self.road._calculate_left_and_right_edge_point(
            last_point, last_point+dir
        )
        ret = (last_point+r) / 2
        return ret.tolist()
    @property
    def waypoint_json(self):

        return {
        'name': self.waypoint_name,
        'class': 'BeamNGWaypoint',
        'persistentId': str(uuid.uuid4()),
        '__parent': 'Roads',
        'position': self.waypoint_position,
        'scale': [self.road.width]*3, #x y z size
        }

    @classmethod
    def write_json(cls, json_data, file_handler):
        json.dump(json_data, file_handler) #dump json in one line
        file_handler.write("\n") #go to new line

    def write_road_to_level(self):
        with open(self.file_path, 'w') as f:
            self.write_json(self.decal_road_json, f)
            self.write_json(self.mesh_road_json, f)
            self.write_json(self.waypoint_json, f)

        print(f"Road written to: \n {self.file_path}")

    def vehicle_start_pose(self, meters_from_road_start=3.5):

        p1 = self.road.points[0]
        p2 = self.road.points[1]

        _, p1r = self.road._calculate_left_and_right_edge_point(p1, p2)
        p1r = p1r[0:2]

        direction = np.subtract(p2[0:2], p1[0:2])
        v = (direction / np.linalg.norm(direction)) * meters_from_road_start
        middle_of_lane = np.add(p1[0:2], p1r[0:2]) / 2 #making car spawn in the middle of right lane
        deg = np.degrees(np.arctan2([-v[0]], [-v[1]]))
        
        #around x, around y, around z here Z is up direction
        rot = (0, 0, deg[0])

        h1 = p1[2]
        h2 = p2[2]
        pos = tuple(middle_of_lane + v) + (max(h1,h2),)

        return pos, rot

    # def vehicle_start_pose(self, meters_from_road_start=3.5):

    #     p1 = self.road.points[0]
    #     p2 = self.road.points[1]

    #     _, p1r = self.road._calculate_left_and_right_edge_point(p1, p2)

    #     direction = np.subtract(p2, p1)
    #     v = (direction / np.linalg.norm(direction)) * meters_from_road_start
    #     middle_of_lane = (p1 + p1r) / 2 #making car spawn in the middle of right lane
        
    #     # Rotation angle around X axis
    #     theta_x = np.degrees(np.arctan2(v[1], v[2]))  # Rotation around X axis
    #     theta_y = np.degrees(np.arctan2(v[0], np.sqrt(v[1]**2 + v[2]**2)))  # Rotation around Y axis
    #     theta_z = np.degrees(np.arctan2(v[1], v[0]))  # Rotation around Z axis

    #     #around x, around y, around z here Z is up direction
    #     rot = (theta_x, theta_y, theta_z)
    #     pos = tuple(middle_of_lane + v)

    #     return pos, rot

if __name__ == "__main__":
    print(f"File {__file__} is not meant to run as main")