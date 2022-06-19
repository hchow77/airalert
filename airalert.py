#!/usr/bin/python

import httplib, urllib
import pprint
import sys
import json
import argparse
import time
import os
import random

try:
    import aqi
    import configparser
except ImportError as e:
    print("Module Missing! - " + str(e))
    print("Run `python -m pip install <module>` (may require sudo) {python-aqi, configparser}")
    sys.exit(1)

config = configparser.ConfigParser()
TEST_MODE = False

def fetchAqi():
    print("Calling Check Air")
    purple_configs = config['purpleair']
    read_key = purple_configs['ReadKey']
    sensor_id = purple_configs['Sensor']

    conn = httplib.HTTPSConnection("api.purpleair.com")
    conn.request(
      "GET",
      "/v1/sensors/{sensor_id}".format(sensor_id=sensor_id),
      headers={"X-API-Key": read_key}
    )

    response = conn.getresponse().read().decode()
    results = json.loads(response)
    result = results['sensor']
    this_aqi = aqi.to_aqi([
      (aqi.POLLUTANT_PM25, result['pm2.5_atm']),
      (aqi.POLLUTANT_PM10, result['pm10.0_atm'])
    ])
    print(
        "Readings for " + result['name'] + " - "
        + "2.5: " + str(result['pm2.5_atm'])
        + ", 10.0: " + str(result['pm10.0_atm'])
        + ", AQI: " + str(this_aqi)
    )
    return this_aqi

def sendMessage(message):
    push_configs = config['pushdata']
    push_token = push_configs['PushToken']
    push_user = push_configs['PushUser']

    if TEST_MODE:
        message = "TEST: " + message

    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.urlencode({
        "token": push_token,
        "user": push_user,
        "message": message,
      }), { "Content-type": "application/x-www-form-urlencoded" })

    response = conn.getresponse().read().decode()
    results = json.loads(response)
    status = results.get('status', -1)
    if status == 1:
        print("Successfully sent push note.")
    else:
        print("Failed to send push note!")

def run():
    trigger_level = config.getint('configlevels', 'TriggerLevel') # AQI Levels
    healthy_level = config.getint('configlevels', 'HealthyLevel')
    test_interval = config.getfloat('configlevels', 'TestInterval') # Time in seconds
    
    healthy = True
    while True:
        if TEST_MODE:
            value = random.randint(1,100)
            test_interval = 2.0
        else:
            value = fetchAqi()
        print("Value: " + str(value))

        if healthy:
            if value >= trigger_level:
                print("Value {value} is now unhealthy. Triggering unhealthy notification".format(value=value))
                sendMessage("Unhealthy AQI detected at {value}!".format(value=value))
                healthy = False
        else:
            if value <= healthy_level:
                print("Value {value} is now healthy! Triggering healthy notification".format(value=value))
                sendMessage("AQI is healthy again at {value}".format(value=value))
                healthy = True

        time.sleep(test_interval)

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--test', action='store_true', help="Run in test mode, generating fake values with a 2 second iteration.")
args = parser.parse_args()

if args.test:
    TEST_MODE = True

configpath = os.path.join(os.path.dirname(__file__), 'app.cfg')
config.read(configpath)

try:
    run()
except KeyboardInterrupt:
    print("Air Alert was halted by user")

