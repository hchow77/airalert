# airalert
Queries air quality and alerts if air reaches an unhealthy AQI Level
using [PurpleAir's API](https://community.purpleair.com/t/making-api-calls-with-the-purpleair-api/180)
and [Pushover's notification system](https://pushover.net/).

## Setup
- Copy template.cfg to app.cfg and set the values in there.
    - Update the configurations to your own pushover credentials.
    - Update the configurations to your own PurpleAir credentials.
        - According to PurpleAir, their API credentials are free upon request.
        > If you want to use the PurpleAir API yourself, you can request your own keys by [contacting us](https://www2.purpleair.com/pages/contact-us).
        > We will need a first and last name to assign new API keys.
    - Set the Sensor value to the sensor ID of your choice. You can find this by:
        - Navigating to [PurpleAir's Map](https://map.purpleair.com/)
        - Selecting a public sensor
        - Hover your cursor over the "Get This Widget" text and select the Download Data link.
        - The sensor id should be a 5-6 digit number in the url of the link you just selected.
        - Note: Private Sensors
            - If you have a private sensor you'd like to use:
                - Retrieve the sensor ID via your registration email, where it should show up in the url links as the "show" argument.
                - Also retrieve the `read_key` in your registration email, where it should show up in the url links as the "key" argument.
                - Ex: Your "Download data" link might look something like "https://www.purpleair.com/sensorlist?show=123456&key=ABCDEF123456", where "123456" is the sensor ID, and "ABCDEF123456" is the read key.
    - Set your preferred air levels and frequency at which you would like to be notified.
        - TriggerLevel: The AQI at which if air quality goes above this level, the program will send a notification.
        - HealthyLevel: The AQI at which if the air was previously above the TriggerLevel, the program will notify if the air quality returns below HealthyLevel.
            - Note: If Trigger and Healthy are the same, then the system may spam notifications if air quality is consistently remaining at that level, so its recommended to at least set HealthyLevel a little under TriggerLevel.
        - TestInterval: The number of seconds between each query of air quality. Recommend at least 15 minutes (900) to stay friendly with Purple system and your pushover notification budget.
- If you don't already have it, install the [python-aqi library](https://pypi.org/project/python-aqi/) for calculating aqi from air quality values.
- Run the script!: `python3 airalert.py`
    - Sample Output: 
    ```
    Calling Check Air
    2022-01-01 10:00:00.000000: Readings for My Sensor - 2.5: 2.6, 10.0: 3.0, AQI: 11
    Value: 11
    ...
    Value: 93
    Value 93 is now unhealthy. Triggering unhealthy notification
    Successfully sent push note.
    ```
    - Abort the script using ctrl-c

## Troubleshooting/Development
If you're having issues with the the notification system, or just want to test run the script,
try running the script at `python3 airalert.py --test`.
This will "simulate" air quality using a random number 1-100 once every two seconds, and if your trigger is within 100,
it should eventually trigger your notification.

## python2 support
python2 branch exists, but may not work immediately. May require moderate changes or library updates depending on environment.
If your use case allows for the option, recommend using the python3 option in master.
