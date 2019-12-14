#!/usr/bin/python3

from flask import Flask, abort, request
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

def check_if_up(ip):
    for i in range(5):
        ping_result = os.system("ping -c 1 " + ip)
        if ping_result == 0:
            return True
    else:
        return False


app = Flask(__name__)
config = load_config()

@app.route("/wake", methods=['POST'])
def wake():
    if 'secret' not in request.json or \
            request.json['secret'] != config['secret']:
        return abort(403)

    # ensure eth0 is up - not sure if this is an issue with my particular Raspberry, but it looks
    # like Raspbian sometimes fails to bring the eth0 interface up when booting, if the last system
    # shutdown wasn't graceful (e.g. there was a power outage)
    interface_result = os.system('ifconfig eth0 up')
    if interface_result != 0:
        return 'can\'t bring eth0 up', 500

    # etherwake requires this server to be run as root. The reason I'm not using the wakeonlan
    # Python library anymore is because it doesn't let me pick the interface through which the magic
    # packets get sent through. This is a problem, as the main network interface of the Raspberry is
    # wlan0, which enables it to have an Internet connection through which to serve the HTTP server.
    # This is fine and dandy, until you consider that the magic packets get routed through there by
    # default as well, which kinda defeats the purpose of this endeavor.
    etherwake_result = os.system('etherwake -i eth0 ' + config['mac_to_wake'])
    if etherwake_result != 0:
        return 'is etherwake installed?', 500

    time.sleep(5) # wait a bit for the PC to wake

    return ('success', 200) if check_if_up(config['ip_to_ping']) else ('not responding', 502)

@app.route("/ping", methods=['GET'])
def ping():
    return ('success', 200) if check_if_up(config['ip_to_ping']) else ('not responding', 502)

if __name__ == "__main__":
    app.run(host=config['ip_rouser'], port=config['port_rouser'])
