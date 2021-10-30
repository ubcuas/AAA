import logging
import heapq
import math
import numpy as np
import shapely.geometry as geom
import shapely.affinity as affin
import shapely.ops as ops
import networkx as nx

from fiona import collection
from common.utils.conversions import ll_to_utm, utm_to_ll

logger = logging.getLogger(__name__)

# All measurements are in meters

# ( long , Lat ) = ( x , y ) = ( 0 , 1 )

# Aircraft_Size (meters) - Higher EXTRA_RADIUS and lower SAFETY_FACTOR results in nicer curves
EXTRA_RADIUS = 15
SAFETY_FACTOR = 2

# Width between survey lines (meters)
SURVEY_WIDTH = 60

# Distance to lead in and out of each point
LEAD_DIST = 30

##############################################################################
##  File Operation Functions
##

def save_mission(waypoints, filename):
    mission_template = "{no}   0   3   {mptype}  {delay}.00000000  0.00000000  0.00000000  0.00000000  {latitude} {longitude}    {altitude}   1\n"
    with open(filename, "w") as outfile:
        outfile.write("QGC WPL 110\n")  # Default line to set up waypoint file
        no = 0
        for point in waypoints:
            point.update({"no": no,})

            mptype = 16
            if 'airdrop' in point['wp_type']:
                mptype = 17

            outfile.write(mission_template.format(**point, mptype=mptype))
            no = no + 1

def save_obstacles(obsticales, filename):
    schema = {'geometry': 'Polygon', 'properties': {'name': 'str'}}
    with collection(filename, "w", "ESRI Shapefile", schema) as output:
        for obs in obsticales:
            shapePoint = geom.Point(obs["longitude"], obs["latitude"])
            output.write({
                'properties': {
                    'name': 'obs'
                },
                'geometry': geom.mapping(shapePoint.buffer(obs["cylinder_radius"]))
            })

##
##
##############################################################################


##############################################################################
## A* Support Functions
##

def heuristic(a, b):
    (x1, y1, z1) = (a.longitude_m, a.latitude_m, a.altitude)
    (x2, y2, z2) = (a.longitude_m, a.latitude_m, a.altitude)
    dx = x1-x2
    dy = y1-y2
    return math.sqrt(dx**2 + dy**2)

def a_star_search(graph, start, goal):
    # logger.debug("A* Pathfinding start for %s to %s", start, goal)
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    goal_reached = None

    while not frontier.is_empty():
        current = frontier.get()

        if all(current[dimension] == goal[dimension] for dimension in ['latitude', 'longitude']):
            # logger.debug("A* Pathfinding complete for %s to %s", start, goal)
            goal_reached = True
            break

        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current

    if goal_reached:
        output = []
        prev = current
        while prev is not None:
            output.append(prev)
            prev = came_from[prev]
        output.reverse()
    else:
        logger.error("No valid path found for %s to %s", start, goal)
        output = [start, goal]

    return output

##
##
##############################################################################


##############################################################################
## Pathfinding Functions
##

def _find_path(waypoint_list, mission_map):
    # Perform the A* pathfinding for each set of points
    logger.debug("Starting A* pathfinding for each segment...")
    total_points = len(waypoint_list)
    count = 0

    avoided_points = []
    for index in range(0, total_points-1):
        if (count / total_points * 100) % 5 == 0:
            logger.info("A*: %s", count / total_points * 100)
        search_results = a_star_search(mission_map, waypoint_list[index], waypoint_list[index+1])
        avoided_points += search_results[:-1]  # Skip the last one since it is included in the previous
        count += 1

    logger.debug("A* pathfinding for each segment done!")

    # Since the last one is skipped every loop add on the final waypoint
    if len(waypoint_list) > 0:
        avoided_points.append(waypoint_list[-1])

    return avoided_points

def find_path(waypoint_list, obstacles_list, flyzone, flyzone_bounds):
    # Transform the obstacles into a obstacles object
    obstacles = [Obstacle(latitude=obs.latitude, longitude=obs.longitude, radius=obs.cylinder_radius, height=obs.cylinder_height) for obs in obstacles_list]

    # Generate the map object
    mission_map = Map(waypoint_list, obstacles, flyzone, flyzone_bounds)

    # Route and return the waypoints
    return _find_path(waypoint_list, mission_map), mission_map

##
##
##############################################################################


##############################################################################
## Route Post-Processing functions
##

