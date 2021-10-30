'''
from django.test import Client, TestCase
from unittest.mock import patch

from imp_module.models import ImpODLC
from interop import odlc

class InteropODLCCase(TestCase):
    @patch('interop.odlc.Client')
    def test_odlc_save_signal(self, mock_gcom_client):
        mock_gcom_client.return_value.post_odlc.return_value = {'id': 12,}

        odlc = ImpODLC()
        odlc.save()

        # Use this as a proxy for interop.odlc.post_or_put_odlc()
        # If you can find out where THE FUCK to mock the signal handler (the method above)
        #    contact Eric Mikulin cause he will buy you a beer
        mock_gcom_client.return_value.post_odlc.assert_called()

    @patch('interop.odlc.Client')
    def test_post_odlc(self, mock_gcom_client):
        test_odlc_data = {"auvsi_id": None,
                        "name": "object",
                        "description": "description",
                        "latitude": "49.1",
                        "longitude": "-123.1",
                        "type": "standard",
                        "shape": "rectangle",
                        "background_color": "green",
                        "alphanumeric": "A",
                        "alphanumeric_color": "red",
                        "orientation": "N",
                        "orientationAbs": 0,
                        "image_source": "image.jpg",
                        "x": "0.1",
                        "y": "0.2",
                        "w": "0.3",
                        "h": "0.4"}

        fake_odlc_data = test_odlc_data
        test_odlc_data['id'] = 14

        mock_gcom_client.return_value.post_odlc.return_value = test_odlc_data

        n_odlc = ImpODLC.create(test_odlc_data)
        fake_kwags = {'instance': n_odlc}

        odlc.post_or_put_odlc(None, **fake_kwags)

        self.assertEqual(n_odlc.auvsi_id, 14)
'''