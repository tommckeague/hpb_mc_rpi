import os
import can
import struct
import time
import requests
from config import GROUND_STATION_HOST_IP, FUELLING_STATION_PI_IP, FUELLING_STATION_PI_HTTP_PORT, HEARTBEAT_INTERVAL
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import influxdb_client

from helpers.mqtt_commands import connect_mqtt, publish_mqtt, close_mqtt
from helpers.can_commands import initialise_can, close_can, can_msg_to_double, can_msg_to_uint8
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


broker = GROUND_STATION_HOST_IP
port = MQTT_BROKER_PORT
client_id = 'publish-fuellingpi2'

# Functions for each CAN ID
# def handle_can_id_106(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_1', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_2', float2)

# def handle_can_id_107(can_data):
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)  
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_3', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_4', float2)

# def handle_can_id_108(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     print("trans6: ", float2)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_5', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_6', float2)
    
# def handle_can_id_109(can_data):
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)  
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     print("trans7: ", float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_7', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_8', float2)


# def handle_can_id_110(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_9', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_10', float2)

# def handle_can_id_111(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_11', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_12', float2)
    
    
# def handle_can_id_121(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_13', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_14', float2)
    
# def handle_can_id_122(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_15', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_16', float2)


# def handle_can_id_123(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_17', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_18', float2)
    

# def handle_can_id_124(can_data):
#     can_data = list(can_data)
#     first_half = can_data[:4]
#     second_half = can_data[4:]
#     first_half = bytes(first_half)
#     second_half = bytes(second_half)    
#     float1 = struct.unpack('<f', first_half)[0]
#     float2 = struct.unpack('<f', second_half)[0]
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_19', float1)
#     publish_mqtt(client, 'pressure_transducer/pressure_reading_20', float2)


# def handle_can_id_5(can_data):
#     byte_list = can_msg_to_uint8(can_data)
#     for i in range(1,5,1):
#         topic = f'pressure_transducer/opening_reading_{i}'
#         publish_mqtt(client, topic, byte_list[i-1])

# def handle_can_id_6(can_data):
#     return
# def handle_can_id_101(can_data):
#     data = {
#         'status': 'completed',
#         'timestamp': can_msg_to_double(can_data),
#     }
#     print(data)
#     response = requests.post(f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/fuelling_station_to_rocket_heartbeat', json=data)
#     print("Response status code:", response.status_code)
#     print("Response text:", response.text)

# def handle_can_id_102(can_data):
#     byte_list = can_msg_to_uint8(can_data)
#     for i in range(1,8,1):
#         topic = f'heartbeat/individual_boards_{i}'
#         publish_mqtt(client, topic, byte_list[i-1])
#     return

# def handle_can_id_103(can_data):
#     byte_list = can_msg_to_uint8(can_data)
#     topic = f'heartbeat/individual_boards_9'
#     publish_mqtt(client, topic, byte_list[0])
#     return

# NEW CANs
# Gains
def handle_RECEIVE_KP_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')
def handle_RECEIVE_KI_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')
def handle_RECEIVE_KD_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')

