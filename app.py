from dis import dis
import json
from flask import Flask
from flask import request
from flask import jsonify
from flask import json
from cmath import sqrt
from utm import to_latlon, from_latlon

app = Flask(__name__)

# Obstacle caching (for averaging drone position to get speed)
obstacles = []

@app.route('/aaa', methods=['GET','POST']) # Only supports posting - keeping GET for testing
def responseHandler():
    if request.method == 'GET': # 'POST' for final
        # Get the interop data; assuming data is in json, no modifications done?
        # interop = #do stuff to parse back into objects 
        #interops[request.interop.id] = request.interop

        obs_list = create_obstacle_list(request.data)

        # Add latest obstacle list to caching obstacle list
        obstacles.append(obs_list)

        # Remove the first cached entry if the size is greater than 5
        if len(obstacles) > 5:
            obstacles.pop(0)

        # Check if need to reroute
        reroute, gcom_obs = need_reroute(obstacles)

        # Flask 1.1.0 a view can directly return a Python dict and Flask will call jsonify automatically
        if reroute:
            return {'reroute': reroute, 'obstacles': gcom_obs}
        else:
            return {'reroute': reroute}

def create_obstacle_list(data = None):
    obs_list = []

    # Code for extracting obstacles from request data
    if data is not None:
        print("Getting aircraft telemetry from gcom-x")
        #obs_list = json.load(data)

    # Grab the data from the test json file and add it to the objects list
    with open('test-uas-telem.json') as f:
        obs_list = json.load(f)

    # Print the list to see that it worked
    #print(obs_list)

    return obs_list

def need_reroute(obstacles):
    """ Check if obstacles have changed enough that we require a reroute"""

    # Make a temporary list of active aircraft
    temp_obs = []
    uas_drone = {}
    
    # Add only drones that are in the air to the temporary list
    for drone in obstacles[len(obstacles) - 1]:
        if drone['team']['name'] == 'UBCUAS':
            uas_drone = drone
        elif drone['inAir'] == True:
            temp_obs.append(drone)

    # Print the list for testing
    #print("Our drone:", uas_drone, "\n")
    #print("Other aircraft:", temp_obs, "\n")

    # Compare telemetry of our aircraft to others
    for drone in temp_obs:
        # Calculate 2D distance from our drone using coordinates
        lat1, long1 = ll_to_utm(drone['telemetry']['longitude'], drone['telemetry']['latitude'])
        lat2, long2 = ll_to_utm(uas_drone['telemetry']['longitude'], uas_drone['telemetry']['latitude'])

        long_diff = long2 - long1
        lat_diff = lat2 - lat1

        # Use formula for distance between two points
        distance = sqrt((long_diff) ** 2 + (lat_diff) ** 2)
        
        print(distance)
        travelled_m = 0

        # Call function which formats objects for gcom-x
        gcom_obs = obstacles_for_gcom(temp_obs)

    return True, gcom_obs

def obstacles_for_gcom(temp_obs):
    gcom_obs = []

    return gcom_obs

# Code from gcom-x for converting
utm_meta = None
def ll_to_utm(longitude, latitude):
    """
    Converts a longitude and latitude pair into a it's utm coordinate
    """
    global utm_meta
    utm_meta = from_latlon(latitude, longitude)[2:]
    return from_latlon(latitude, longitude)[:2]

def utm_to_ll(x, y):
    """
    Converts a utm coordinate to latitude and longitude
    """
    global utm_meta
    return reversed(to_latlon(x, y, *utm_meta))

def obstacles_for_gcomx(obs):
    """ format obstacle for gcom """
    # values: latitude, longitude, radius, height
    # buffer radius based on aircraft speed, want 5 second buffer time?
    buffer_time = 5

    speed = calc_speed(obs) # units?

    radius = speed * buffer_time

    ret = {'latitude': obs['telemetry']['latitude'], 'longitude': obs['telemetry']['longitude'], 'radius': radius, 'height':  obs['telemetry']['altitude']}

    print(ret)

    return ret

def calc_speed(obs):
    return 0

if __name__ == "__main__":

    app.run(debug=True)