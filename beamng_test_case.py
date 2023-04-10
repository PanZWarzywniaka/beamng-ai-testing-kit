from roads import Road
import uuid
import numpy as np
import json
from pathlib import Path


class BeamNGTestCase:
    def __init__(self, r: Road, file_path: Path, visualise:bool = False) -> None:
        self.road = r
        self.file_path = file_path
        self.waypoint_name = "GoalWaypoint"

        if visualise:
            self.road._show()
    
    @property
    def decal_road_json(self):

        road_width_column = np.full(self.road.n_points, self.road.width)
        nodes = np.column_stack((self.road.points, road_width_column))

        return {"class": "DecalRoad",
            "persistentId": str(uuid.uuid4()), 
            "__parent": "Roads", 
            "position": [0, 0, 0], 
            "Material": "a_asphalt_01_a", 
            "drivability": 1, 
            "improvedSpline": True, 
            "nodes": nodes.tolist(), 
            "order_simset": 7, 
            "overObjects": True
        }
    @property
    def mesh_road_json(self):

        mesh_road_width = self.road.width*3
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
    def waypoint_json(self):

        return {
        'name': self.waypoint_name,
        'class': 'BeamNGWaypoint',
        'persistentId': str(uuid.uuid4()),
        '__parent': 'Roads',
        'position': self.road.points[-1].tolist(),
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

    def vehicle_start_pose(self, meters_from_road_start=2.5):

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
        pos = tuple(middle_of_lane + v) + (p1[2],)

        return pos, rot
    ##start finish collect data


if __name__ == "__main__":
    print(f"File {__file__} is not meant to run as main")