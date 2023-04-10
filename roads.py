import uuid
import requests
import matplotlib.pyplot as plt
import numpy as np
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
from pathlib import Path
import json
from scipy.interpolate import splprep, splev
from geopy import distance
from shapely import MultiLineString, LineString, line_merge
np.set_printoptions(suppress=True)
from abc import ABC

class Road:

    def __init__(self, width=8, points=None, **kwargs) -> None:
        self.width = 8
        self.points = points

    @property
    def line_string(self):
        return LineString(self.points)

    @property
    def center(self):
        return np.mean(self.points, axis=0)

    @property
    def n_points(self):
        return self.points.shape[0]

    def _show(self):
        print(self.points)
        print(f"Length of road is {round(self.line_string.length, 2)} meters")
        plt.plot(self.points[:,0], self.points[:,1])
        ax = plt.gca()
        ax.set_aspect('equal', adjustable='box')
        plt.show()

    def _calculate_left_and_right_edge_point(self, p1, p2):
        '''
            Given two points from middle lane, calculates
            the point of left and right edge
        '''
        height = p1[2]
        origin = np.array(p1[0:2])
        next = np.array(p2[0:2])

        direction_v = np.subtract(next, origin)

        # calculate the vector which length is half the road width
        v = (direction_v / np.linalg.norm(direction_v)) * self.width / 2
        # add normal vectors
        left_point = origin + np.array([-v[1], v[0]])
        right_point = origin + np.array([v[1], -v[0]])

        #add origin height
        left_point = np.append(left_point, height)
        right_point = np.append(right_point, height)

        return left_point, right_point

    def vehicle_start_pose(self, meters_from_road_start=2.5):

        p1 = self.points[0]
        p2 = self.points[1]

        _, p1r = self._calculate_left_and_right_edge_point(p1, p2)
        p1r = p1r[0:2]

        direction = np.subtract(p2[0:2], p1[0:2])
        v = (direction / np.linalg.norm(direction)) * meters_from_road_start
        middle_of_lane = np.add(p1[0:2], p1r[0:2]) / 2 #making car spawn in the middle of right lane
        deg = np.degrees(np.arctan2([-v[0]], [-v[1]]))
        
        #around x, around y, around z here Z is up direction
        rot = (0, 0, deg[0])
        pos = tuple(middle_of_lane + v) + (p1[2],)

        return pos, rot


class OSMRoad(Road):
    def __init__(self, bbox, street_name, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bbox = bbox
        self.street_name = street_name

        self._download_street_points()
        self._add_elevation()
        self._project_points()

    def _project_points(self):
        #recenter
        mean_lonlat = np.mean(self.points[:, 0:2], axis=0)
        self.points[:, 0:2] -= mean_lonlat

        #scale
        LAT_DEGREE_IN_METERS = 111.2 * 1000
        EARTH_RADIUS_IN_METERS = 6371 * 1000

        lat = np.deg2rad(mean_lonlat[1])
        LON_DEGREE_IN_METERS = (np.pi/180)*EARTH_RADIUS_IN_METERS*np.cos(lat)

        self.points[:,0] *= LON_DEGREE_IN_METERS 
        self.points[:,1] *= LAT_DEGREE_IN_METERS 

        min_z = np.min(self.points[:, 2])
        self.points[:, 2] -= min_z #make the lowest point 0 level


    def _query(self):
        query = overpassQueryBuilder(
            bbox=self.bbox, elementType=['way'],
            includeGeometry=True, selector=f'"name"="{self.street_name}"')

        elements = Overpass().query(query).toJSON()['elements']
        return elements

    def _get_geometry(self, geom):
        points = [(point['lon'], point['lat']) for point in geom]
        points = np.array(points)
        return points

    def _download_street_points(self):

        ways = self._query()
        way_geometries = []
        for way in ways:
            g = self._get_geometry(way['geometry'])
            way_geometries.append(g)

        mls = MultiLineString(way_geometries)
        mls = line_merge(mls)

        if isinstance(mls, MultiLineString):
            #pick longest one
            lengths = [g.length for g in mls.geoms]
            longest = np.argmax(lengths)
            mls = mls.geoms[longest]
        
        self.points = np.array(mls.coords)

    def _add_elevation(self, dataset="eudem25m"):
        points_str = [f"{lat},{lon}" for lon, lat in self.points]
        locations = "|".join(points_str)
        response = requests.get(f"https://api.opentopodata.org/v1/{dataset}?locations={locations}")
        elevations = [p['elevation'] for p in response.json()['results']]
        self.points = np.column_stack((self.points, elevations))



if __name__ == "__main__":
    print(f"File {__file__} is not meant to run as main")