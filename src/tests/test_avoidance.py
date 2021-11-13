from django.test import TestCase, Client
from django.urls import reverse

from unittest.mock import patch
from unittest import skip

@skip("Skipping until a better way is found")
class TestAvoidance_Views_route(TestCase):
    """
    /avoidance/api/route/<mission_id>/$
    """
    fixtures = ['default_mission.json']

    @patch('views.wps.post_process_path')
    @patch('views.wps.find_path')
    @patch('views.wps.draw_complete_route')
    def test_route(self, mock_draw_complete_route, mock_find_path, mock_post_process_path):
        mock_find_path.return_value = (None, None)
        mock_post_process_path.return_value = [{'order': 1, 'latitude': 38.142544, 'longitude': -76.434088, 'altitude': 60.96, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 2, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 91.44, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 3, 'latitude': 38.144678, 'longitude': -76.427995, 'altitude': 30.48, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 4, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 35.0, 'is_generated': False, 'wp_type': "airdrop", 'delay': 0},
                                       {'order': 5, 'latitude': 38.14455483521934, 'longitude': -76.42834666026644, 'altitude': 35.0, 'is_generated': True, 'wp_type': "search_grid", 'delay': 0}]

        c = Client()
        mission_id = 1
        url = "/avoidance/api/route/%s/" % mission_id

        response = c.get(url)
        self.assertEqual(200, response.status_code)

        expected = {'waypoints': [
                        {'order': 1, 'latitude': 38.142544, 'longitude': -76.434088, 'altitude': 60.96, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                        {'order': 2, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 91.44, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                        {'order': 3, 'latitude': 38.144678, 'longitude': -76.427995, 'altitude': 30.48, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                        {'order': 4, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 35.0, 'is_generated': False, 'wp_type': "airdrop", 'delay': 0},
                        {'order': 5, 'latitude': 38.14455483521934, 'longitude': -76.42834666026644, 'altitude': 35.0, 'is_generated': True, 'wp_type': "search_grid", 'delay': 0}
                    ]}
        self.assertEqual(expected['waypoints'], response.json()['waypoints'])

        for key in ['waypoints', 'obstacles', 'flyzone']:
            self.assertTrue(key in response.json())

@skip("Skipping until a better way is found")
class TestAvoidance_Views_reroute(TestCase):
    """
    /avoidance/api/reroute/<mission_id>/$
    """
    fixtures = ['default_mission.json', 'pre_ordered.json']

    @patch('views.wps.post_process_path')
    @patch('views.wps.find_path')
    @patch('views.wps.draw_complete_route')
    def test_get_reroute(self, mock_draw_complete_route, mock_find_path, mock_post_process_path):
        mock_find_path.return_value = (None, None)
        mock_post_process_path.return_value = [{'order': 1, 'latitude': 38.142544, 'longitude': -76.434088, 'altitude': 60.96, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 2, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 91.44, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 3, 'latitude': 38.144678, 'longitude': -76.427995, 'altitude': 30.48, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 4, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 35.0, 'is_generated': False, 'wp_type': "airdrop", 'delay': 0},
                                       {'order': 5, 'latitude': 38.14455483521934, 'longitude': -76.42834666026644, 'altitude': 35.0, 'is_generated': True, 'wp_type': "search_grid", 'delay': 0}]

        c = Client()
        mission_id = 1
        url = "/avoidance/api/reroute/%s/" % mission_id

        response = c.get(url)
        self.assertEqual(200, response.status_code)

        expected = {'waypoints': [
                        {'order': 1, 'latitude': 38.142544, 'longitude': -76.434088, 'altitude': 60.96, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                        {'order': 2, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 91.44, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                        {'order': 3, 'latitude': 38.144678, 'longitude': -76.427995, 'altitude': 30.48, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                        {'order': 4, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 35.0, 'is_generated': False, 'wp_type': "airdrop", 'delay': 0},
                        {'order': 5, 'latitude': 38.14455483521934, 'longitude': -76.42834666026644, 'altitude': 35.0, 'is_generated': True, 'wp_type': "search_grid", 'delay': 0}
                    ]}
        self.assertEqual(expected['waypoints'], response.json()['waypoints'])

        for key in ['waypoints', 'obstacles', 'flyzone']:
            self.assertTrue(key in response.json())

    def test_post_reroute(self):
        c = Client()
        mission_id = 1
        url = "/avoidance/api/reroute/%s/" % mission_id

        data = {'waypoints': [
                    {'order': 1, 'latitude': 12.0, 'longitude': -76.999, 'altitude': 200.0, 'is_generated': True, 'wp_type': "auto_flight", 'delay': 0},
                    {'order': 2, 'latitude': 24.0, 'longitude': -76.365, 'altitude': 300.0, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                    {'order': 3, 'latitude': 36.0, 'longitude': -76.427, 'altitude': 100.0, 'is_generated': True, 'wp_type': "auto_flight", 'delay': 0}
                ]}

        response = c.post(url, data, content_type="application/json")
        self.assertEqual(200, response.status_code)

        self.assertEqual(data['waypoints'], response.json()['waypoints'])

@skip("Skipping until a better way is found")
class TestAvoidance_Views_missions(TestCase):
    """
    /avoidance/api/missions/$
    """
    fixtures = ['default_mission.json']

    def test_missions(self):
        c = Client()
        url = "/avoidance/api/missions/"

        response = c.get(url)
        self.assertEqual(200, response.status_code)

        expected = {'missions': [1]}
        self.assertEqual(expected, response.json())

@skip("Skipping until a better way is found")
class TestAvoidance_Views_files(TestCase):
    """
    /avoidance/file/route/<mission_id>/$
    /avoidance/file/obs/<mission_id>/$
    """
    fixtures = ['default_mission.json']

    @patch('views.wps.post_process_path')
    @patch('views.wps.find_path')
    @patch('views.wps.draw_complete_route')
    def test_route_file(self, mock_draw_complete_route, mock_find_path, mock_post_process_path):
        mock_find_path.return_value = (None, None)
        mock_post_process_path.return_value = [{'order': 1, 'latitude': 38.142544, 'longitude': -76.434088, 'altitude': 60.96, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 2, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 91.44, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 3, 'latitude': 38.144678, 'longitude': -76.427995, 'altitude': 30.48, 'is_generated': False, 'wp_type': "auto_flight", 'delay': 0},
                                       {'order': 4, 'latitude': 38.141833, 'longitude': -76.425263, 'altitude': 35.0, 'is_generated': False, 'wp_type': "airdrop", 'delay': 0},
                                       {'order': 5, 'latitude': 38.14455483521934, 'longitude': -76.42834666026644, 'altitude': 35.0, 'is_generated': True, 'wp_type': "search_grid", 'delay': 0}]

        c = Client()
        route_url = "/avoidance/api/route/1/"
        url = "/avoidance/file/route/1/"

        # Ensure that the route exists to get
        response = c.get(route_url)

        response = c.get(url)
        self.assertEqual(200, response.status_code)

        expected = b'QGC WPL 110\n0   0   3   16  0.00000000  0.00000000  0.00000000  0.00000000  38.142544 -76.434088    60.96   1\n1   0   3   16  0.00000000  0.00000000  0.00000000  0.00000000  38.141833 -76.425263    91.44   1\n2   0   3   16  0.00000000  0.00000000  0.00000000  0.00000000  38.144678 -76.427995    30.48   1\n3   0   3   17  0.00000000  0.00000000  0.00000000  0.00000000  38.141833 -76.425263    35.0   1\n4   0   3   16  0.00000000  0.00000000  0.00000000  0.00000000  38.14455483521934 -76.42834666026644    35.0   1\n'
        self.assertEqual(expected, response.content)

    def test_obs_file(self):
        c = Client()
        url = "/avoidance/file/obs/1/"

        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertTrue(b"mission_1_obstacles" in response.content)
