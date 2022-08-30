#!/usr/bin/python3

import http.client, urllib
import pprint
import sys
import json
import argparse
import configparser
import time
import os
import datetime
import random

try:
    import aqi
except ModuleNotFoundError:
    print("Missing aqi lib. Run `python3 -m pip install python-aqi` (may require sudo)")
    sys.exit(1)

config = configparser.ConfigParser()
TEST_MODE = False

def fetchAqi():
    print("Calling Check Air")
    purple_configs = config['purpleair']
    read_key = purple_configs['ReadKey']
    sensor_id = purple_configs['Sensor']
    private_key = purple_configs.get('PrivateReadKey')

    url = f"/v1/sensors/{sensor_id}"

    # Not sure why purple isn't accepting urlencoded creds, but seems like manual appending like this works for now.
    if private_key:
        url += f"?read_key={private_key}"

    conn = http.client.HTTPSConnection("api.purpleair.com")
    try:
      conn.request(
        "GET",
        url,
        headers={"X-API-Key": read_key}
      )
    except TimeoutError:
      print(f"AQI request for {sensor_id} timedout. Retrying later...", file=sys.stderr)

    response = conn.getresponse().read().decode()
    results = json.loads(response)
    result = results['sensor']
    this_aqi = aqi.to_aqi([
      (aqi.POLLUTANT_PM25, result['pm2.5_atm']),
      (aqi.POLLUTANT_PM10, result['pm10.0_atm'])
    ])
    ct = datetime.datetime.now()
    location = result['name']
    print(f"{ct}: Readings for {location} - 2.5: {result['pm2.5_atm']}, 10.0: {result['pm10.0_atm']}, AQI: {this_aqi}")
    return {'aqi':this_aqi, 'location':location}

def sendMessage(message):
    push_configs = config['pushdata']
    push_token = push_configs['PushToken']
    push_user = push_configs['PushUser']

    if TEST_MODE:
        message = "TEST: " + message

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
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
    timeout = 0
    while True:
        if TEST_MODE:
            data = {'aqi':random.randint(1,100), 'location':"TEST"}
            test_interval = 2.0
        else:
            data = fetchAqi()

        if not data:
            timeout += 1
            if timeout >= 3:
                print("System Timed Out more than 3 times in a row. Aborting...")
                sys.exit(1)
            time.sleep(test_interval)
            continue
        else:
            timeout = 0

        value = data['aqi']
        location = data['location']
        print(f"Value for {location}: {value}")

        if healthy:
            if value >= trigger_level:
                print("Value {value} is now unhealthy. Triggering unhealthy notification".format(value=value))
                sendMessage("Unhealthy AQI detected for {location} at {value}!".format(location=location, value=value))
                healthy = False
        else:
            if value <= healthy_level:
                print("Value {value} is now healthy! Triggering healthy notification".format(value=value))
                sendMessage("AQI is healthy again for {location} at {value}".format(location=location, value=value))
                healthy = True

        time.sleep(test_interval)

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--test', action='store_true', help="Run in test mode, generating fake values with a 2 second iteration.")
parser.add_argument('--config', nargs='?', default='app.cfg', help="Path to the config file. Defaults to 'app.cfg' in directory with this script.")
args = parser.parse_args()

if args.test:
    TEST_MODE = True

configpath = os.path.join(os.path.dirname(__file__), args.config)
config.read(configpath)

try:
    run()
except KeyboardInterrupt:
    print("Air Alert was halted by user")

