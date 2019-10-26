#!/usr/bin/python3

from flask import Flask, abort, request
from wakeonlan import send_magic_packet
import os, time, json

def get_abs_path(file_name):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(script_dir, file_name)

def load_config():
    config = json.load(open(get_abs_path('config.json'), 'r'))
    expected_config_keys = [
        'ip_rouser',
        'port_rouser',
        'mac_to_wake',
        'ip_to_ping',
        'secret',
    ]

    for key in expected_config_keys:
        if key not in config: raise ValueError(key, 'not in config')

    return config


app = Flask(__name__)
config = load_config()

@app.route("/wake", methods=['POST'])
def home():
    if 'secret' not in request.json or \
            request.json['secret'] != config['secret']:
        return abort(403)

    send_magic_packet(config['mac'])
    time.sleep(2) # wait a bit for the PC to wake

    # ping PC, see if it's up
    ping_result = os.system("ping -c 1 " + config['ip'])

    if ping_result == 0:
        return 'success', 200
    else:
        return 'gone', 410

if __name__ == "__main__":
    app.run(host=config['ip_rouser'], port=config['port_rouser'])