def _do_expand_point(mission_map, start_wp, target_wp, finish_wp, rot_angle):
    output = []

    if start_wp is not None:
        incoming_line = geom.LineString([target_wp.as_tuple(), start_wp.as_tuple()])

        lead_in = affin.rotate(incoming_line, rot_angle, origin=target_wp.as_point(), use_radians=True)
        lead_in_point = lead_in.interpolate(LEAD_DIST).coords[0]
        lead_in_wp = Waypoint(latitude=lead_in_point[1], longitude=lead_in_point[0],
                                altitude=target_wp.altitude, invert_m_l=True, wp_type='auto_flight')
        output.append(lead_in_wp)

    output.append(target_wp)

    if finish_wp is not None:
        outgoing_line = geom.LineString([target_wp.as_tuple(), finish_wp.as_tuple()])

        lead_out = affin.rotate(outgoing_line, -rot_angle, origin=target_wp.as_point(), use_radians=True)
        lead_out_point = lead_out.interpolate(LEAD_DIST).coords[0]
        lead_out_wp = Waypoint(latitude=lead_out_point[1], longitude=lead_out_point[0],
                                altitude=target_wp.altitude, invert_m_l=True, wp_type='auto_flight')
        output.append(lead_out_wp)
    else:
        lead_out = affin.rotate(incoming_line, 180, origin=target_wp.as_point(), use_radians=False)
        lead_out_point = lead_out.interpolate(LEAD_DIST).coords[0]
        lead_out_wp = Waypoint(latitude=lead_out_point[1], longitude=lead_out_point[0],
                                altitude=target_wp.altitude, invert_m_l=True, wp_type='auto_flight')
        output.append(lead_out_wp)

    return output

def _expand_point(mission_map, start_wp, target_wp, finish_wp):
    if start_wp is not None and finish_wp is not None:
        incoming_vec = [start_wp.as_tuple()[x] - target_wp.as_tuple()[x] for x in (0,1,2)]
        outgoing_vec = [finish_wp.as_tuple()[x] - target_wp.as_tuple()[x] for x in (0,1,2)]

        inbetween_angle = np.arccos( np.dot(incoming_vec, outgoing_vec) / (np.linalg.norm(incoming_vec) * np.linalg.norm(outgoing_vec)) )
        rot_angle = (math.pi - inbetween_angle) / 2
    else:
        rot_angle = 0

    output = []
    output = _do_expand_point(mission_map, start_wp, target_wp, finish_wp, rot_angle)

    # Route adjust Case 0.5
    if start_wp is not None and finish_wp is not None:
        incoming_vec = [output[0].as_tuple()[x] - output[1].as_tuple()[x] for x in (0,1,2)]
        outgoing_vec = [output[2].as_tuple()[x] - output[1].as_tuple()[x] for x in (0,1,2)]

        inner_cos = np.dot(incoming_vec, outgoing_vec) / (np.linalg.norm(incoming_vec) * np.linalg.norm(outgoing_vec))
        inner_cos = np.clip(inner_cos, -1, 1)

        inbetween_angle = np.arccos( inner_cos )
        if not math.isclose(math.degrees(inbetween_angle), 180, abs_tol=2):
            output = _do_expand_point(mission_map, start_wp, target_wp, finish_wp, -1*rot_angle)

    # Route Exit Case 1
    if mission_map.valid_line(output[0], output[-1]) or start_wp is None:
        return output

    logger.debug("Line is going into backup case 2")
    overshot_base_line = geom.LineString([start_wp.as_tuple(), target_wp.as_tuple()])
    ratio = (overshot_base_line.length + LEAD_DIST) / overshot_base_line.length
    overshot_line = affin.scale(overshot_base_line, ratio, ratio, ratio, start_wp.as_tuple())
    overshot_point = overshot_line.coords[-1]

    output = [target_wp, Waypoint(latitude=overshot_point[1], longitude=overshot_point[0],
                                altitude=target_wp.altitude, invert_m_l=True, wp_type='auto_flight')]

    # Route Exit Case 2
    if mission_map.valid_line(output[0], output[-1]):
        return output

    logger.debug("Resorting to exit case 3")
    target_wp.delay = 1
    return [target_wp,]

