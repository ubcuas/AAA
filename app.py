
import json
from flask import Flask  
from flask import request
from flask import jsonify 

app = Flask(__name__)  

# some sort of caching
interops = {}
obstacles = []

@app.route('/aaa', methods=['POST']) #only support posting
def responseHandler():
    if request.method == 'POST':
        # get the interop data; assuming data is in json, no modifications done?
        # interop = #do stuff to pase back into objects 
        interops[request.interop.id] = request.interop

        obs_list = create_obstacle_list()

        # check if need to reroute
        reroute = need_reroute(obs_list)

        # Flask 1.1.0 a view can directly return a Python dict and Flask will call jsonify automatically
        if reroute:
            return {'reroute': reroute, 'obstacles': obs_list}
        else:
            return {'reroute': reroute}

def create_obstacle_list():
    obs_list = []

    # some obstacle:
    o = {'Latitude': , 'Longitude': , 'Radius': , 'Height': }

    obs_list.append(o)

    return obs_list

def need_reroute(obstacles):
    """ check if obstacles have changed enough that we require a reroute"""
    """ returns a boolean"""
    return

