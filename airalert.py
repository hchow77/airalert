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

try:
    import aqi
except ModuleNotFoundError:
    print("Missing aqi lib. Run `python3 -m pip install python-aqi` (may require sudo)")
    sys.exit(1)

config = configparser.ConfigParser()

def fetchAqi():
    print("Calling Check Air")
    purple_configs = config['purpleair']
    read_key = purple_configs['ReadKey']
    sensor_id = purple_configs['Sensor']

    conn = http.client.HTTPSConnection("api.purpleair.com")
    conn.request(
      "GET",
      f"/v1/sensors/{sensor_id}",
      headers={"X-API-Key": read_key}
    )

    response = conn.getresponse().read().decode()
    results = json.loads(response)
    result = results['sensor']
    this_aqi = aqi.to_aqi([
      (aqi.POLLUTANT_PM25, result['pm2.5_atm']),
      (aqi.POLLUTANT_PM10, result['pm10.0_atm'])
    ])
    ct = datetime.datetime.now()
    print(f"{ct}: Readings for {result['name']} - 2.5: {result['pm2.5_atm']}, 10.0: {result['pm10.0_atm']}, AQI: {this_aqi}")
    return this_aqi

def sendMessage(message):
    push_configs = config['pushdata']
    push_token = push_configs['PushToken']
    push_user = push_configs['PushUser']

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
    import random
    
    healthy = True
    while True:
        #value = random.randint(1,100)
        value = fetchAqi()
        print(f"Value: {value}")

        if healthy:
            if value >= trigger_level:
                print(f"Value {value} is now unhealthy. Triggering unhealthy notification")
                sendMessage(f"Unhealthy AQI detected at {value}!")
                healthy = False
        else:
            if value <= healthy_level:
                print(f"Value {value} is now healthy! Triggering healthy notification")
                sendMessage(f"AQI is healthy again at {value}")
                healthy = True

        time.sleep(test_interval)

#parser = argparse.ArgumentParser()
#parser.add_argument('message', help="Message to send as a push note")
#args = parser.parse_args()

configpath = os.path.join(os.path.dirname(__file__), 'app.cfg')
config.read(configpath)

try:
    run()
except KeyboardInterrupt:
    print("Air Alert was halted by user")