def _lead_inout_mission_wps(mission_map, waypoint_list, obstacles_list, flyzone, flyzone_bounds):
    logger.debug("Starting Route Post-Processing...")
    total_points = len(waypoint_list)
    count = 0
    smoothed_points = []

    # Since the first is skipped use edgecase
    if len(waypoint_list) > 1:
        if "auto_flight" in waypoint_list[0].wp_type and not waypoint_list[0].is_generated:
            smoothed_points += _expand_point(mission_map, None, waypoint_list[0], waypoint_list[1])
        else:
            smoothed_points.append(waypoint_list[0])

    for index in range(1, total_points-1):
        if (count / total_points * 100) % 5 == 0:
            logger.info("A*: %s", count / total_points * 100)

        if "auto_flight" in waypoint_list[index].wp_type and not waypoint_list[index].is_generated:
            expand_results = _expand_point(mission_map, waypoint_list[index-1], waypoint_list[index], waypoint_list[index+1])
            smoothed_points += expand_results
        else:
            smoothed_points.append(waypoint_list[index])
        count += 1

    # Since the last one is skipped use edgecase
    if len(waypoint_list) > 1:
        if "auto_flight" in waypoint_list[-1].wp_type and not waypoint_list[-1].is_generated:
            smoothed_points += _expand_point(mission_map, waypoint_list[-2], waypoint_list[-1], None)
        else:
            smoothed_points.append(waypoint_list[-1])

    # Post route edgecase check
    if len(waypoint_list) <= 1:
        smoothed_points = waypoint_list

    logger.debug("Route Post-Processing done!")
    return smoothed_points

def post_process_path(prev_map, waypoint_list, obstacles_list, flyzone, flyzone_bounds):
    # Transform the obstacles into a obstacles object
    obstacles = [Obstacle(latitude=obs.latitude, longitude=obs.longitude, radius=obs.cylinder_radius, height=obs.cylinder_height) for obs in obstacles_list]

    # Expand out waypoints
    waypoint_list = _lead_inout_mission_wps(prev_map, waypoint_list, obstacles_list, flyzone, flyzone_bounds)

    # Generate the map object
    mission_map = Map(waypoint_list, obstacles, flyzone, flyzone_bounds)

    # Route the waypoints
    avoided_points = _find_path(waypoint_list, mission_map)

    # Return the waypoints in their dict format
    return [x.export_as_dict() for x in avoided_points]

##
##
##############################################################################


##############################################################################
## Base Route Drawing Functions
##

def _find_off_axis_point(flyzone, off_axis_odlc_pos, off_axis_odlc_line, altitude_msl):
    flyzone_points = [Waypoint(latitude=x.latitude, longitude=x.longitude, altitude=altitude_msl) for x in flyzone]
    flyzone_ring = geom.LinearRing([(x.longitude_m, x.latitude_m) for x in flyzone_points])

    # Check if off_axis within flyzone
    if off_axis_odlc_pos.as_point().intersects(geom.Polygon(flyzone_ring)):
        return [off_axis_odlc_pos,]

    # Get closest point just inside flyzone
    buffered_ring = flyzone_ring.buffer(EXTRA_RADIUS)
    intersecting_line = off_axis_odlc_line.intersection(buffered_ring)
    poi = intersecting_line.coords[0]
    return [Waypoint(latitude=poi[1], longitude=poi[0], altitude=altitude_msl, invert_m_l=True, wp_type='off_axis'),]

def _draw_search_grid(short_p, search_grid_points, altitude_msl):
    def _calc_point(original_point, length, angle):
        x_prime = original_point.x + length * math.cos(angle)
        y_prime = original_point.y + length * math.sin(angle)
        return geom.Point(x_prime, y_prime)

    longest_idx = 0
    longest_len = 0
    for x in range(0, len(search_grid_points)):
        cur_p = search_grid_points[x]
        line = geom.LineString([(short_p.longitude_m, short_p.latitude_m), (cur_p.longitude_m, cur_p.latitude_m)])

        if line.length > longest_len:
            longest_idx = x
            longest_len = line.length
    long_p = search_grid_points[longest_idx]

    follow_line = geom.LineString([(short_p.longitude_m, short_p.latitude_m), (long_p.longitude_m, long_p.latitude_m)])
    fl_ends = list(follow_line.coords)
    cut_line_slope = -1 * (fl_ends[1][0] - fl_ends[0][0]) / (fl_ends[1][1] - fl_ends[0][1])
    cut_line_angle = math.atan(cut_line_slope)

    grids = math.floor(follow_line.length / SURVEY_WIDTH)
    search_grid_ring = geom.LinearRing([(x.longitude_m, x.latitude_m) for x in search_grid_points])
    calculated_grid_points = [(short_p.longitude_m, short_p.latitude_m),] # Should start at the grid start point
    for x in range(1, grids):
        m_p = follow_line.interpolate(SURVEY_WIDTH * x)

        # Create line to right, create line to left
        l_point = _calc_point(m_p, -longest_len, cut_line_angle)
        r_point = _calc_point(m_p, longest_len, cut_line_angle)
        scan_line = geom.LineString([l_point, m_p, r_point])

        # Get intersection points
        intersections = scan_line.intersection(search_grid_ring)
        intersections_list = list(intersections)

        if x % 2:
            intersections_list.reverse()

        for c in range(len(intersections_list)):
            calculated_grid_points += list(intersections_list[c].coords)

    return [Waypoint(longitude=x[0], latitude=x[1], altitude=altitude_msl, invert_m_l=True, wp_type='search_grid') for x in calculated_grid_points]

