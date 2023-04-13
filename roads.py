import uuid
import requests
import matplotlib.pyplot as plt
import numpy as np
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
from pathlib import Path
import json
from scipy.interpolate import splprep, splev
from geopy import distance
from shapely import MultiLineString, LineString, line_merge, Polygon
np.set_printoptions(suppress=True)
from abc import ABC

class Road:

    def __init__(self, width=8, points=None, name="Test Road", **kwargs) -> None:
        self.width = 8
        self.points = points
        self.name = name

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
        plt.plot(self.points[:,0], self.points[:,1], "--o")
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

    def _interpolate(self):
    
        SPLINE_DEGREE = 1
        INTERPOLATED_POINTS_FOR_EACH_POINT = 2
        
        pos_tck, _ = splprep(self.points.T, s=1, k=SPLINE_DEGREE)

        N_POINTS = self.n_points * INTERPOLATED_POINTS_FOR_EACH_POINT
        unew = np.linspace(0, 1, N_POINTS)

        interpolated = splev(unew, pos_tck) #retured as list of ND arrays
        self.points = np.array(interpolated).T


    def _right_lane_polygon(self) -> Polygon:

        polygon_points = np.copy(self.points[::-1])
        #iterate pair wise
        for previous, current in zip(self.points, self.points[1:]):
            _, right = self._calculate_left_and_right_edge_point(previous, current)
            right = right.reshape((1,3))
            polygon_points = np.append(polygon_points, right, axis=0)

        #add last point, as linear interpolation
        diff = polygon_points[-1] - polygon_points[-2]
        last_point = polygon_points[-1] + diff
        last_point = last_point.reshape((1,3))
        polygon_points = np.append(polygon_points, last_point, axis=0)
        p = Polygon(polygon_points)
        return p


class OSMRoad(Road):
    def __init__(self, bbox, street_name, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bbox = bbox
        self.street_name = street_name #for OSM query
        self.name = street_name #for test name


        self._download_street_points()
        self._add_elevation()
        self._project_points()
        self._shift_height()
        self._interpolate()
        
        self.right_lane_polygon = self._right_lane_polygon()

    def _shift_height(self):
        '''Shift down Z (up) axis'''
        min_z = np.min(self.points[:, 2])
        self.points[:, 2] -= min_z 
        self.points[:, 2] += 1     #make the lowest point at z=1

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