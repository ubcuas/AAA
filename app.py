from dis import dis
import json
import datetime
from flask import Flask
from flask import request
from flask import jsonify
from flask import json
from math import sqrt
from numpy import true_divide
from utm import to_latlon, from_latlon
import dateutil.parser

app = Flask(__name__)

BUFFER_TIME = 5

# Obstacle caching (for averaging drone position to get speed)
obstacles = []

@app.route('/aaa', methods=['GET','POST']) # Only supports posting - keeping GET for testing
def responseHandler():
    if request.method == 'GET': # 'POST' for final
        # Get the interop data; assuming data is in json, no modifications done?
        # interop = #do stuff to parse back into objects 
        #interops[request.interop.id] = request.interop

        obs_list = create_obstacle_list() # add back "request.data"

        # Add latest obstacle list to caching obstacle list
        obstacles.append(obs_list)

        ### Temporary second set of data for testing
        with open('test-uas-telem2.json') as f:
            obs_list = json.load(f)

        obstacles.append(obs_list)
        print(obstacles)
        ### Testing code ends here

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

def create_obstacle_list(): # add back "data = None"

    # Code for extracting obstacles from request data
    '''if data is not None:
        print("Getting aircraft telemetry from gcom-x")
        obs_list = json.load(data)'''

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
    gcom_obs = []

    
    # Add only drones that are in the air to the temporary list
    for drone in obstacles[len(obstacles) - 1]:
        if drone['team']['name'] == 'UBCUAS':
            uas_drone = drone
        elif drone['inAir'] == True:
            temp_obs.append(drone)

    # Print the list for testing
    #print("Our drone:", uas_drone, "\n")
    #print("Other aircraft:", temp_obs, "\n")

    x1, y1 = ll_to_utm(uas_drone['telemetry']['longitude'], uas_drone['telemetry']['latitude'])
    s1 = calc_speed(uas_drone) # TODO: change when func is implemented
    r1 = s1 * BUFFER_TIME

    # Compare telemetry of our aircraft to others
    for drone in temp_obs:
        
        x2, y2 = ll_to_utm(drone['telemetry']['longitude'], drone['telemetry']['latitude'])
        s2 = calc_speed(drone) # TODO: change when func is implemented
        r2 = s2 * BUFFER_TIME

        # only add to obstacle list if in collision zone
        if collision(x1, y1, x2, y2, r1, r2):
            # Call function which formats objects for gcom-x
            gcom_obs.append(obstacles_for_gcom(drone, r2))

    return True, gcom_obs

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

def obstacles_for_gcom(obs, radius):
    """ format obstacle for gcom """
    ret = {'latitude': obs['telemetry']['latitude'], 'longitude': obs['telemetry']['longitude'], 'radius': radius, 'height': obs['telemetry']['altitude']}
    print(ret)
    return ret

def calc_speed(obs):
    lat_history = []
    long_history = []
    timestamp_history = []
    total_distance = 0
    time_elapsed = 0
    heading = 0
    drone_speed = 0

    # Look through the obstacle caching and find total displacement as well as time passed
    for set in obstacles:
        for drone in set:
            if drone['team']['name'] == obs['team']['name']:
                # If no heading saved then save the first one
                if len(lat_history) == 0:
                    heading = drone['telemetry']['heading']
                # Check that the drone heading hasn't changed too much (rapid change in direction)
                if (abs(heading - drone['telemetry']['heading']) > 70):
                    lat_history = []
                    long_history = []
                    timestamp_history = []

                heading = drone['telemetry']['heading']

                lat, long = ll_to_utm(drone['telemetry']['longitude'], drone['telemetry']['latitude'])
                lat_history.append(lat)
                long_history.append(long)

                timestamp_history.append(drone['telemetryTimestamp'])

                break

    # Calculate total distance travelled
    for i in range(1, len(lat_history)):
        total_distance += sqrt((lat_history[i] - lat_history[i - 1]) ** 2 + (long_history[i] - long_history[i - 1]) ** 2)
        print("Total distance: ", total_distance)

    # Calculate total time elapsed
    for i in range(1, len(timestamp_history)):
        time1 = dateutil.parser.isoparse(timestamp_history[i - 1])
        time2 = dateutil.parser.isoparse(timestamp_history[i])

        time_elapsed += (time2-time1).total_seconds()
        print("Time elapsed: ", time_elapsed)
    
    # Calculate speed
    if time_elapsed != 0:
        drone_speed = total_distance / time_elapsed
    
    print("Drone speed:", drone_speed)

    return drone_speed

def collision(x1, y1, x2, y2, r1, r2):
    """ assumes all arguments have same units """
    # Calculate 2D distance using coordinates

    distance = sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))
    print("Distance between: ", distance)

    # check if within buffer radius / collision zone
    if distance <= (r1 + r2): 
        return True
    return False


if __name__ == "__main__":

    app.run(debug=True)