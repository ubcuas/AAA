from django.test import TestCase
from django.urls import reverse
from unittest.mock import MagicMock, patch

from interop import client as gcom_client

from interop.models import Team


class GcomClientGeneralTests(TestCase):

    def test_get_ClientSession(self):
        from interop.models import ClientSession

        test_session = ClientSession(username="test",
                                     password="password",
                                     url="172.0.0.6:80",
                                     session_id="fakesessionid",
                                     expires=None,
                                     active=True)
        test_session.save()

        test_client = gcom_client.Client()
        result = test_client.get_ClientSession()

        self.assertEqual(result.session_id, "fakesessionid")
        self.assertTrue(result.active)


class GcomClientLoginTests(TestCase):
    @patch('interop.client.requests.Session')
    def test_default_login(self, mock_session):
        from interop.models import ClientSession
        test_session_id = "teststringsessionid"
        mock_session.return_value.post.return_value.cookies.get_dict.return_value = {'sessionid': test_session_id}

        url = '172.0.0.1'
        port = '80'
        username = 'testuser'
        password = 'testpass'

        test_client = gcom_client.Client()
        test_client.login(url, port, username, password)

        test_session = ClientSession.objects.get(active=True)
        self.assertEqual(test_session.session_id, test_session_id)

    @patch('interop.client.requests.Session')
    def test_default_login_http_included(self, mock_session):
        from interop.models import ClientSession
        test_session_id = "teststringsessionid"
        mock_session.return_value.post.return_value.cookies.get_dict.return_value = {'sessionid': test_session_id}

        url = 'http://172.0.0.1'
        port = '80'
        username = 'testuser'
        password = 'testpass'

        test_client = gcom_client.Client()
        test_client.login(url, port, username, password)

        test_session = ClientSession.objects.get(active=True)
        self.assertEqual(test_session.session_id, test_session_id)


class GcomClientGetMissionsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.patcher = patch('interop.client.Client.get_ClientSession')
        cls.mock_ClientSession = cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    @patch('interop.client.requests.get')
    @patch('interop.client.requests')
    def test_default_get_mission(self, mock_requests, mock_result):

        mock_result.return_value.json.return_value = {'test_mission': "TheCakeWasALie"}

        test_client = gcom_client.Client()
        result = test_client.get_mission()

        self.assertTrue('test_mission' in result)
        self.assertEqual(result['test_mission'], "TheCakeWasALie")


class GcomClientGetObstaclesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patcher = patch('interop.client.Client.get_ClientSession')
        cls.mock_ClientSession = cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    @patch('interop.client.requests.get')
    @patch('interop.client.requests')
    def test_default_get_obstacles(self, mock_requests, mock_result):
        mock_result.return_value.json.return_value = {'stationary_obstacles': {'test_obstacles': "TheCakeWasALie"}}

        test_client = gcom_client.Client()
        result = test_client.get_obstacles()

        self.assertTrue('test_obstacles' in result)
        self.assertEqual(result['test_obstacles'], "TheCakeWasALie")


class GcomClientODLCTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patcher = patch('interop.client.Client.get_ClientSession')
        cls.mock_ClientSession = cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    @patch('interop.client.requests.get')
    @patch('interop.client.requests')
    def test_default_get_odlcs(self, mock_requests, mock_result):
        mock_result.return_value.json.return_value = {'test_odlc': "TheCakeWasALie"}

        test_client = gcom_client.Client()
        result = test_client.get_odlcs()

        self.assertTrue('test_odlc' in result)
        self.assertEqual(result['test_odlc'], "TheCakeWasALie")

    @patch('interop.client.requests.post')
    @patch('interop.client.requests')
    def test_default_post_odlc(self, mock_requests, mock_result):
        mock_result.return_value.json.return_value = {'test_odlc': "TheCakeWasALie"}

        test_client = gcom_client.Client()
        result = test_client.post_odlc({'test_odlc': "TheCakeWasALie"})

        self.assertTrue('test_odlc' in result)
        self.assertEqual(result['test_odlc'], "TheCakeWasALie")

    @patch('interop.client.requests.put')
    @patch('interop.client.requests')
    def test_default_put_odlc(self, mock_requests, mock_result):
        mock_result.return_value.json.return_value = {'test_odlc': "TheCakeWasALie"}

        test_client = gcom_client.Client()
        result = test_client.put_odlc({'id': 1, 'test_odlc': "TheCakeWasALie"})

        self.assertTrue('test_odlc' in result)
        self.assertEqual(result['test_odlc'], "TheCakeWasALie")