def _calculate_odlc_search(flyzone, start_point, search_grid_points, off_axis_odlc_pos, altitude_msl=35):
    # off_axis_odlc_pos = Waypoint(latitude=off_axis_odlc_pos.latitude, longitude=off_axis_odlc_pos.longitude, altitude=altitude_msl, is_generated=False, wp_type='off_axis')
    search_grid_points = [Waypoint(latitude=x.latitude, longitude=x.longitude, altitude=altitude_msl, is_generated=False) for x in search_grid_points]

    shortest_idx = 0
    shortest_len = 100000000
    for x in range(0, len(search_grid_points)):
        cur_p = search_grid_points[x]
        line = geom.LineString([(start_point.longitude_m, start_point.latitude_m), (cur_p.longitude_m, cur_p.latitude_m)])

        if line.length < shortest_len:
            shortest_idx = x
            shortest_len = line.length
    short_p = search_grid_points[shortest_idx]

    search_grid_grid_points = _draw_search_grid(short_p, search_grid_points, altitude_msl)
    return search_grid_grid_points

    # off_axis_line = geom.LineString([(start_point.longitude_m, start_point.latitude_m),
    #                                  (off_axis_odlc_pos.longitude_m, off_axis_odlc_pos.latitude_m)])

    # if off_axis_line.length > shortest_len:
    #     return search_grid_grid_points + _find_off_axis_point(flyzone, off_axis_odlc_pos, off_axis_line, altitude_msl)
    # else:
    #     return _find_off_axis_point(flyzone, off_axis_odlc_pos, off_axis_line, altitude_msl) + search_grid_grid_points

def _draw_airdrop(airdrop_pos, altitude_msl=35):
    return [Waypoint(latitude=airdrop_pos.latitude, longitude=airdrop_pos.longitude, altitude=altitude_msl, is_generated=False, wp_type='airdrop')]

def _draw_auto_route(auto_flight_wps):
    auto_route_points = [Waypoint(latitude=x.latitude, longitude=x.longitude, altitude=x.altitude_msl, is_generated=False, wp_type='auto_flight') for x in auto_flight_wps]
    return auto_route_points

def draw_complete_route(flyzone, auto_flight_wps, airdrop_pos, search_grid_wps, off_axis_odlc_pos):
    base_route = []
    base_route += _draw_auto_route(auto_flight_wps)
    base_route += _draw_airdrop(airdrop_pos)
    base_route += _calculate_odlc_search(flyzone, base_route[-1], search_grid_wps, off_axis_odlc_pos)

    return base_route

##
##
##############################################################################


##############################################################################
## Classes
##

class Obstacle():
    as_Circle = None
    height = None

    def __init__(self, latitude, longitude, radius, height):
        self.as_Circle = geom.Point(*ll_to_utm(longitude, latitude)).buffer(radius)
        self.height = height

