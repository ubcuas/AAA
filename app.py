import json
from flask import Flask
from flask import request
from flask import jsonify
from flask import json

app = Flask(__name__)

# Obstacle caching
interops = {}
obstacles = []

@app.route('/aaa', methods=['GET','POST']) # Only support posting - keeping GET for testing
def responseHandler():
    if request.method == 'GET': # 'POST' for final
        # Get the interop data; assuming data is in json, no modifications done?
        # interop = #do stuff to parse back into objects 
        #interops[request.interop.id] = request.interop

        obs_list = create_obstacle_list()

        # Check if need to reroute
        reroute = need_reroute(obs_list)

        # Save obstacle list to caching after comparing with previous list
        obstacles = obs_list

        # Flask 1.1.0 a view can directly return a Python dict and Flask will call jsonify automatically
        if reroute:
            return {'reroute': reroute, 'obstacles': obs_list}
        else:
            return {'reroute': reroute}

def create_obstacle_list():
    obs_list = []

    # Grab the data from the test json file and add it to the objects list
    with open('test-uas-telem.json') as f:
        obs_list = json.load(f)

    # Print the list to see that it worked
    print(obs_list)

    return obs_list

def need_reroute(obstacles):
    """ check if obstacles have changed enough that we require a reroute"""

    # No reroute needed if it is the first telemtry received
    if obstacles == None:
        return False
    # Make a temporary list of active aircraft (other than our own)
    temp_obs = []

    for obs in obstacles:
        if obs.inAir == "true":
            temp_obs.append(obs)
    
    print(temp_obs)

    # Compare telemetry of our aircraft to others

    """ returns a boolean"""
    return True

if __name__ == "__main__":

    app.run()