# Flight computer
def handle_RECEIVE_EMERGENCY_STOP(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')
def handle_RECEIVE_FIRE_IGNITER(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')
def handle_RECEIVE_HANDOFF_CONTROL(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')
def handle_RECEIVE_RETAKE_CONTROL(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'general_command_receipt')

# Servos
def handle_OX_PRESSURE_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_OX_VENT_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_ETH_VENT_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_OX_OUT_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_ETH_OUT_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_GS_OX_IN_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_GS_N2_IN_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_GS_N2_VENT_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')
def handle_GS_OX_VENT_ID(can_id, can_data):
    send_upload_command_receipt(can_id, can_data,'servo_command_receipt')

# Hearbeats
def handle_RECEIVE_HB_FUELLING_TO_ROCKET(can_id, can_data):
    data = {
        'status': 'completed',
        'timestamp': can_msg_to_double(can_data),
    }
    print(data)
    response = requests.post(f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/fuelling_station_to_rocket_heartbeat', json=data)
    print("Response status code:", response.status_code)
    print("Response text:", response.text)
    return
def handle_RECEIVE_HB_INDIVIDUAL_BOARDS_LV(can_id, can_data):
    byte_list = can_msg_to_uint8(can_data)
    for i in range(1,8,1):
        topic = f'heartbeat/individual_boards_{i}'
        publish_mqtt(client, topic, byte_list[i-1])
    return
def handle_RECEIVE_HB_INDIVIDUAL_BOARDS_GS(can_id, can_data):
    byte_list = can_msg_to_uint8(can_data)
    topic = f'heartbeat/individual_boards_9'
    publish_mqtt(client, topic, byte_list[0])
    return

# Pressure Transducers
def handle_RECEIVE_PT_LV_N2_AND_ETH(can_id, can_data):
    print(can_data)
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/pressure_reading_1', float1)
    publish_mqtt(client, 'pressure_transducer/pressure_reading_2', float2)
def handle_RECEIVE_PT_LV_N20(can_id, can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/pressure_reading_3', float1)
def handle_RECEIVE_PT_LV_4_AND_5(can_id, can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/pressure_reading_4', float1)
    publish_mqtt(client, 'pressure_transducer/pressure_reading_6', float2)

def handle_RECEIVE_PT_LV_6(can_id, can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/pressure_reading_5', float1)
def handle_RECEIVE_PT_GS_1_AND_2(can_id, can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/pressure_reading_7', float1)
    publish_mqtt(client, 'pressure_transducer/pressure_reading_8', float2)
def handle_RECEIVE_PT_GS_3_AND_4(can_id, can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/pressure_reading_9', float1)
    publish_mqtt(client, 'pressure_transducer/pressure_reading_10', float2)
def handle_RECEIVE_TC_1_AND_2(can_id, can_data):
    print('hitting here')
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/temperature_reading_1', float1)
    publish_mqtt(client, 'pressure_transducer/temperature_reading_2', float2)
def handle_RECEIVE_TC_3_AND_4(can_id, can_data):
    can_data = list(can_data)
    first_half = can_data[:4]
    second_half = can_data[4:]
    first_half = bytes(first_half)
    second_half = bytes(second_half)    
    float1 = struct.unpack('<f', first_half)[0]
    float2 = struct.unpack('<f', second_half)[0]
    publish_mqtt(client, 'pressure_transducer/temperature_reading_3', float1)
    publish_mqtt(client, 'pressure_transducer/temperature_reading_4', float2)

def send_upload_command_receipt(can_id, can_data, endpoint):
    data = {'status': 'completed', 'can_id': can_id, 'data_field': can_data.hex()}
    url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/{endpoint}'
    try:
        response = requests.post(url, json=data)
        return response
    except requests.exceptions.RequestException as e:
        print("Error while sending command receipt to http:", e)
        return None

def execute_code_for_can_id(id_string, can_id, received_data):
    try:
        func_name = f'handle_{id_string}'
        func = globals().get(func_name)
        if func:
            func(can_id, received_data)
        else:
            print(f"No handler function for ID {id_string}")
    except Exception as e:
        print(f"Error executing function for CAN ID {id_string}: {e}")

# Initialisations
try:
    client = connect_mqtt(client_id, broker, port)
    # can_bus = initialise_can('can0')
    # Using same bus
    can_bus = can.interface.Bus(channel='can1', interface='socketcan')
    
    # Loading in receive CAN ids
    can_id_map = {
        SEND_KP_ID: 'SEND_KP_ID',
        RECEIVE_KP_ID: 'RECEIVE_KP_ID',
        SEND_KI_ID: 'SEND_KI_ID',
        RECEIVE_KI_ID: 'RECEIVE_KI_ID',
        SEND_KD_ID: 'SEND_KD_ID',
        RECEIVE_KD_ID: 'RECEIVE_KD_ID',
        OX_PRESSURE_ID: 'OX_PRESSURE_ID',
        OX_VENT_ID: 'OX_VENT_ID',
        ETH_VENT_ID: 'ETH_VENT_ID',
        OX_OUT_ID: 'OX_OUT_ID',
        ETH_OUT_ID: 'ETH_OUT_ID',
        GS_OX_IN_ID: 'GS_OX_IN_ID',
        GS_N2_IN_ID: 'GS_N2_IN_ID',
        GS_N2_VENT_ID: 'GS_N2_VENT_ID',
        GS_OX_VENT_ID: 'GS_OX_VENT_ID',
        RECEIVE_PT_LV_N2_AND_ETH: 'RECEIVE_PT_LV_N2_AND_ETH',
        RECEIVE_PT_LV_N20: 'RECEIVE_PT_LV_N20',
        RECEIVE_PT_LV_4_AND_5: 'RECEIVE_PT_LV_4_AND_5',
        RECEIVE_PT_LV_6: 'RECEIVE_PT_LV_6',
        RECEIVE_PT_GS_1_AND_2: 'RECEIVE_PT_GS_1_AND_2',
        RECEIVE_PT_GS_3_AND_4: 'RECEIVE_PT_GS_3_AND_4',
        RECEIVE_TC_1_AND_2: 'RECEIVE_TC_1_AND_2',
        RECEIVE_HB_FUELLING_TO_ROCKET:'RECEIVE_HB_FUELLING_TO_ROCKET',
        RECEIVE_HB_INDIVIDUAL_BOARDS_GS:'RECEIVE_HB_INDIVIDUAL_BOARDS_GS', # one in first index
        RECEIVE_HB_INDIVIDUAL_BOARDS_LV: 'RECEIVE_HB_INDIVIDUAL_BOARDS_LV' # full 8 bits
    }

except:
    print('Error in initialisation')
    raise

try:
    print(can_id_map)
    while True:
        try:
            msg = can_bus.recv(1)
            if msg is not None:
                can_id = hex(msg.arbitration_id)
                can_data = msg.data
                if can_id in can_id_map:
                    print('here')
                    execute_code_for_can_id(can_id_map[can_id], can_id, can_data)

        except Exception as e:
            print(f"Error receiving CAN: {e}")
except KeyboardInterrupt:
    print('Keyboard interrupt exit')

finally:
#    close_can(can_bus)
    close_mqtt(client)
    

