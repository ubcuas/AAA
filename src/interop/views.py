import json
import logging

from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from interop.models import UasMission, UasTelemetry, Team, GpsPosition

from interop.client import Client

from pylibuuas.telem import deserialize_telem_msg

from src.utils.conversions import feet_to_meter

logger = logging.getLogger(__name__)

"""
Uas_client connection status
0 - Disconnected
1 - Connected
2 - Connected Sending data
3 - Connected Sending data Failed
"""

connect_stat = 0
current_mission_id = -1

UAS_team_id = 1


def get_connect_stat():
    global connect_stat
    return connect_stat


def send_telemetry(uas_client):
    connected = get_connect_stat()
    if connected > 0:
        if UasTelemetry.objects.count() != 0:

            uas_telemetry = UasTelemetry.objects.filter(team=Team.objects.get(team_id=UAS_team_id)).latest('created_at')
            if not uas_telemetry.uploaded:
                try:
                    uas_client.post_telemetry(uas_telemetry.marshal())
                    global connect_stat
                    connect_stat = 2
                    uas_telemetry.uploaded = True
                    uas_telemetry.save()
                    logger.debug('Posted telemetry data')
                    return True
                except Exception as error:
                    connect_stat = 3
                    logger.exception('Unable to send telemetry data error: %s' % error)
            else:
                logger.debug("No new telemetry.")
    else:
        logger.debug('The UBC UAS interop server is not connected, or smurf is not connected.')
    return False


@csrf_exempt
@require_http_methods(["GET", "POST"])
def telemetry(request):
    if request.method == 'GET':
        uas_telem = UasTelemetry.objects.filter(team=Team.objects.get(team_id=UAS_team_id)).latest('created_at')
        if uas_telem:
            return JsonResponse(uas_telem[0].marshal())
        else:
            return HttpResponse(status=204)  # No content

    if request.method == 'POST':
        telem = deserialize_telem_msg(request.body)

        gps_data = GpsPosition(latitude=telem.latitude_dege7 / 1.0E7, longitude=telem.longitude_dege7 / 1.0E7)

        uas_team = Team.objects.get(team_id=UAS_team_id)

        new_telem = UasTelemetry(team=uas_team,
                                 gps=gps_data,
                                 altitude_msl=telem.altitude_msl_m,
                                 uas_heading=telem.heading_deg)

        gps_data.save()
        new_telem.save()
        gcom_client = Client()
        send_telemetry(gcom_client)

        # Issue #38: now that we've received a POST to our telemetry endpoint, we should update our database with
        # telemetry from other teams.
        teams_telemetry = gcom_client.get_teams_telemetry()

        for team_telemetry in teams_telemetry:
            # verify the team doesn't contain our own ID, since we log our own telemetry through a different mechanism
            if team_telemetry['team']['id'] != UAS_team_id:
                # check if we've stored this team's information before. if not, create a new team entry
                if not Team.objects.filter(team_id=team_telemetry['team']['id']).exists():
                    new_team = Team(
                        team_id=team_telemetry['team']['id'],
                        username=team_telemetry['team']['username'],
                        name=team_telemetry['team']['name'],
                        university=team_telemetry['team']['university']
                    )
                    new_team.save()

                gps_data = GpsPosition(
                                       latitude=team_telemetry['telemetry']['latitude'],
                                       longitude=team_telemetry['telemetry']['longitude']
                                      )
                team_telem = UasTelemetry(team=Team.objects.get(team_id=team_telemetry['team']['id']),
                                          gps=gps_data,
                                          altitude_msl=feet_to_meter(team_telemetry['telemetry']['altitude']),
                                          uas_heading=team_telemetry['telemetry']['heading'],
                                          uploaded=True,  # all foreign team  telemetry is "uploaded" by default
                                          timestamp=datetime.strptime(team_telemetry['telemetryTimestamp'],
                                                                               "%Y-%m-%dT%H:%M:%S.%f%z")
                                          )
                gps_data.save()
                team_telem.save()

        return HttpResponse(status=200)

    return HttpResponse(status=400)  # Bad request


