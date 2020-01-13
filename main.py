#!/usr/bin/python3

from flask import Flask, abort, request
import os, time, json, subprocess

def get_abs_path(file_name):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(script_dir, file_name)

def load_config():
    config = json.load(open(get_abs_path('config.json'), 'r'))
    expected_config_keys = [
        'ip_rouser',
        'port_rouser',
        'mac_to_wake',
        'ip_to_ping_from',
        'ip_to_ping',
        'secret',
    ]

    for key in expected_config_keys:
        if key not in config:
            raise ValueError(key, 'not in config')

    return config

def check_if_up(ip):
    # ensure eth0 is on the correct IP
    os.system('ifconfig eth0 %s netmask 255.255.255.0' % config['ip_to_ping_from'])

    for i in range(5):
        ping_result = os.system("ping -c 1 " + ip)
        if ping_result == 0:
            return True
    else:
        return False


app = Flask(__name__)
config = load_config()

def valid_secret(json):
    if 'secret' not in json or json['secret'] != config['secret']:
        return False

    return True

##########################################################################
# Unrelated to rouser-pi, related to room-dash project

@app.route('/monitor/on', methods=['POST'])
def monitor_on():
    if not valid_secret(request.json):
        return abort(403)

    result = os.system('vcgencmd display_power 1')
    if result != 0:
        return 'error', 500

    return 'success', 200

@app.route('/monitor/off', methods=['POST'])
def monitor_off():
    if not valid_secret(request.json):
        return abort(403)

    result = os.system('vcgencmd display_power 0')
    if result != 0:
        return 'error', 500

    return 'success', 200

@app.route('/monitor/status', methods=['POST'])
def monitor_status():
    if not valid_secret(request.json):
        return abort(403)

    result = subprocess.run(['vcgencmd', 'display_power'], capture_output = True)
    if result.returncode != 0 or not result.stdout:
        return 'error', 500

    # stdout should look as follows:
    #   display_power=0
    status = result.stdout.decode('utf-8').strip().split('=')[1] == '1'
    return str(status), 200

##########################################################################

@app.route('/wake', methods=['POST'])
def wake():
    if not valid_secret(request.json):
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

@app.route('/ping', methods=['GET'])
def ping():
    return ('success', 200) if check_if_up(config['ip_to_ping']) else ('not responding', 502)

if __name__ == "__main__":
    app.run(host=config['ip_rouser'], port=config['port_rouser'])
