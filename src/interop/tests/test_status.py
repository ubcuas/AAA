from django.test import TestCase, Client
from datetime import datetime, timezone

from unittest import skip, mock

from interop.models import Team


class Test_Status_Route(TestCase):
    fixtures = ['telem.json']

    @mock.patch('interop.views.datetime')
    def test_uas_status_connected1(self, mock_datetime):
        """
           last uas telemetry within 5 seconds
        """
        mock_datetime.utcnow = mock.Mock(
            return_value=datetime(2021, 3, 13, 21, 58, 29, 2, tzinfo=timezone.utc))

        c = Client()
        url = "/api/interop/telemstatus"
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, response.json()["status"])

    @mock.patch('interop.views.datetime')
    def test_uas_status_connected2(self, mock_datetime):
        """
           last uas telemetry within 5 seconds
        """
        mock_datetime.utcnow = mock.Mock(
            return_value=datetime(2021, 3, 13, 21, 58, 33, 0, tzinfo=timezone.utc))

        c = Client()
        url = "/api/interop/telemstatus"
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, response.json()["status"])

    @mock.patch('interop.views.datetime')
    def test_uas_status_disconnected(self, mock_datetime):
        """
           last uas telemetry more than 5 seconds ago
        """
        mock_datetime.utcnow = mock.Mock(
            return_value=datetime(2021, 3, 14, 21, 59, 33, 0, tzinfo=timezone.utc))

        c = Client()
        url = "/api/interop/telemstatus"
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, response.json()["status"])


class Test_Team_Status_Route(TestCase):
    fixtures = ['telem.json']

    @mock.patch('interop.views.datetime')
    def test_team_status_connected1(self, mock_datetime):
        """
           last team telemetry within 5 seconds
        """
        mock_datetime.utcnow = mock.Mock(
            return_value=datetime(2021, 3, 20, 17, 34, 54, 718347, tzinfo=timezone.utc))

        c = Client()
        url = "/api/interop/teamtelemstatus"
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, response.json()["status"])

    @mock.patch('interop.views.datetime')
    def test_team_status_connected2(self, mock_datetime):
        """
           last team telemetry within 5 seconds
        """
        mock_datetime.utcnow = mock.Mock(return_value=datetime(2021, 3, 20, 17, 34, 57, 0, tzinfo=timezone.utc))

        c = Client()
        url = "/api/interop/teamtelemstatus"
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, response.json()["status"])

    @mock.patch('interop.views.datetime')
    def test_team_status_disconnected(self, mock_datetime):
        """
           last team telemetry more than 5 seconds ago
        """
        mock_datetime.utcnow = mock.Mock(return_value=datetime(2021, 3, 20, 17, 35, 33, 0, tzinfo=timezone.utc))

        c = Client()
        url = "/api/interop/teamtelemstatus"
        response = c.get(url)
        self.assertEqual(200, response.status_code)

        self.assertEqual(0, response.json()["status"])