@csrf_exempt
@require_http_methods(["GET"])
def teams(request):
    body_unicode = request.body.decode('utf-8')
    teams_telemetry = json.loads(body_unicode)

    try:
        gcomclient = Client()

        teams_telemetry = gcomclient.get_teams_telemetry()
        clientsession = gcomclient.get_clientSession()

        logger.debug(teams)

    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError(e)

    response_payload = []

    for team_telemetry in teams_telemetry:
        if team_telemetry['team']['username'] != clientsession.username:
            # check if we've stored this team's information before. if not, create a new team entry
            if not Team.objects.filter(team_id=team_telemetry['team']['id']).exists():
                new_team = Team(
                    team_id=team_telemetry['team']['id'],
                    username=team_telemetry['team']['username'],
                    name=team_telemetry['team']['name'],
                    university=team_telemetry['team']['university']
                )
                new_team.save()

            team_telem = UasTelemetry(team=Team.objects.get(team_id=team_telemetry['team']['id']),
                                      gps=GpsPosition(
                                          latitude=team_telemetry['telemetry']['latitude'],
                                          longitude=team_telemetry['telemetry']['longitude']
                                      ),
                                      altitude_msl=feet_to_meter(team_telemetry['telemetry']['altitude']),
                                      uas_heading=team_telemetry['telemetry']['heading'],
                                      uploaded=True,
                                      timestamp=datetime.strptime(team_telemetry['telemetryTimestamp'],
                                                                           "%Y-%m-%dT%H:%M:%S.%f%z")
                                      )
            team_telem.save()
            response_payload.append(team_telem.marshall())

    return JsonResponse(response_payload)


# -1 error, 0 stopped, 1 sending
@csrf_exempt
@require_http_methods(["GET"])
def telem_status(request):
    # the connection errors out so we show error here
    if connect_stat == 3:
        response = {
            'status': -1,
            'mission_id': current_mission_id,
        }
        return JsonResponse(response)
    # no error
    else:
        last_uas_telem = UasTelemetry.objects.filter(team=Team.objects.get(team_id=UAS_team_id)).latest('created_at')
        if last_uas_telem:
            stat = 1
            # Set timezone to UTC, strip timezone info to get difference
            delta = datetime.utcnow().replace(tzinfo=None) - last_uas_telem.created_at.replace(tzinfo=None)
            if delta.seconds <= 5:
                stat = 1
            else:
                stat = 0
        else:
            stat = -1
        response = {
            'status': stat,
            'mission_id': current_mission_id,
        }
        return JsonResponse(response)


@csrf_exempt
@require_http_methods(["GET"])
def team_telem_status(request):
    # fetch the most recent telemetry from other teams
    last_team_telem = UasTelemetry.objects.exclude(team=Team.objects.get(team_id=UAS_team_id)).latest('created_at')
    if last_team_telem:
        # Calculate time since last team telem by first getting it in UTC, and then stripping the datetime info
        delta = datetime.utcnow().replace(tzinfo=None) - last_team_telem.created_at.replace(tzinfo=None)
        if delta.seconds <= 5:
            stat = 1
        else:
            stat = 0
    else:
        stat = -1
    response = {
        'status': stat,
        'mission_id': current_mission_id,
    }
    return JsonResponse(response)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    global connect_stat
    global current_mission_id

    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    username = body['username']
    password = body['password']

    logger.info('Login: username - %s, password - %s', username, password)
    logger.info('Login: url - %s, port - %s', body['url'], body['portNum'])

    try:
        gcomclient = Client()
        gcomclient.login(body['url'], body['portNum'], username, password)

    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError(e)

    connect_stat = 1
    response = {
        'status': connect_stat,
        'mission_id': current_mission_id,
    }
    return JsonResponse(response)


@csrf_exempt
@require_http_methods(["GET"])
def status(request):
    global connect_stat
    global current_mission_id

    response = {
        'status': connect_stat,
        'mission_id': current_mission_id,
    }

    return JsonResponse(response)


@csrf_exempt
@require_http_methods(["POST"])
def mission(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    current_mission_id = int(body['mission_id'])

    try:
        gcomclient = Client()

        mission = gcomclient.get_mission(mission_id=current_mission_id)
        logger.debug(mission)
        UasMission.create(mission)

    except Exception as e:
        logger.exception(e)
        return HttpResponseServerError(e)

    response = {
        'status': connect_stat,
        'mission_id': current_mission_id,
    }

    return JsonResponse(response)
