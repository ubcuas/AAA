import os
import tarfile
import json
import requests
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from wsgiref.util import FileWrapper

from interop.models import UasMission

import avoidance.waypoint_system as wps
from avoidance.models import OrderedRouteWayPoint
from avoidance.decorators import timed


@require_http_methods(["GET"])
def route(request, mission_id):
    """
    GET[mission_id]:
        - Returns the route as a JSON object.
        - If no route has been calculated, will create the new route.
    """

    # Map needs an empty default route
    if "0" in mission_id:
        return JsonResponse({"default":"No Waypoints"})
    return _route(request, mission_id)

def _route(request, mission_id):
    mission = UasMission.objects.get(id=mission_id)

    pre_calc_route = OrderedRouteWayPoint.objects.filter(mission=mission.id).order_by('order')

    if not pre_calc_route:
        pre_calc_route = _call_routing(mission)

    output_waypoints = _parse_waypoints_to_dict(pre_calc_route)
    output_obstacles = _parse_obs_to_points_list(mission.get_obstacles_as_list())
    output_flyzone = _parse_fz_to_points_list(mission.flyzone.get_waypoints_as_list(), mission.flyzone.get_vertical_bounds())

    payload = {'waypoints': output_waypoints, 'obstacles': output_obstacles, 'flyzone': output_flyzone}
    return JsonResponse(payload)

@csrf_exempt
@require_http_methods(["POST"])
def upload_to_acom(request, mission_id):
    """
    POST:
        - pulls the requested route from database, format to ACOM specs,
          then posted to ACOM
    """
    if request.method == "POST":
        mission = UasMission.objects.get(id=mission_id)
        route =  OrderedRouteWayPoint.objects.filter(mission=mission).order_by('order')
        waypoints = _serialize_orwp_to_acomjson(route)
        acom_payload = {'wps' : waypoints, 'takeoffAlt': 31,'rtl': False}
        r = requests.post(settings.ACOM_HOSTNAME + '/aircraft/mission', json=acom_payload)

        if not r.ok:
            raise Exception('Failed to POST /api/upload_to_acom: [%s] %s' % (r.status_code, r.content))
        return JsonResponse(r.json())
    return


@csrf_exempt
@require_http_methods(["GET", "POST"])
def reroute(request, mission_id):
    """
    GET:
        - Forces a recalculation of the route and sends it back
    POST:
        - Saves a new route, with (or without) avoidance verification
    """
    if request.method == 'GET':
        mission = UasMission.objects.get(id=mission_id)

        OrderedRouteWayPoint.objects.filter(mission=mission).delete()

        _call_routing(mission)
        return _route(request, mission_id)

    else:  # request.method == 'POST'
        new_waypoints = json.loads(request.body)['waypoints']
        mission = UasMission.objects.get(id=mission_id)

        # Clean and place into DB
        OrderedRouteWayPoint.objects.filter(mission=mission.id).delete()
        order = 0
        for new_wp in new_waypoints:
            order+=1
            db_new_wp = OrderedRouteWayPoint(mission=mission,
                                                    latitude=new_wp['latitude'],
                                                    longitude=new_wp['longitude'],
                                                    altitude_msl=new_wp['altitude'],
                                                    order=order,
                                                    is_generated=new_wp["is_generated"],
                                                    wp_type=new_wp["wp_type"])
            db_new_wp.save()
        return _route(request, mission_id)

@timed
def _call_routing(mission):
    """
    Preps and calls the waypoint system, gets results and puts back into DB.

    WayPoints -> Airdrop -> Shortest_Path( SearchGrid, Off-axis )
    """
    # Gather the required data
    flyzone = mission.flyzone.get_waypoints_as_list()
    flyzone_bounds = mission.flyzone.get_vertical_bounds()

    auto_flight_points = mission.get_waypoints_as_list()

    airdrop_pos = mission.airdrop_pos

    search_grid_points = mission.search_grid.get_waypoints_as_list()
    off_axis_odlc_pos = mission.off_axis_odlc_pos

    obstacles = mission.get_obstacles_as_list()

    # Perform the routing
    new_waypoints = wps.draw_complete_route(flyzone, auto_flight_points, airdrop_pos, search_grid_points, off_axis_odlc_pos)

    # import cProfile
    # pr = cProfile.Profile()
    # new_waypoints = pr.runcall(wps.find_path, new_waypoints, obstacles, flyzone, flyzone_bounds)
    # pr.print_stats('cumtime')
    new_waypoints, mission_map = wps.find_path(new_waypoints, obstacles, flyzone, flyzone_bounds)

    new_waypoints = wps.post_process_path(mission_map, new_waypoints, obstacles, flyzone, flyzone_bounds)


    # Cleanup, write to DB and return calculated route
    OrderedRouteWayPoint.objects.filter(mission=mission.id).delete()
    order = 0
    for new_wp in new_waypoints:
        order+=1
        db_new_wp = OrderedRouteWayPoint(mission=mission,
                                                latitude=new_wp['latitude'],
                                                longitude=new_wp['longitude'],
                                                altitude_msl=new_wp['altitude'],
                                                order=order,
                                                is_generated=new_wp["is_generated"],
                                                delay=new_wp["delay"],
                                                wp_type=new_wp["wp_type"])
        db_new_wp.save()
    return OrderedRouteWayPoint.objects.filter(mission=mission.id).order_by('order')

