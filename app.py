import json
from flask import Flask
from flask import request
from flask import jsonify
from flask import json

app = Flask(__name__)

# Obstacle caching
obstacles = []

@app.route('/aaa', methods=['GET','POST']) # Only support posting - keeping GET for testing
def responseHandler():
    if request.method == 'GET': # 'POST' for final
        # Get the interop data; assuming data is in json, no modifications done?
        # interop = #do stuff to parse back into objects 
        #interops[request.interop.id] = request.interop

        obs_list = create_obstacle_list(request.data)

        # Save obstacle list to caching after comparing with previous list
        obstacles.append(obs_list)
        obstacles.append(obs_list)
        #print("Obstacles appended:", obstacles, "\n")
        if len(obstacles) > 5:
            obstacles.pop(0)

        # Check if need to reroute
        reroute = need_reroute(obstacles)

        # Flask 1.1.0 a view can directly return a Python dict and Flask will call jsonify automatically
        if reroute:
            return {'reroute': reroute, 'obstacles': obs_list}
        else:
            return {'reroute': reroute}

def create_obstacle_list(data = None):
    obs_list = []

    # Code for extracting obstacles from request data
    if data is not None:
        print("getting from gcom")
        obs_list = json.load(data)

    # Grab the data from the test json file and add it to the objects list
    with open('test-uas-telem.json') as f:
        obs_list = json.load(f)

    # Print the list to see that it worked
    #print(obs_list)

    return obs_list

def need_reroute(obstacles):
    """ check if obstacles have changed enough that we require a reroute"""

    # Make a temporary list of active aircraft (other than our own)
    temp_obs = []
    
    for drone in obstacles:
        if drone['inAir'] == True:
            temp_obs.append(drone)

    print(temp_obs)

    # Compare telemetry of our aircraft to others
    for drone in temp_obs:
        
        # call other function which formats objects for gcom
        obstacles_for_gcom(drone)

    return True

def obstacles_for_gcom(obs):
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

    app.run()


list = create_obstacle_list()
need_reroute(list)