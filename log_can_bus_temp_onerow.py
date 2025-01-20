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
import time
from config import (
    PI_IP,
    MQTT_BROKER_PORT,
    FUELLING_STATION_PI_IP,
    FUELLING_STATION_PI_HTTP_PORT,
    HOST_LAPTOP_IP,
    GROUND_STATION_HOST_IP,
    HEARTBEAT_INTERVAL,
    COMMAND_TIMEOUT_INTERVAL,
    RESEND_FAILED_CAN_INTERVAL,
    RESEND_FAILED_CAN_COUNT,
    SEND_HB_FUELLING_TO_ROCKET,
    RECEIVE_HB_FUELLING_TO_ROCKET,
    RECEIVE_HB_INDIVIDUAL_BOARDS_LV,
    RECEIVE_HB_INDIVIDUAL_BOARDS_GS,
    OX_PRESSURE_ID,
    OX_VENT_ID,
    ETH_VENT_ID,
    OX_OUT_ID,
    ETH_OUT_ID,
    GS_OX_IN_ID,
    GS_N2_IN_ID,
    GS_N2_VENT_ID,
    GS_OX_VENT_ID,
    SEND_KP_ID,
    RECEIVE_KP_ID,
    SEND_KI_ID,
    RECEIVE_KI_ID,
    SEND_KD_ID,
    RECEIVE_KD_ID,
    RECEIVE_PT_LV_N2_AND_ETH,
    RECEIVE_PT_LV_N20,
    RECEIVE_PT_LV_4_AND_5,
    RECEIVE_PT_LV_6,
    RECEIVE_PT_GS_1_AND_2,
    RECEIVE_PT_GS_3_AND_4,
    RECEIVE_TC_1_AND_2,
    RECEIVE_TC_3_AND_4,
    SEND_EMERGENCY_STOP,
    RECEIVE_EMERGENCY_STOP,
    SEND_FIRE_IGNITER,
    RECEIVE_FIRE_IGNITER,
    SEND_HANDOFF_CONTROL,
    RECEIVE_HANDOFF_CONTROL,
    SEND_RETAKE_CONTROL,
    RECEIVE_RETAKE_CONTROL,
)

# Constants
LOG_FILE_PATH_TEMPLATE = 'can_logging_day4_hotfire3/can_log_{timestamp}.csv'
LOG_FILE_DURATION = timedelta(minutes=10)  # Duration for each log file

log_file_lock = threading.Lock()
last_log_file_time = {}
is_first_row = True

data_to_log = {
    'timestamp1': '',
    'timestamp2': '',
    'n2_sense_A': '',
    'eth_sense_A': '',
    'ox_sense_A': '',
    'eth_press': '',
    'ox_press': '',
    'cham_press': '',
    'n2_gs': '',
    'tr2_gs': '',
    'tr3_gs': '',
    'tr4_gs': '',
    'temp1': '',
    'temp2': '',
}

def handle_RECEIVE_PT_LV_N2_AND_ETH(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['n2_sense_A'] = struct.unpack('<f', first_half)[0]
    data_to_log['eth_sense_A'] = struct.unpack('<f', second_half)[0]
    return True

def handle_RECEIVE_PT_LV_N20(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['ox_sense_A'] = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return True

def handle_RECEIVE_PT_LV_4_AND_5(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)   
    data_to_log['ox_press'] = struct.unpack('<f', first_half)[0]
    data_to_log['eth_press'] = struct.unpack('<f', second_half)[0]  
    return True 
    
def handle_RECEIVE_PT_LV_6(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['cham_press'] = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    return True

def handle_RECEIVE_PT_GS_1_AND_2(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['n2_gs'] = struct.unpack('<f', first_half)[0]
    data_to_log['tr2_gs'] = struct.unpack('<f', second_half)[0]
    return True

def handle_RECEIVE_PT_GS_3_AND_4(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['tr3_gs'] = struct.unpack('<f', first_half)[0]
    data_to_log['tr4_gs'] = struct.unpack('<f', second_half)[0]
    return True

def handle_RECEIVE_TC_1_AND_2(can_data):
    print('hitting here')
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['temp1'] = struct.unpack('<f', first_half)[0]
    data_to_log['temp2'] = struct.unpack('<f', second_half)[0]
    return True
    
def handle_RECEIVE_TC_3_AND_4(can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    data_to_log['temp1'] = struct.unpack('<f', first_half)[0]
    data_to_log['temp2'] = struct.unpack('<f', second_half)[0]
    return True

can_id_to_function = {
    RECEIVE_PT_LV_N2_AND_ETH: 'RECEIVE_PT_LV_N2_AND_ETH',
    RECEIVE_PT_LV_N20: 'RECEIVE_PT_LV_N20',
    RECEIVE_PT_LV_4_AND_5: 'RECEIVE_PT_LV_4_AND_5',
    RECEIVE_PT_LV_6: 'RECEIVE_PT_LV_6',
    RECEIVE_PT_GS_1_AND_2: 'RECEIVE_PT_GS_1_AND_2',
    RECEIVE_PT_GS_3_AND_4: 'RECEIVE_PT_GS_3_AND_4',
    RECEIVE_TC_1_AND_2: 'RECEIVE_TC_1_AND_2',
    RECEIVE_TC_3_AND_4: 'RECEIVE_TC_3_AND_4'
}

def return_data_for_can_id(can_id, received_data):
    id_string = can_id_to_function[can_id]
    try:
        func_name = f'handle_{id_string}'
        func = globals().get(func_name)
        if func:
            return func(received_data)
        else:
            print(f"No handler function for ID {id_string}")
    except Exception as e:
        print(f"Error executing function for CAN ID {id_string}: {e}")


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
        log_file_path = LOG_FILE_PATH_TEMPLATE.format(timestamp=timestamp)
    else:
        timestamp = last_log_file_time[can_id].strftime('%d_%m_%y_%H-%M')
        log_file_path = LOG_FILE_PATH_TEMPLATE.format(timestamp=timestamp)

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
    global is_first_row
    can_id = hex(msg.arbitration_id)
    with log_file_lock:
        log_file_path = get_log_file_path(can_id)
        with open(log_file_path, 'a', newline='') as log_file:
            csv_writer = csv.writer(log_file)
            timestamp_str = datetime.utcnow().isoformat()
            data_to_log['timestamp1'] = timestamp_str
            data_to_log['timestamp2'] = time.time_ns()
            
            channel = msg.channel
            timestamp = msg.timestamp
            is_proceed = return_data_for_can_id(can_id, msg.data)
            if is_proceed:
                csv_writer = csv.DictWriter(log_file, fieldnames=data_to_log.keys())
                if is_first_row:
                    csv_writer.writeheader()
                    csv_writer.writerow(data_to_log)
                    is_first_row = False
                else:    
                    csv_writer.writerow(data_to_log)
                print('CAN msg logged')
            else:
                print('Error parsing data')

def can_listener(bus):
    try:
        print(f'Listening on {bus.channel_info}')
        while True:
            try:
                msg = bus.recv(1)
                if msg is not None:
                    can_id = hex(msg.arbitration_id)
                    log_can_message(msg)

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