def _serialize_orwp_to_acomjson(orwp_list):
    """
    Takes in a mission object and returns a list of all the waypoints formatted to acom spec
    """
    acom_wps = []
    for wp in orwp_list:
        acom_wps.append({'hold': 0, 'radius': 1, 'lat': wp.latitude, 'lng': wp.longitude, 'alt' : wp.altitude_msl})
    return acom_wps

def _parse_waypoints_to_dict(orwp_list):
    """
    Takes in a mission object and returns a dict with all the waypoints
    """
    new_waypoints = []
    for db_new_wp in orwp_list:
        new_waypoints.append({'order': db_new_wp.order, 'latitude': db_new_wp.latitude, 'longitude': db_new_wp.longitude, 'altitude': db_new_wp.altitude_msl, 'is_generated': db_new_wp.is_generated, 'wp_type': db_new_wp.wp_type, 'delay': db_new_wp.delay})
    return new_waypoints

def _parse_obs_to_dict(obs_list):
    """
    Takes in a mission object and returns a list with all the obstacles as dicts
    """
    new_obstacles = []
    for obs in obs_list:
        new_obstacles.append({'latitude': obs.latitude, 'longitude': obs.longitude, 'height': obs.cylinder_height, 'cylinder_radius': obs.cylinder_radius})
    return new_obstacles

def _parse_obs_to_points_list(obs_list):
    """
    Takes in a mission object and returns a list with all the obstacles, with the obstacles as a list of points
    """
    import shapely.geometry as geom
    from common.utils.conversions import ll_to_utm, utm_to_ll

    new_obstacles = []
    for obs in obs_list:
        order = 0
        obs_as_list = []
        points = geom.Point(ll_to_utm(obs.longitude, obs.latitude)).buffer(obs.cylinder_radius).exterior.coords
        for point in points:
            order += 1
            conv_long, conv_lat = utm_to_ll(*point)
            obs_as_list.append({'order': order, 'latitude': conv_lat, 'longitude': conv_long, 'altitude': obs.cylinder_height, 'is_generated': False, 'wp_type': "obstacle"})
        new_obstacles.append(obs_as_list)
    return new_obstacles

def _parse_fz_to_points_list(flyzone, bounds):
    """
    Takes in the list of flyzone points and returns a dict representation
    """
    flyzone_dict = {'min': bounds[0], 'max': bounds[1], 'points': []}
    order = 0
    for fz_point in flyzone:
        order += 1
        flyzone_dict['points'].append({'order': order, 'latitude': fz_point.latitude, 'longitude': fz_point.longitude, 'altitude': None, 'is_generated': False, 'wp_type': "flyzone"})
    return flyzone_dict

@require_http_methods(["GET"])
def missions(request):
    """
    GET[]
        - Returns a list of possible missions
    """
    missions = UasMission.objects.filter()
    return JsonResponse({"missions": [mission.id for mission in missions]})

@require_http_methods(["GET"])
def route_file(request, mission_id):
    """
    GET[mission_id]
        - Returns a download to a mission waypoint file
    """
    basepath = "staticfiles/"
    filename = basepath+"mission_%s_waypoints.waypoints" % mission_id

    mission = UasMission.objects.get(id=mission_id)
    pre_calc_route = OrderedRouteWayPoint.objects.filter(mission=mission.id).order_by('order')
    waypoints = _parse_waypoints_to_dict(pre_calc_route)

    # Create and save the file
    wps.save_mission(waypoints, filename)

    wrapper = FileWrapper(open(filename))
    response = HttpResponse(wrapper, content_type='text/plain')
    response['Content-Length'] = os.path.getsize(filename)
    return response

@require_http_methods(["GET"])
def obs_file(request, mission_id):
    """
    GET[mission_id]
        - Returns a download to a zip filled with the shapefile
    """
    basepath = "staticfiles/"
    base_filename = basepath+"mission_%s_obstacles." % mission_id
    zip_filename = '%star.gz' % base_filename
    suffixes = ["shp", "shx", "dbf", "cpg"]

    mission = UasMission.objects.get(id=mission_id)
    obstacles = _parse_obs_to_dict(mission.get_obstacles_as_list())
    # Create and save the files
    wps.save_obstacles(obstacles, base_filename+"shp")

    with tarfile.open(zip_filename, "w:gz") as tar:
        for suffix in suffixes:
            filename = base_filename + suffix
            tar.add(filename)

    wrapper = FileWrapper(open(zip_filename, 'br'))
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Length'] = os.path.getsize(zip_filename)
    return response
