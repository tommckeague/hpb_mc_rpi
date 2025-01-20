import can
import subprocess
from datetime import datetime, timedelta
import threading
import os
import csv
from helpers.influx_commands import connect_influxdb, write_to_influx, close_influx
from helpers.can_commands import initialise_can, can_msg_to_double, can_msg_to_uint8
from dotenv import load_dotenv
import struct

# Constants
LOG_FILE_PATH_TEMPLATE = 'can_logging_water_test_2/{can_id}/can_log_{timestamp}.csv'
LOG_FILE_DURATION = timedelta(minutes=10)  # Duration for each log file

log_file_lock = threading.Lock()
last_log_file_time = {}

# Functions for each CAN ID
def handle_can_id_106(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_107(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)  
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_108(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]
    
def handle_can_id_109(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)  
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_110(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_111(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]
    
def handle_can_id_121(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_122(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_123(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_124(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return [float1, float2]

def handle_can_id_101(can_data):
    float1 = can_msg_to_double(can_data)
    #write_to_influx(write_api, "hypower", "can_logging", "measurement", 'id_101_', float1)
    print('written: ', float1)
    return [float1]

def handle_can_id_102(can_data):
    ints = can_msg_to_uint8(can_data)
    return ints

def handle_can_id_103(can_data):
    ints = can_msg_to_uint8(can_data)
    return ints

can_id_to_function = {
    '0x101': handle_can_id_101,
    '0x102': handle_can_id_102,
    '0x103': handle_can_id_103,
    '0x106': handle_can_id_106,
    '0x107': handle_can_id_107,
    '0x108': handle_can_id_108,
    '0x109': handle_can_id_109,
    '0x110': handle_can_id_110,
    '0x111': handle_can_id_111,
    '0x121': handle_can_id_121,
    '0x122': handle_can_id_122,
    '0x123': handle_can_id_123,
    '0x124': handle_can_id_124,
}

def return_data_for_can_id(received_id, recieved_data):
    func = can_id_to_function.get(received_id)
    if func:
        return func(recieved_data)  # Call the function associated with the ID
    else:
        print(f"No handler function for ID {received_id}")

def get_log_file_path(can_id):
    global last_log_file_time
    current_time = datetime.utcnow()

    # Initialize last_log_file_time for new CAN IDs
    if can_id not in last_log_file_time:
        last_log_file_time[can_id] = current_time

    # Rotate log file if 10 minutes have passed
    if current_time - last_log_file_time[can_id] >= LOG_FILE_DURATION:
        last_log_file_time[can_id] = current_time
        timestamp = current_time.strftime('%d_%m_%y_%H-%M')
        log_file_path = LOG_FILE_PATH_TEMPLATE.format(can_id=can_id, timestamp=timestamp)
    else:
        timestamp = last_log_file_time[can_id].strftime('%d_%m_%y_%H-%M')
        log_file_path = LOG_FILE_PATH_TEMPLATE.format(can_id=can_id, timestamp=timestamp)

    # Ensure the directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    return log_file_path

def initialize_can_interface(interface):
    try:
        result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
        if 'UP' not in result.stdout:
            can0 = initialise_can('can0')
            print(f'{interface} needs to be up before logging.')
            raise Exception(f'{interface} is down')
        return can.interface.Bus(channel=interface, interface='socketcan')
    except Exception as e:
        print(f'Error initializing CAN interface: {e}')
        raise

def log_can_message(msg):
    can_id = hex(msg.arbitration_id)
    with log_file_lock:
        log_file_path = get_log_file_path(can_id)
        with open(log_file_path, 'a', newline='') as log_file:
            csv_writer = csv.writer(log_file)
            timestamp_str = datetime.utcnow().isoformat()

            channel = msg.channel
            timestamp = msg.timestamp
            message_id = can_id
            processed_data = return_data_for_can_id(can_id, msg.data)
            raw_data = msg.data.hex()
            csv_writer.writerow([
                timestamp_str,
                channel,
                timestamp,
                message_id,
                raw_data,
                *processed_data,
            ])
            print('CAN msg logged')

def can_listener(bus):
    try:
        print(f'Listening on {bus.channel_info}')
        while True:
            try:
                msg = bus.recv(1)
                if msg is not None:
                    log_can_message(msg)
                    can_id = hex(msg.arbitration_id)
            except Exception as e:
                print(f'Error receiving CAN message: {e}')
    except KeyboardInterrupt:
        print(f'Keyboard interrupt detected on {bus.channel_info}. Exiting...')
    finally:
        bus.shutdown()  # Close the CAN interface
        print(f'CAN interface {bus.channel_info} closed.')

def main():
    try:
        can0 = initialize_can_interface('can0')
        #can1 = initialize_can_interface('can1')
        load_dotenv()
        GROUND_STATION_HOST_IP = os.getenv('GROUND_STATION_HOST_IP')
        #influx_url = f"http://{GROUND_STATION_HOST_IP}:8086"
        #client, write_api, query_api = connect_influxdb(influx_url, "hypower", "hypower")
    except Exception as e:
        print(f'Initialization failed: {e}')
        return

    print('CAN interfaces initialized. Logging started.')

    # Create and start threads for each CAN interface
    try:
        can0_thread = threading.Thread(target=can_listener, args=(can0,))
        #can1_thread = threading.Thread(target=can_listener, args=(can1,))
        can0_thread.start()
        #can1_thread.start()

        # Wait for threads to finish
        can0_thread.join()
        #can1_thread.join()
    except KeyboardInterrupt:
        print('Keyboard interrupt detected. Exiting...')

if __name__ == '__main__':
    main()
