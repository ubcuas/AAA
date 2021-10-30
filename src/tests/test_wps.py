from django.test import TestCase

import avoidance.waypoint_system as wps

from interop.models import OrderedWayPoint, OrderedBoundaryPoint, Obstacle, GpsPosition

def is_valid_route(waypoints, obstacles, flyzone):
    """Buckle up, this is one expensive test"""
    import shapely.geometry as geom
    import shapely.ops as ops
    from common.utils.conversions import ll_to_utm

    wp_tuples = [ll_to_utm(x['longitude'], x['latitude']) for x in waypoints]
    obs = ops.cascaded_union([geom.Point(*ll_to_utm(x.longitude, x.latitude)).buffer(x.cylinder_radius) for x in obstacles])
    fz = geom.Polygon([ll_to_utm(x.longitude, x.latitude) for x in flyzone])

    for index in range(0, len(wp_tuples)-1):
        line = geom.LineString((wp_tuples[index], wp_tuples[index+1]))
        if line.intersects(obs) or not line.within(fz):
            print(line.intersects(obs), "-", line, "-", line.intersection(obs))
            print(not line.within(fz))
            return False
    return True

class Test_WPS_find_path(TestCase):
    def test_no_waypoint(self):
        waypoint_list = []
        obstacle_list = []
        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)

        expected_waypoints = []
        self.assertEqual(expected_waypoints, new_waypoints)

    def test_single_waypoint(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.425, altitude=64, is_generated=False, wp_type="auto_flight"),]
        obstacle_list = []
        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)

        expected_waypoints = [{'latitude': 38.140, 'longitude': -76.425, 'altitude': 64, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},]
        self.assertEqual(expected_waypoints, new_waypoints)

    def test_single_segment(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=200, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.150, longitude=-76.440, altitude=200, is_generated=False, wp_type="auto_flight")]

        obstacle_list = [Obstacle(latitude=38.145, longitude=-76.430, cylinder_height=750, cylinder_radius=91.44),]

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_single_segment_multi_obs_conccentric(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=200, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.150, longitude=-76.440, altitude=200, is_generated=False, wp_type="auto_flight")]

        obstacle_list = [Obstacle(latitude=38.145, longitude=-76.430, cylinder_height=750, cylinder_radius=91.44),
                         Obstacle(latitude=38.145, longitude=-76.430, cylinder_height=750, cylinder_radius=76.2)]

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_single_segment_multi_obs_overlapping(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=200, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.150, longitude=-76.440, altitude=200, is_generated=False, wp_type="auto_flight")]

        obstacle_list = [Obstacle(latitude=38.145, longitude=-76.430, cylinder_height=750, cylinder_radius=91.44),
                         Obstacle(latitude=38.1455, longitude=-76.4305, cylinder_height=750, cylinder_radius=152.4)]

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_single_segment_no_obs(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=200, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.150, longitude=-76.440, altitude=200, is_generated=False, wp_type="auto_flight")]

        obstacle_list = [Obstacle(latitude=30.25000, longitude=-70.25000, cylinder_height=750, cylinder_radius=300),]

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_multi_segment(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=60.96, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.145, longitude=-76.430, altitude=60.96, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.150, longitude=-76.440, altitude=60.96, is_generated=False, wp_type="auto_flight")]

        obstacle_list = [Obstacle(latitude=38.1425, longitude=-76.425, cylinder_height=750, cylinder_radius=3.048),
                         Obstacle(latitude=38.1475, longitude=-76.435, cylinder_height=750, cylinder_radius=152.4)]

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_multi_segment_no_obs(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=60.96, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.145, longitude=-76.430, altitude=60.96, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.150, longitude=-76.440, altitude=60.96, is_generated=False, wp_type="auto_flight")]

        obstacle_list = []

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=2),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=3),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=4),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_single_segment_cross_angled_jut_flyzone(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=60.96, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.140, longitude=-76.440, altitude=60.96, is_generated=False, wp_type="auto_flight")]

        obstacle_list = []

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.425, order=2),  # Jut
                        OrderedBoundaryPoint(latitude=38.142, longitude=-76.430, order=3),  # Jut
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.435, order=4),  # Jut
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=5),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=6),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=7),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

    def test_single_segment_cross_flat_jut_flyzone(self):
        waypoint_list = [wps.Waypoint(latitude=38.140, longitude=-76.420, altitude=60.96, is_generated=False, wp_type="auto_flight"),
                         wps.Waypoint(latitude=38.140, longitude=-76.440, altitude=60.96, is_generated=False, wp_type="auto_flight")]

        obstacle_list = []

        flyzone_list = [OrderedBoundaryPoint(latitude=38.138, longitude=-76.415, order=1),
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.425, order=2),  # Jut
                        OrderedBoundaryPoint(latitude=38.142, longitude=-76.425, order=3),  # Jut
                        OrderedBoundaryPoint(latitude=38.142, longitude=-76.435, order=3),  # Jut
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.435, order=4),  # Jut
                        OrderedBoundaryPoint(latitude=38.138, longitude=-76.445, order=5),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.445, order=6),
                        OrderedBoundaryPoint(latitude=38.155, longitude=-76.415, order=7),]
        flyzone_bounds = (10, 210)

        new_waypoints, mission_map = wps.find_path(waypoint_list, obstacle_list, flyzone_list, flyzone_bounds)
        new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacle_list, flyzone_list, flyzone_bounds)
        self.assertTrue(is_valid_route(new_waypoints, obstacle_list, flyzone_list))

