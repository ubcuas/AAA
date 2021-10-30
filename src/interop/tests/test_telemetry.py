from pylibuuas.telem import TelemetryArgs, new_telem_msg
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from interop.models import Team
from interop.models import UasTelemetry
import logging

logger = logging.getLogger(__name__)

UAS_team_id = 1


class InteropUploadTelemetryCase(TestCase):
    # Necessary fixtures for these tests to work.
    fixtures = ['telem.json', ]

    def test_send_telemetry(self):
        from interop.models import UasTelemetry
        from interop.models import GpsPosition
        from interop import views

        mock_Client = MagicMock()

        test_gps = GpsPosition.objects.create(latitude=24.0,
                                              longitude=23.0)

        test_telem = UasTelemetry(team=Team.objects.get(team_id=UAS_team_id),
                                  gps=test_gps,
                                  altitude_msl=100,
                                  uas_heading=123)
        test_telem.save()
        self.assertFalse(test_telem.uploaded)

        result = views.send_telemetry(mock_Client)
        self.assertTrue(result)

        test_telem = UasTelemetry.objects.get(id=test_telem.id)
        self.assertTrue(test_telem.uploaded)

        mock_Client.post_telemetry.assert_called()


class InteropDownloadTelemetryCase(TestCase):
    """
    After completing the above test, this test verifies that we can successfully
    download telemetry from the AUVSI interop server, and store it in our database in a usable format.
    """
    # Necessary fixtures for these tests to work; contains data. Particularly a fixture containing our team's data.
    fixtures = ['telem.json']

    def setUp(self):
        from interop.models import ClientSession
        # Initialize a client session for testing purposes
        test_session = ClientSession(url="http://172.0.0.12:80",
                                     session_id="teststringwooohooo",
                                     active=True)
        test_session.save()

    # After testing sending telemetry, attempt to get other teams' telemetry
    @patch('interop.views.Client')
    def test_post_success_and_get_telemetry(self, mock_client):
        c = Client()
        post_payload = new_telem_msg(TelemetryArgs(
            latitude_dege7=1,
            longitude_dege7=2,
            altitude_agl_m=3.0,
            altitude_msl_m=4.0,
            heading_deg=5.0,
            velocityx_m_s=6.0,
            velocityy_m_s=7.0,
            velocityz_m_s=8.0,
            roll_rad=9.0,
            pitch_rad=10.0,
            yaw_rad=11.0,
            rollspeed_rad_s=12.0,
            pitchspeed_rad_s=13.0,
            yawspeed_rad_s=14.0,
            timestamp_pixhawk_ms=15,
            timestamp_msg_ms=16,
        ))

        # Mock telemetry return value for Team University
        mock_client.return_value.get_teams_telemetry.return_value = [{
            "team": {
                "id": 2,
                "username": "testuser",
                "name": "Team Name",
                "university": "Team University"
            },
            "inAir": False,
            "telemetry": {
                "latitude": -87.0,
                "longitude": 14.0,
                "altitude": 20.0,
                "heading": 5.0
            },
            "telemetryId": "1278",
            "telemetryAgeSec": 1.064382,
            "telemetryTimestamp": "2019-10-05T20:42:23.643989+00:00",
        }]

        # Post our telemetry
        response = c.post(reverse('interop.telemetry'),
                          post_payload,
                          content_type="application/json")

        # Check to see if the team data was added to the database
        self.assertTrue(Team.objects.filter(university="Team University").exists())

        # Check to see if telemetry entry was added to the database
        self.assertTrue(UasTelemetry.objects.filter(team=Team.objects.get(university="Team University"))
                        .exists())

        logger.info("GPS telemetry entry #1: {}"
                    .format(UasTelemetry.objects.filter(team=Team.objects.get(university="Team University"))
                            .latest('created_at').marshal()))

        logger.info("Telemetry entry #1 timestamp: {}"
                    .format(UasTelemetry.objects.filter(team=Team.objects.get(university="Team University"))
                            .latest('created_at').timestamp))

        # Mock telemetry return value for Team University, again
        mock_client.return_value.get_teams_telemetry.return_value = [{
            "team": {
                "id": 2,
                "username": "testuser",
                "name": "Team Name",
                "university": "Team University"
            },
            "inAir": False,
            "telemetry": {
                "latitude": -82.0,
                "longitude": 10.0,
                "altitude": 40.0,
                "heading": 6.0
            },
            "telemetryId": "1281",
            "telemetryAgeSec": 1.064382,
            "telemetryTimestamp": "2019-10-05T20:44:23.643989+00:00",
        }]

        # Post our telemetry, again (note that when we post our telemetry, we fetch telemetry from AUVSI interop)
        response = c.post(reverse('interop.telemetry'),
                          post_payload,
                          content_type="application/json")

        # Check to see if both telemetry entries were added to the database
        self.assertTrue(UasTelemetry.objects.filter(team=Team.objects.get(university="Team University"))
                        .count() == 2)

        logger.info("Telemetry entry #2: {}"
                    .format(UasTelemetry.objects.filter(team=Team.objects.get(university="Team University"))
                            .latest('created_at').marshal()))

        logger.info("Telemetry entry #2 timestamp: {}"
                    .format(UasTelemetry.objects.filter(team=Team.objects.get(university="Team University"))
                            .latest('created_at').timestamp))

        # Verify that the team only has one instance, not creating duplicates
        self.assertTrue(Team.objects.filter(university="Team University").count() == 1)

        logger.info("Single instance of team data found in database: {}"
                    .format(str(Team.objects.get(university="Team University"))))

        mock_client.assert_called()
