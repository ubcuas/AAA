from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from interop.models import UasTelemetry

import time

def mock_get_mission():
    test_mission = {
          "id": 1,
          "flyZones": [
            {
              "altitudeMax": 750.0,
              "altitudeMin": 0.0,
              "boundaryPoints": [
                {
                  "latitude": 38.142544,
                  "longitude": -76.434088
                },
                {
                  "latitude": 38.141833,
                  "longitude": -76.425263
                },
                {
                  "latitude": 38.144678,
                  "longitude": -76.427995
                }
              ]
            }
          ],
          "searchGridPoints": [
            {
              "latitude": 38.142544,
              "longitude": -76.434088
            }
          ],
          "offAxisOdlcPos": {
            "latitude": 38.142544,
            "longitude": -76.434088
          },
          "waypoints": [
            {
              "latitude": 38.142544,
              "altitude": 200.0,
              "longitude": -76.434088
            }
          ],
          "airDropPos": {
            "latitude": 38.141833,
            "longitude": -76.425263
          },
          "emergentLastKnownPos": {
            "latitude": 38.145823,
            "longitude": -76.422396
          },
          "stationaryObstacles": [
            {
              "latitude": 38.14792,
              "radius": 150.0,
              "longitude": -76.427995,
              "height": 200.0
            },
            {
              "latitude": 38.145823,
              "radius": 50.0,
              "longitude": -76.422396,
              "height": 300.0
            }
          ]
        }
    return test_mission

class InteropMissionCase(TestCase):
    def setUp(self):
        from interop.models import ClientSession
        test_session = ClientSession(url="http://172.0.0.12:80",
                                    session_id="teststringwooohooo",
                                    active=True)
        test_session.save()

    def test_get_status(self):
        c = Client()
        response = c.get(reverse('interop.status'))

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json()['status'])

    @patch('interop.views.Client')
    def test_post_login(self, mock_Client):
        # Mock the data that is returned from the client
        mock_Client.return_value.get_mission.return_value = mock_get_mission()

        c = Client()
        post_data = {'password': "testpass", 'portNum': "8000", 'url': "127.0.0.1", 'username': "testuser"}
        response = c.post(reverse('interop.login'),
                        post_data,
                        content_type="application/json")

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json()['status'])

        mock_Client.assert_called()

    @patch('interop.views.Client')
    def test_post_mission(self, mock_Client):
        # Mock the data that is returned from the client
        mock_Client.return_value.get_mission.return_value = mock_get_mission()

        c = Client()
        post_data = {"mission_id" : 1}
        response = c.post(reverse('interop.mission'),
                        post_data,
                        content_type="application/json")

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json()['status'])

        mock_Client.assert_called()