# class Test_WPS_calculate_odlc_search(TestCase):
#     def test_case_default(self):
#         """
#         Test case where:
#         - Search grid is closer
#         - Off_Axis is outside flyzone
#         """
#         search_grid_list = []
#         search_grid_list.append(wps.Waypoint(latitude=38.0, longitude=-76.0, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.1, longitude=-76.0, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.1, longitude=-76.1, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.0, longitude=-76.1, altitude=60.96, is_generated=False, wp_type="search_grid"))

#         flyzone_list = []
#         flyzone_list.append(OrderedBoundaryPoint(latitude=37.5, longitude=-75.5, order=1))
#         flyzone_list.append(OrderedBoundaryPoint(latitude=38.15, longitude=-75.5, order=2))
#         flyzone_list.append(OrderedBoundaryPoint(latitude=38.15, longitude=-76.15, order=3))
#         flyzone_list.append(OrderedBoundaryPoint(latitude=37.5, longitude=-76.15, order=4))

#         off_axis_odlc_pos = wps.Waypoint(latitude=38.6, longitude=-74.6, altitude=60.96, is_generated=False, wp_type="off_axis")
#         start_point = wps.Waypoint(latitude=37.6, longitude=-75.6, altitude=60.96, is_generated=False, wp_type="auto_flight")

#         new_waypoints = wps._calculate_odlc_search(flyzone_list, start_point, search_grid_list, off_axis_odlc_pos, altitude_msl=110)

#         for wp in new_waypoints:
#             self.assertEqual(wp['altitude'], 110)

#         self.assertEqual(new_waypoints[0]['latitude'], search_grid_list[0].latitude_m)
#         self.assertEqual(new_waypoints[0]['longitude'], search_grid_list[0].longitude_m)

#         # Since off_axis is outside the flyzone, should be a calculated point NOT the off-axis point
#         self.assertNotEqual(new_waypoints[-1]['latitude'], off_axis_odlc_pos.latitude_m)
#         self.assertNotEqual(new_waypoints[-1]['longitude'], off_axis_odlc_pos.longitude_m)

#     def test_case_off_axis_inside(self):
#         """
#         Test case where:
#         - Search grid is closer
#         - Off_Axis is inside the flyzone
#         """
#         search_grid_list = []
#         search_grid_list.append(wps.Waypoint(latitude=38.0, longitude=-76.0, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.1, longitude=-76.0, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.1, longitude=-76.1, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.0, longitude=-76.1, altitude=60.96, is_generated=False, wp_type="search_grid"))

