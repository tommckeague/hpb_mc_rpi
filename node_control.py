import os
import sys
import time
import requests
from config import GROUND_STATION_HOST_IP, FUELLING_STATION_PI_IP, FUELLING_STATION_PI_HTTP_PORT, HEARTBEAT_INTERVAL
from helpers.mqtt_commands import connect_mqtt, publish_mqtt, close_mqtt

import os
import sys

def fuelling_station_to_host_heartbeat(host, timeout, on_success=None, on_failure=None):
    command = f"timeout {timeout} ping -c 1 {host} > /dev/null 2>&1"
    response = os.system(command)

    if response == 0:
        print(f"{host} is alive")
        if on_success:
            on_success()
    else:
        print(f"{host} is down")
        if on_failure:
            on_failure()
    sys.stdout.flush()

def fuelling_station_to_rocket_heartbeat(fuelling_station_url, timestamp):
    data = {
        'status': 'pending',
        'timestamp': timestamp,
    }
    print(data)
    response = requests.post(fuelling_station_url, json=data)
    print("Response status code:", response.status_code)
    print("Response text:", response.text)

try:
    HEARTBEAT_INTERVAL = int(HEARTBEAT_INTERVAL)
    last_time = time.time()

except Exception as e:
    print(f'Error in initialising node_control because: {e}')
    raise

while True:
    time.sleep(0.5)
    current_time = time.time()

    if current_time - last_time >= HEARTBEAT_INTERVAL:
        fuelling_station_to_host_heartbeat(GROUND_STATION_HOST_IP, 2)
        fuelling_station_to_rocket_heartbeat(f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/fuelling_station_to_rocket_heartbeat', time.time())
        last_time = current_time