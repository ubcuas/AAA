import requests
import logging

from interop.models import ClientSession

logger = logging.getLogger(__name__)


class Client():
    """
    Client class that connects to auvsi interop-server.
    See: https://github.com/auvsi-suas/interop
    """

    def get_ClientSession(self):
        """
        Gets the latest active client session
        """
        gcom_session = ClientSession.objects.get(active=True)
        return gcom_session

    def get_cookies(self, gcom_session):
        cookies = {
            "sessionid": gcom_session.session_id,
        }
        logger.debug("Using %s sessionid", gcom_session.session_id)
        return cookies

    def login(self, url, port, username, password):
        """
        POST /api/login
        """
        logger.debug("POST interop-server /api/login")
        if "http://" not in url:
            url = "http://" + url
        url = url + ":" + port

        request_url = url + "/api/login"
        request_payload = {
            "username": username,
            "password": password
        }

        session = requests.Session()
        r = session.post(request_url, json=request_payload)

        if not r.ok:
            raise Exception('Failed to Login: [%s] %s' % (r.status_code, r.content))

        # Create a new local session object
        cookies = r.cookies.get_dict()
        gcom_session = ClientSession(username=username,
                                     password=password,
                                     url=url,
                                     session_id=cookies['sessionid'],
                                     expires=None,
                                     active=True)

        # Deactivate previous sessions
        prev_sessions = ClientSession.objects.filter()
        for psess in prev_sessions:
            psess.active = False
            psess.save()

        # Save new session
        gcom_session.save()

    def get_mission(self, mission_id=1):
        """
        GET /api/missions
        """
        logger.debug("GET interop-server /api/missions")
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + f"/api/missions/{mission_id}"

        r = requests.get(request_url, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to GET /api/missions: [%s] %s' % (r.status_code, r.content))

        return r.json()

    def get_obstacles(self):
        """
        GET /api/obstacles
        """
        logger.debug("GET interop-server /api/obstacles")
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/obstacles"

        r = requests.get(request_url, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to GET /api/obstacles: [%s] %s' % (r.status_code, r.content))

        return r.json()['stationary_obstacles']

    def get_odlcs(self):
        """
        GET /api/odlcs
        """
        logger.debug("GET interop-server /api/odlcs")
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/odlcs"

        r = requests.get(request_url, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to GET /api/odlcs: [%s] %s' % (r.status_code, r.content))

        return r.json()

    def post_odlc(self, odlc_json):
        """
        POST /api/odlcs
        """
        logger.debug("POST interop-server /api/odlcs")
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/odlcs"

        r = requests.post(request_url, json=odlc_json, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to POST /api/odlcs: [%s] %s' % (r.status_code, r.content))

        return r.json()

    def put_odlc(self, odlc_json):
        """
        PUT /api/odlcs/<id>
        """
        logger.debug("PUT interop-server /api/odlcs/%s" % odlc_json['id'])
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/odlcs/%s" % odlc_json['id']

        r = requests.put(request_url, json=odlc_json, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to PUT /api/odlcs: [%s] %s' % (r.status_code, r.content))

        return r.json()

    def delete_odlc(self, odlc_id):
        """
        DELETE /api/odlcs/<id>
        """
        logger.debug("DELETE interop-server /api/odlcs/%s" % odlc_id)
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/odlcs/%s" % odlc_id

        r = requests.delete(request_url, cookies=cookies)

        if r.status_code == 404:
            logger.warning('Failed to DELETE /api/odlcs/%s: [%s] %s', odlc_id, r.status_code, r.content)
        elif not r.ok:
            raise Exception('Failed to DELETE /api/odlcs/%s: [%s] %s' % (odlc_id, r.status_code, r.content))

        return r.content

    def post_odlc_image(self, odlc_json, thumbnail_filename):
        """
        POST /api/odlcs/<id>/image
        """
        logger.debug("POST interop-server /api/odlcs/%s/image" % odlc_json['id'])
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)
        headers = {'Content-Type': 'image/jpeg'}

        request_url = session.url + "/api/odlcs/%s/image" % odlc_json['id']
        img_data = open(thumbnail_filename, 'rb').read()

        r = requests.post(request_url, data=img_data, cookies=cookies, headers=headers)

        if not r.ok:
            raise Exception('Failed to POST /api/odlcs/%s/image: [%s] %s' % (odlc_json['id'], r.status_code, r.content))

        return r.content

    def post_telemetry(self, telem_data):
        """
        POST /api/telemetry
        """
        logger.debug("POST interop-server /api/telemetry")
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/telemetry"

        r = requests.post(request_url, json=telem_data, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to POST /api/telemetry: [%s] %s' % (r.status_code, r.content))

        return r.content

    def get_teams_telemetry(self):
        """
        GET /api/teams
        """
        logger.debug("GET interop-server /api/teams")
        session = self.get_ClientSession()
        cookies = self.get_cookies(session)

        request_url = session.url + "/api/teams"

        r = requests.get(request_url, cookies=cookies)

        if not r.ok:
            raise Exception('Failed to GET /api/teams: [%s] %s' % (r.status_code, r.content))

        return r.json()