#         flyzone_list = []
#         flyzone_list.append(OrderedBoundaryPoint(latitude=37.5, longitude=-75.5, order=1))
#         flyzone_list.append(OrderedBoundaryPoint(latitude=38.15, longitude=-75.5, order=2))
#         flyzone_list.append(OrderedBoundaryPoint(latitude=38.15, longitude=-76.15, order=3))
#         flyzone_list.append(OrderedBoundaryPoint(latitude=37.5, longitude=-76.15, order=4))

#         off_axis_odlc_pos =wps.Waypoint(latitude=38.11, longitude=-76.11, altitude=60.96, is_generated=False, wp_type="off_axis")
#         start_point = wps.Waypoint(latitude=37.6, longitude=-75.6, altitude=60.96, is_generated=False, wp_type="auto_flight")

#         new_waypoints = wps._calculate_odlc_search(flyzone_list, start_point, search_grid_list, off_axis_odlc_pos, altitude_msl=110)

#         for wp in new_waypoints:
#             self.assertEqual(wp['altitude'], 110)

#         self.assertEqual(new_waypoints[0]['latitude'], search_grid_list[0].latitude_m)
#         self.assertEqual(new_waypoints[0]['longitude'], search_grid_list[0].longitude_m)

#         # Since off_axis is outside the flyzone, should be a calculated point NOT the off-axis point
#         self.assertEqual(new_waypoints[-1]['latitude'], off_axis_odlc_pos.latitude_m)
#         self.assertEqual(new_waypoints[-1]['longitude'], off_axis_odlc_pos.longitude_m)

#     def test_case_off_axis_closer(self):
#         """
#         Test case where:
#         - Search grid is further away
#         - Off_Axis is inside the flyzone
#         """
#         search_grid_list = []
#         search_grid_list.append(wps.Waypoint(latitude=38.0, longitude=-76.0, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.1, longitude=-76.0, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.1, longitude=-76.1, altitude=60.96, is_generated=False, wp_type="search_grid"))
#         search_grid_list.append(wps.Waypoint(latitude=38.0, longitude=-76.1, altitude=60.96, is_generated=False, wp_type="search_grid"))

#         flyzone_list = []
#         flyzone_list.append(OrderedWayPoint(latitude=37.5, longitude=-75.5, order=1))
#         flyzone_list.append(OrderedWayPoint(latitude=38.15, longitude=-75.5, order=2))
#         flyzone_list.append(OrderedWayPoint(latitude=38.15, longitude=-76.15, order=3))
#         flyzone_list.append(OrderedWayPoint(latitude=37.5, longitude=-76.15, order=4))

#         start_point = wps.Waypoint(latitude=37.6, longitude=-75.6, altitude=60.96, is_generated=False, wp_type="auto_flight")
#         off_axis_odlc_pos = wps.Waypoint(latitude=37.605, longitude=-75.605, altitude=60.96, is_generated=False, wp_type="off_axis")

#         new_waypoints = wps._calculate_odlc_search(flyzone_list, start_point, search_grid_list, off_axis_odlc_pos, altitude_msl=110)

#         for wp in new_waypoints:
#             self.assertEqual(wp['altitude'], 110)

#         # Since the off-axis point is closer, search grid starts at index 1
#         self.assertEqual(new_waypoints[1]['latitude'], search_grid_list[0].latitude_m)
#         self.assertEqual(new_waypoints[1]['longitude'], search_grid_list[0].longitude_m)

#         # Since off_axis is outside the flyzone, should be a calculated point NOT the off-axis point
#         self.assertEqual(new_waypoints[0]['latitude'], off_axis_odlc_pos.latitude_m)
#         self.assertEqual(new_waypoints[0]['longitude'], off_axis_odlc_pos.longitude_m)