class Waypoint():
    latitude = 0.0
    latitude_m = 0.0

    longitude = 0.0
    longitude_m = 0.0

    altitude = 0.0
    is_generated = True
    delay = 0

    wp_type = "none"
    _choices = ('none','auto_flight', 'airdrop', 'search_grid', 'off_axis')

    _as_point = None
    _as_tuple = None

    def __init__(self, latitude, longitude, altitude, is_generated=True, wp_type='none', invert_m_l=False):
        if not invert_m_l:
            self.longitude, self.latitude = longitude, latitude
            self.longitude_m, self.latitude_m = ll_to_utm(longitude, latitude)
        else:
            self.longitude, self.latitude = utm_to_ll(longitude, latitude)
            self.longitude_m, self.latitude_m = longitude, latitude

        self.altitude = altitude

        self.is_generated = is_generated

        if wp_type in self._choices:
            self.wp_type = wp_type

    def __getitem__(self, key):
        if key == 'latitude':
            return self.latitude_m
        if key == 'longitude':
            return self.longitude_m
        if key == 'altitude':
            return self.altitude
        # Else
        return None

    def __lt__(self, other):
        return self.latitude+self.longitude < other.latitude+other.longitude

    def convert_m_to_l(self):
        self.latitude_m = self.latitude
        self.longitude_m = self.longitude

        self.longitude, self.latitude = utm_to_ll(self.longitude_m, self.latitude_m)

    def export_as_dict(self):
        return {'latitude': self.latitude, 'longitude': self.longitude, 'altitude': self.altitude,
                'is_generated': self.is_generated, 'wp_type': self.wp_type, 'delay': self.delay}

    def as_point(self):
        if not self._as_point:
            self._as_point = geom.Point(self.longitude_m, self.latitude_m)
        return self._as_point

    def as_tuple(self):
        if not self._as_tuple:
            self._as_tuple = (self.longitude_m, self.latitude_m, self.altitude)
        return self._as_tuple

class Map:
    def __init__(self, waypoint_list, obstacles, flyzone, flyzone_bounds):
        self.obstacle_union = self._convert_obs_to_union(obstacles)
        self.flyzone_obj = self._convert_flyzone_to_polygon(flyzone)

        logger.info("Starting map preprocessing...")
        possible_points = waypoint_list.copy()
        possible_points += self._convert_obs_to_points(obstacles)
        possible_points += self._convert_flyzone_to_points()

        self.graph = nx.Graph()
        self.graph.add_nodes_from(possible_points)

        total_nodes = self.graph.number_of_nodes()
        num_nodes_checked = 0

        loading_milestone = 10.0

        visited_nodes = dict({})

        for s_node in self.graph.nodes:
            if (num_nodes_checked / total_nodes * 100) >= loading_milestone:
                logger.info("Preprocessing: %.1f", loading_milestone)
                loading_milestone = loading_milestone + 10.0
            for e_node in self.graph.nodes:
                if s_node == e_node:
                    continue
                elif e_node in visited_nodes.keys():
                    continue
                elif self.valid_line(s_node, e_node):
                    self.graph.add_edge(s_node, e_node)
            num_nodes_checked += 1
            visited_nodes[s_node] = True
        logger.info("Map preprocessing done!")

    def _convert_obs_to_points(self, obstacles, altitude=40):
        points = []
        for obs in obstacles:
            buffered_obstacle = obs.as_Circle.buffer(EXTRA_RADIUS*SAFETY_FACTOR)
            buffered_obstacle.simplify(0.2, preserve_topology=False)
            points += [Waypoint(longitude=c[0], latitude=c[1], altitude=altitude, invert_m_l=True) for c in buffered_obstacle.exterior.coords]
        return points

    def _convert_obs_to_union(self, obstacles):
        buffered_obstacles = [obs.as_Circle.buffer(EXTRA_RADIUS) for obs in obstacles]
        buffered_obstacle_union = ops.cascaded_union(buffered_obstacles)
        return buffered_obstacle_union

    def _convert_flyzone_to_points(self, altitude=40):
        return [Waypoint(longitude=c[0], latitude=c[1], altitude=altitude, invert_m_l=True) for c in self.flyzone_obj.buffer(-EXTRA_RADIUS*(SAFETY_FACTOR-1)).exterior.coords]

    def _convert_flyzone_to_polygon(self, flyzone):
        return geom.Polygon([ll_to_utm(x.longitude, x.latitude) for x in flyzone]).buffer(-EXTRA_RADIUS)

    def neighbors(self, point):
        return [key for key, value in self.graph.adj[point].items()]

    def cost(self, start_point, end_point):
        (x1, y1, z1) = (start_point.longitude_m, start_point.latitude_m, start_point.altitude)
        (x2, y2, z2) = (end_point.longitude_m, end_point.latitude_m, end_point.altitude)
        dx = x1-x2
        dy = y1-y2
        return math.sqrt(dx**2 + dy**2)

    def valid_line(self, start_point, end_point):
        line = geom.LineString((start_point.as_tuple(), end_point.as_tuple()))
        # return not line.intersects(self.obstacle_union)
        return line.within(self.flyzone_obj) and not line.intersects(self.obstacle_union)

class PriorityQueue:
    def __init__(self):
        self.elements = []

    def is_empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]

##
##
##############################################################################
