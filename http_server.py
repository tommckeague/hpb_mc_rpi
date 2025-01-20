from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timedelta
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import serial
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import time
from helpers.can_commands import initialise_can, send_can_message, close_can, double_to_can_msg, str_to_can_msg, can_msg_to_str
from helpers.GPIO_commands import initialise_GPIO, close_GPIO, duty_cycle_from_angle
from helpers.mqtt_commands import connect_mqtt, publish_mqtt, close_mqtt
from helpers.influx_commands import connect_influxdb, read_from_influx, write_to_influx, close_influx
from helpers.automated_stages import stages_keys, fuelling_stages
import RPi.GPIO as GPIO
import os
from dotenv import load_dotenv
import requests
import httpx

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
    OX_AND_ETH_SIMULTANEOUSLY_ID,
    SEND_KP_ID,
    RECEIVE_KP_ID,
    SEND_KI_ID,
    RECEIVE_KI_ID,
    SEND_KD_ID,
    RECEIVE_KD_ID,
    RECEIVE_PT_LV_N2_AND_ETH,
    RECEIVE_PT_LV_N20,
    RECEIVE_PT_LV_6,
    RECEIVE_PT_LV_4_AND_5,
    RECEIVE_PT_GS_1_AND_2,
    RECEIVE_PT_GS_3_AND_4,
    RECEIVE_TC_1_AND_2,
    SEND_EMERGENCY_STOP,
    RECEIVE_EMERGENCY_STOP,
    SEND_FIRE_IGNITER,
    RECEIVE_FIRE_IGNITER,
    SEND_HANDOFF_CONTROL,
    RECEIVE_HANDOFF_CONTROL,
    SEND_RETAKE_CONTROL,
    RECEIVE_RETAKE_CONTROL,
    SEND_INIT_OXVENT,
    SEND_INIT_ENGINE_IGNITION,
    OX_VENT_UPPER_BOUND, 
    OX_VENT_LOWER_BOUND, 
    OX_VENT_OPEN_PERCENTAGE,
    IGNITER_START_DELAY,
    OX_FILL_SET_OPEN_PERCENTAGE,
    OX_FILL_VALVE_OPEN_ANGLE,
    CHAMBER_MAX_PRESSURE_TIME_LIMIT,
)

# Helper functions
pending_requests: Dict[str, asyncio.TimerHandle] = {}

async def check_timeout(can_bus, can_id: str, key: str, handle_timeout_func, interval:int):
    await asyncio.sleep(interval)
    if key in pending_requests:
        # Timer expired and no completion received
        del pending_requests[key]
        print(f"Timeout occurred for key: {key}")
        handle_timeout_func(can_bus, can_id, key)

async def send_repeated_CAN(can_bus, can_id, can_data):
    for i in range(RESEND_FAILED_CAN_COUNT):
        send_can_message(can_bus, can_id, can_data)
        await asyncio.sleep(RESEND_FAILED_CAN_INTERVAL)

def handle_timeout_heartbeat(can_id: str, timestamp: str):
    print(f"Handling timeout for timestamp: {timestamp}")
    publish_mqtt(client_mqtt, 'heartbeat/rocket_to_fuelling_station', '0')

def handle_completion_heartbeat(can_id: str, timestamp: str):
    print(f"Handling completion for timestamp: {timestamp}")
    publish_mqtt(client_mqtt, 'heartbeat/rocket_to_fuelling_station', '100')

def handle_timeout_general_command_receipt(can_bus, can_id: str, communication_identifier: str):
    data_bytes = bytes.fromhex(communication_identifier)
    can_data = bytearray(data_bytes)
    can_id = int(can_id, 16)
    send_repeated_CAN(can_bus, can_id, can_data)
    return None
    # print(f"Handling timeout for timestamp: {timestamp}")
    # publish_mqtt(client_mqtt, 'heartbeat/rocket_to_fuelling_station', '0')

def handle_completion_general_command_receipt(can_bus, can_id: str, communication_identifier: str):
    data_bytes = bytes.fromhex(communication_identifier)
    can_data = bytearray(data_bytes)
    can_id = int(can_id, 16)
    if can_data[0] == can_data[2] and can_data[1] == can_data[3]:
        send_can_message(can1, can_id, [can_data[0],can_data[1],can_data[2],can_data[3],1,0,0,0])
    print(f"Handling completion for servo communication_identifier: {can_data}")
    # publish_mqtt(client_mqtt, 'heartbeat/rocket_to_fuelling_station', '100')

def handle_timeout_fire_igniter_command_receipt(can_bus, can_id: str, communication_identifier: str):
    data_bytes = bytes.fromhex(communication_identifier)
    can_data = bytearray(data_bytes)
    can_id = int(can_id, 16)


def handle_completion_fire_igniter_command_receipt(can_bus, can_id: str, communication_identifier: str):
    data_bytes = bytes.fromhex(communication_identifier)
    can_data = bytearray(data_bytes)
    can_id = int(can_id, 16)
    
def handle_emergency_stop(can_bus):
    cl = 180
    op = 1
    print('entered message')
    can_id = can_id_map['OX_OUT_ID']
    print(can_id)
    can_id = int(can_id, 16)
    print(can_id)
    can_data = [3, cl, 3, cl, 1, 0, 0, 0]
    print(can_data)
    send_can_message(can1, can_id, can_data)  # Send CAN message
    print('entered message')
    can_id = can_id_map['ETH_OUT_ID']
    can_id = int(can_id, 16)
    can_data = [4, cl, 4, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['OX_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [1, op, 1, op, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['ETH_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [2, cl, 2, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['OX_PRESSURE_ID']
    can_id = int(can_id, 16)
    print('here',can_id)
    can_data = [0, op, 0, op, 1, 0, 0, 0]
    print('here',can_data)
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_N2_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [2, op, 2, op, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_OX_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [3, op, 3, op, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_N2_IN_ID']
    can_id = int(can_id, 16)
    can_data = [1, cl, 1, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_OX_IN_ID']
    can_id = int(can_id, 16)
    can_data = [0, cl, 0, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    


try: 
    can_id_map = {
        'SEND_KP_ID': SEND_KP_ID,
        'RECEIVE_KP_ID': RECEIVE_KP_ID,
        'SEND_KI_ID': SEND_KI_ID,
        'RECEIVE_KI_ID': RECEIVE_KI_ID,
        'SEND_KD_ID': SEND_KD_ID,
        'RECEIVE_KD_ID': RECEIVE_KD_ID,
        'OX_PRESSURE_ID': OX_PRESSURE_ID,
        'OX_VENT_ID': OX_VENT_ID,
        'ETH_VENT_ID': ETH_VENT_ID,
        'OX_OUT_ID': OX_OUT_ID,
        'ETH_OUT_ID': ETH_OUT_ID,
        'GS_OX_IN_ID': GS_OX_IN_ID,
        'GS_N2_IN_ID': GS_N2_IN_ID,
        'GS_N2_VENT_ID': GS_N2_VENT_ID,
        'GS_OX_VENT_ID': GS_OX_VENT_ID,
        'OX_AND_ETH_SIMULTANEOUSLY_ID': OX_AND_ETH_SIMULTANEOUSLY_ID,
        'SEND_INIT_OXVENT':SEND_INIT_OXVENT,
        'SEND_INIT_ENGINE_IGNITION':SEND_INIT_ENGINE_IGNITION,
        'SEND_FIRE_IGNITER': SEND_FIRE_IGNITER,
        'SEND_EMERGENCY_STOP':SEND_EMERGENCY_STOP
    }

    # CAN
    can1 = initialise_can('can1')
    # Send OX vent initialisation
    #can_id = can_id_map['SEND_INIT_OXVENT']
    #can_data = [OX_VENT_UPPER_BOUND, OX_VENT_LOWER_BOUND, OX_VENT_OPEN_PERCENTAGE,0,0,0,0,0]
    #send_can_message(can1, can_id, can_data)
    #can_id = can_id_map['SEND_INIT_ENGINE_IGNITION']
    #igniter_start_delay_int = int(IGNITER_START_DELAY * 100)
    #ox_fill_set_open_percentage_8bit = int(OX_FILL_SET_OPEN_PERCENTAGE) & 0xFF
    #ox_fill_valve_open_angle_8bit = int(OX_FILL_VALVE_OPEN_ANGLE) & 0xFF
    #chamber_max_pressure_time_limit_int = int(CHAMBER_MAX_PRESSURE_TIME_LIMIT * 100)
    #can_data = struct.pack('>HBBH', 
    #                       igniter_start_delay_int, 
    #                       ox_fill_set_open_percentage_8bit, 
    #                       ox_fill_valve_open_angle_8bit, 
    #                       chamber_max_pressure_time_limit_int)
    #send_can_message(can1, can_id, can_data)

    # GPIOs
    fire_igniter_gpio_pin = 11
    pwm1_gpio_pin = 32
    pwm2_gpio_pin = 33
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(fire_igniter_gpio_pin, GPIO.OUT)
    GPIO.output(fire_igniter_gpio_pin, GPIO.LOW)
    GPIO.setup(pwm1_gpio_pin, GPIO.OUT)
    servo1 = GPIO.PWM(pwm1_gpio_pin, 50)
    servo1.start(0)
    servo1.ChangeDutyCycle(duty_cycle_from_angle(180))
    GPIO.setup(pwm2_gpio_pin, GPIO.OUT)
    servo2 = GPIO.PWM(pwm2_gpio_pin, 50)
    servo2.start(0)
    servo2.ChangeDutyCycle(duty_cycle_from_angle(180))

    # MQTT
    broker = GROUND_STATION_HOST_IP
    print(broker)
    port = MQTT_BROKER_PORT
    client_id = 'publish-fuellingpi1'
    client_mqtt = connect_mqtt(client_id, broker, port)

    # Influx
    influx_url = f"http://{GROUND_STATION_HOST_IP}:8086"
    client, write_api, query_api = connect_influxdb(influx_url, "hypower", "hypower")
    write_to_influx(write_api, "hypower", "fuelling_sequence", "measurement", 'stage', '0') #this will be commented out so stage doesnt start at 0 every time

    # Variables
    states = {'permission_control_fuelling': True, 'is_firing_auth': False}
    
    print('Init is fine')

except Exception as e:
    print(f'HTTP server initialisation failed because: {e}')
    raise

# Fast API
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow the listed methods
    allow_headers=["*"],  # Allow all headers
)

class Item(BaseModel):
    state_request_value: float

class SequenceOption(BaseModel):
    option: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

prev_prev_actuator_states = [0,0,0,0,0,0,0,0,0]
prev_actuator_states = [0,0,0,0,0,0,0,0,0]
actuator_can_ids = [
    can_id_map['OX_PRESSURE_ID'],
    can_id_map['OX_VENT_ID'],
    can_id_map['ETH_VENT_ID'],
    can_id_map['OX_OUT_ID'],
    can_id_map['ETH_OUT_ID'],
    can_id_map['GS_OX_IN_ID'],
    can_id_map['GS_N2_IN_ID'],
    can_id_map['GS_N2_VENT_ID'],
    can_id_map['GS_OX_VENT_ID'],
]

def handle_timeout_servo_command_receipt(can_id: str, communication_identifier: str):
    data_bytes = bytes.fromhex(communication_identifier)
    can_data = bytearray(data_bytes)
    actuator_id = can_data[0]
    can_id = actuator_can_ids[actuator_id-1]
    send_repeated_CAN(can_bus, can_id, can_data)

def handle_completion_servo_command_receipt(can_id: str, communication_identifier: str):
    data_bytes = bytes.fromhex(communication_identifier)
    can_data = bytearray(data_bytes)
    actuator_id = can_data[0]
    if can_data[0] == can_data[2] and can_data[1] == can_data[3]:
        send_can_message(can1, actuator_can_ids[actuator_id-1], [can_data[0],can_data[1],can_data[2],can_data[3],1,0,0,0])
    print(f"Handling completion for servo communication_identifier: {can_data}")
    # publish_mqtt(client_mqtt, 'heartbeat/rocket_to_fuelling_station', '100')

# Assuming the variables 'states', 'actuator_can_ids', 'prev_actuator_states', 
# 'prev_prev_actuator_states', 'send_can_message', 'can1', and 'FUELLING_STATION_PI_IP', 
# 'FUELLING_STATION_PI_HTTP_PORT' are defined elsewhere.

@app.post("/change_state_actuator")
async def process_data(request: Request, item: Item):
    try:
        # Checking permission to control fuelling
        if states['permission_control_fuelling']:
            headers = request.headers
            headers_dict = dict(headers)
            actuator_id = int(headers_dict['actuator_id'])
            data = int(item.state_request_value)
            print(f"Actuator ID: {actuator_id}, Data: {data}")
            
            # Updating actuator states
            prev_actuator_states[actuator_id - 1] = data

            try:
                # Prepare CAN data
                # can_data = [actuator_id - 1, data, 0, 0, 0, 0, 0, 0]
                if actuator_id-1 == 5:
                    can_data = [0, data, 0, data, 1, 0, 0, 0]
                elif actuator_id - 1 == 6:
                    can_data = [1, data, 1, data, 1, 0, 0, 0]
                elif actuator_id - 1 == 7:
                    can_data = [2, data, 2, data, 1, 0, 0, 0]
                elif actuator_id - 1 == 8:
                    can_data = [3, data, 3, data, 1, 0, 0, 0]
                else:
                    can_data = [actuator_id - 1, data, actuator_id - 1, data, 1, 0, 0, 0]


                can_data_hex = bytearray(can_data).hex()  # Convert CAN data to hex
                can_id = int(actuator_can_ids[actuator_id - 1], 16)  # Get CAN ID
                print('can_id: ', can_id, 'can_data: ', can_data)
                send_can_message(can1, can_id, can_data)  # Send CAN message

                # Prepare data for the POST request
                data_payload = {'status': 'pending', 'can_id': str(can_id), 'data_field': can_data_hex}
                url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/servo_command_receipt'
                print(f"Sending to URL: {url}")

                # Send asynchronous POST request using httpx
                # async with httpx.AsyncClient() as client:
                #     response = await client.post(url, json=data_payload)
                #     print(f"Response status: {response.status_code}")
                #     print(f"Response content: {response.json()}")
                # prev_prev_actuator_states = prev_actuator_states
                # print('here')
                
                # return {"message": "Data received", "response": response.json()}
                return {"message: Data received"}
            except:
                print('Failed on actuating')

            # except httpx.RequestError as e:
            #     print(f"Error while sending command receipt to {url}: {e}")
            #     raise HTTPException(status_code=500, detail="Error sending command receipt")

        else:
            raise HTTPException(status_code=403, detail="Not allowed: Rocket has control")
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/change_state_actuator_eth_ox_simultaneously")
async def process_data(request: Request, item: Item):
    try:
        # Checking permission to control fuelling
        if states['permission_control_fuelling']:
            data = int(item.state_request_value)
            try:
                can_id = can_id_map['OX_AND_ETH_SIMULTANEOUSLY_ID']
                can_id = int(can_id, 16)
                can_data = [data,0,0,0,0,0,0,0]
                print('can_id: ', can_id, 'can_data: ', can_data)
                send_can_message(can1, can_id, can_data)  # Send CAN message

                # Prepare data for the POST request
                # can_data_hex = bytearray(can_data).hex()  # Convert CAN data to hex
                # data_payload = {'status': 'pending', 'can_id': str(can_id), 'data_field': can_data_hex}
                # url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/servo_command_receipt'
                # print(f"Sending to URL: {url}")

                # Send asynchronous POST request using httpx
                # async with httpx.AsyncClient() as client:
                #     response = await client.post(url, json=data_payload)
                #     print(f"Response status: {response.status_code}")
                #     print(f"Response content: {response.json()}")
                # prev_prev_actuator_states = prev_actuator_states
                # print('here')
                # return {"message": "Data received", "response": response.json()}
                return {"message: Data received"}
            except:
                print('Failed on actuating')

            # except httpx.RequestError as e:
            #     print(f"Error while sending command receipt to {url}: {e}")
            #     raise HTTPException(status_code=500, detail="Error sending command receipt")
        else:
            raise HTTPException(status_code=403, detail="Not allowed: Rocket has control")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/undo_actuator_state")
async def process_data(item: SequenceOption):
    try:
        if states['permission_control_fuelling']:
            can_id = can_id_map['UPDATE_ALL_SERVOS']
            temp = prev_actuator_states
            prev_actuator_states = prev_prev_actuator_states
            prev_prev_actuator_states = temp
            send_can_message(can1, can_id, prev_actuator_states)
            data = {'status': 'pending', 'can_id': can_id, 'data_field': prev_actuator_states.hex()}
            url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/servo_command_receipt'
            #response = requests.post(url, json=data)
            return {"message": "Data received", "q": data}
        else:
            raise HTTPException(status_code=403, detail="Not allowed: Rocket has control") 
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

class SendStartupValvePositions(BaseModel):
    oxidiser_setpoint: int
    pressure_setpoint: int
    delay: float
@app.post("/send_startup_valve_positions")
async def process_data(data: SendStartupValvePositions):
    try:
        oxidiser_setpoint = data.oxidiser_setpoint
        pressure_setpoint = data.pressure_setpoint
        delay = data.delay

        return {"message": "Data received", "q": data}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


class CodeVerify(BaseModel):
    code: int
@app.post("/handoff_fuelling_control")
async def process_data(data: CodeVerify):
    try:
        if data.code != 1:
            raise HTTPException(status_code=401, detail="Wrong code to handoff control")        
        states['permission_control_fuelling'] = False
        
        can_id = can_id_map['SEND_HANDOFF_CONTROL']
        can_id = int(can_id, 16)
        send_can_message(can1, can_id, [0,0,0,0,0,0,0,0])
        states['is_firing_auth'] = True
        return {"message": "Handoff succesful", "code": data.code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/retake_fuelling_control")
async def process_data(data: CodeVerify):
    try:
        if data.code == 1:
            can_id = can_id_map['SEND_RETAKE_CONTROL']
            can_id = int(can_id, 16)
            send_can_message(can1, can_id, [0,0,0,0,0,0,0,0])
            states['is_firing_auth'] = False
  
        else:
            raise HTTPException(status_code=401, detail="Wrong code to handoff control")  
        
        return {"message": "Handoff succesful", "code": data.code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

# fix this
@app.post("/fuelling_sequence")
async def process_data(data: SequenceOption):
    try:
        current_stage_index = read_from_influx(query_api, "fuelling_sequence", "measurement", "stage")
        current_stage_index = int(current_stage_index)
        if data.option == 'Next_Stage':
            current_stage_index = current_stage_index + 1 if current_stage_index + 1 < len(stages_keys) else current_stage_index 
            print("put next command here")

        elif data.option == 'Prev_Stage':
            current_stage_index = current_stage_index - 1 if current_stage_index - 1 >= 0 else current_stage_index 
            print("prev")
        
        current_stage = stages_keys[current_stage_index]
        prev_actuator_states = fuelling_stages[current_stage]
        send_can_message(can1, 0x104, prev_actuator_states[0:3])
        send_can_message(can1, 0x120, prev_actuator_states[3:5])
        send_can_message(can1, 0x105, prev_actuator_states[5:9])
        write_to_influx(write_api, "hypower", "fuelling_sequence", "measurement", 'stage', str(current_stage_index))
        publish_mqtt(client_mqtt, 'fuelling_sequence/stage', str(current_stage_index))
        return {"message": "Fuelling auto-sequence okay", "stage": str(current_stage_index)}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.get("/fuelling_sequence")
async def process_data():
    try:
        current_stage_index = read_from_influx(query_api, "fuelling_sequence", "measurement", "stage")
        current_stage_index = int(current_stage_index)
        current_stage = stages_keys[current_stage_index]
        publish_mqtt(client_mqtt, 'fuelling_sequence/stage', str(current_stage))
        return {"message": "Sent Stage over MQTT", "stage": str(current_stage)}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


    
def handle_emergency_stop(can_bus):
    cl = 180
    op = 1
    print('entered message')
    can_id = can_id_map['OX_OUT_ID']
    print(can_id)
    can_id = int(can_id, 16)
    print(can_id)
    can_data = [3, cl, 3, cl, 1, 0, 0, 0]
    print(can_data)
    send_can_message(can1, can_id, can_data)  # Send CAN message
    print('entered message')
    can_id = can_id_map['ETH_OUT_ID']
    can_id = int(can_id, 16)
    can_data = [4, cl, 4, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['OX_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [1, op, 1, op, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['ETH_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [2, cl, 2, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['OX_PRESSURE_ID']
    can_id = int(can_id, 16)
    print('here',can_id)
    can_data = [0, op, 0, op, 1, 0, 0, 0]
    print('here',can_data)
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_N2_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [2, op, 2, op, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_OX_VENT_ID']
    can_id = int(can_id, 16)
    can_data = [3, op, 3, op, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_N2_IN_ID']
    can_id = int(can_id, 16)
    can_data = [1, cl, 1, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
    can_id = can_id_map['GS_OX_IN_ID']
    can_id = int(can_id, 16)
    can_data = [0, cl, 0, cl, 1, 0, 0, 0]
    send_can_message(can1, can_id, can_data)  # Send CAN message
   

@app.post("/emergency_stop_pass")
async def process_data(data: CodeVerify):
    try:
        print(data.code)
        if data.code != 1:
            raise HTTPException(status_code=401, detail="Wrong code to deploy emergency stop")
        can_id = can_id_map['SEND_EMERGENCY_STOP']
        can_id = int(can_id, 16)
        can_data = [0,0,0,0,0,0,0,0]
        #send_can_message(can1, can_id, can_data)  # Send CAN message
        print('before func')
        handle_emergency_stop(can1)
        print('after')
        
        # can_data_hex = bytearray(can_data).hex()
        # data_payload = {'status': 'pending', 'can_id': str(can_id), 'data_field': can_data_hex}
        # url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
        # print(f"Sending to URL: {url}")
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, json=data_payload)
        #     print(f"Response status: {response.status_code}")
        #     print(f"Response content: {response.json()}")
        #prev_prev_actuator_states = prev_actuator_states
        return {"message": "Emergency stop deployed", "code": data.code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/emergency_stop_free")
async def process_data(data: CodeVerify):
    try:
        print('here', states['is_firing_auth'])
        if states['is_firing_auth'] == False:
            print('Fire ignitor not')
            raise HTTPException(status_code=401, detail="Firing sequence not enabled")
            
        can_id = can_id_map['SEND_EMERGENCY_STOP']
        can_id = int(can_id, 16)
        can_data = [0,0,0,0,0,0,0,0]
        #send_can_message(can1, can_id, can_data)  # Send CAN message
        handle_emergency_stop(can1)
        # can_data_hex = bytearray(can_data).hex()
        # data_payload = {'status': 'pending', 'can_id': str(can_id), 'data_field': can_data_hex}
        # url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
        # print(f"Sending to URL: {url}")
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, json=data_payload)
        #     print(f"Response status: {response.status_code}")
        #     print(f"Response content: {response.json()}")
        prev_prev_actuator_states = prev_actuator_states
        print('here')
        return {"message": "Emergency stop deployed", "code": data.code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@app.post("/fire_igniter")
async def process_data(data: CodeVerify):
    try:
        if data.code != 1:
            raise HTTPException(status_code=401, detail="Wrong code to handoff control")    
        can_id = can_id_map['SEND_FIRE_IGNITER']
        can_id = int(can_id, 16)
        can_data = [0,0,0,0,0,0,0,0]
        send_can_message(can1, can_id, can_data)
        # can_data_hex = bytearray(can_data).hex()
        # data_payload = {'status': 'pending', 'can_id': str(can_id), 'data_field': can_data_hex}
        # url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
        # print(f"Sending to URL: {url}")
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, json=data_payload)
        #     print(f"Response status: {response.status_code}")
        #     print(f"Response content: {response.json()}")
        states['is_firing_auth'] = True
        
        GPIO.output(fire_igniter_gpio_pin, GPIO.HIGH)
        time.sleep(0.5)
        can_id = can_id_map['OX_OUT_ID']
        can_id = int(can_id, 16)
        can_data = [3, 135, 3, 135, 1, 0, 0, 0]
        send_can_message(can1, can_id, can_data)  # Send CAN message
        can_id = can_id_map['ETH_OUT_ID']
        can_id = int(can_id, 16)
        can_data = [4, 135, 4, 135, 1, 0, 0, 0]
        send_can_message(can1, can_id, can_data)  # Send CAN message
        time.sleep(3)
        can_id = can_id_map['OX_OUT_ID']
        can_id = int(can_id, 16)
        can_data = [3, 54, 3, 54, 1, 0, 0, 0]
        send_can_message(can1, can_id, can_data)  # Send CAN message
        can_id = can_id_map['ETH_OUT_ID']
        can_id = int(can_id, 16)
        can_data = [4, 54, 4, 54, 1, 0, 0, 0]
        send_can_message(can1, can_id, can_data)  # Send CAN message
        
        time.sleep(3)
        GPIO.output(fire_igniter_gpio_pin, GPIO.LOW)

        print('gpio')
        return {"message": "Igniter firing succesful", "code": data.code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

class Burst(BaseModel):
    code: float
@app.post("/burst_ox_vent")
async def process_data(data: Burst):
    try:
        print('burst_ox_vent')
        print(data.code)
        can_id = can_id_map['OX_VENT_ID']
        can_id = int(can_id, 16)
        can_data = [1,1,1,1,1,0,0,0]
        send_can_message(can1, can_id, can_data)
        time.sleep(data.code)
        can_data = [1,180,1,180,1,0,0,0]
        send_can_message(can1, can_id, can_data)
        
        return {"message": "Igniter firing succesful", "code": data.code}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

# def firing1(can_bus):
#     time.sleep(1)
#     can_id = can_id_map['OX_OUT_ID']
#     can_id = int(can_id, 16)
#     can_data = [3, 144, 3, 144, 1, 0, 0, 0]
#     send_can_message(can1, can_id, can_data)  # Send CAN message
#     can_id = can_id_map['ETH_OUT_ID']
#     can_id = int(can_id, 16)
#     can_data = [4, 144, 4, 144, 1, 0, 0, 0]
#     send_can_message(can1, can_id, can_data)  # Send CAN message
        
# def firing2(can_bus):
#     time.sleep(1)
#     can_id = can_id_map['OX_OUT_ID']
#     can_id = int(can_id, 16)
#     can_data = [3, 108, 3, 108, 1, 0, 0, 0]
#     send_can_message(can1, can_id, can_data)  # Send CAN message
#     can_id = can_id_map['ETH_OUT_ID']
#     can_id = int(can_id, 16)
#     can_data = [4, 108, 4, 108, 1, 0, 0, 0]
#     send_can_message(can1, can_id, can_data)  # Send CAN message
        
# def firing3(fire_igniter_gpio_pin):
#     time.sleep(3)
#     GPIO.output(fire_igniter_gpio_pin, GPIO.LOW)

# async def firing_all(can_bus, fire_igniter_gpio_pin):
#     firing1(can_bus)
#     firing2(can_bus)
#     firing3(fire_igniter_gpio_pin)

# @app.post("/fire_igniter")
# async def process_data(data: CodeVerify):
#     try:
#         if data.code != 1:
#             raise HTTPException(status_code=401, detail="Wrong code to handoff control")    
#         can_id = can_id_map['SEND_FIRE_IGNITER']
#         can_id = int(can_id, 16)
#         can_data = [0,0,0,0,0,0,0,0]
#         send_can_message(can1, can_id, can_data)
#         # can_data_hex = bytearray(can_data).hex()
#         # data_payload = {'status': 'pending', 'can_id': str(can_id), 'data_field': can_data_hex}
#         # url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
#         # print(f"Sending to URL: {url}")
#         # async with httpx.AsyncClient() as client:
#         #     response = await client.post(url, json=data_payload)
#         #     print(f"Response status: {response.status_code}")
#         #     print(f"Response content: {response.json()}")
#         states['is_firing_auth'] = True
        
#         GPIO.output(fire_igniter_gpio_pin, GPIO.HIGH)

#         await firing_all(can1, fire_igniter_gpio_pin)

#         print('gpio')
#         return {"message": "Igniter firing succesful", "code": data.code}

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


class PIDGains(BaseModel):
    kp: float
    ki: float
@app.post("/set_chamber_pressure_gains")
async def process_data(data: PIDGains):
    try:
        kp = data.kp
        ki = data.ki
        packed_data = struct.pack('ff', kp, ki)
        send_can_message(can1, can_id_map['SEND_CHAMBER_PRESSURE_GAINS'], packed_data)
        data = {'status': 'pending', 'can_id': can_id_map['SEND_CHAMBER_PRESSURE_GAINS'], 'data_field': packed_data.hex()}
        url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
        response = requests.post(url, json=data)
        return {"message": "PI gains post successful"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/set_oxidiser_pressure_gains")
async def process_data(data: PIDGains):
    try:
        kp = data.kp
        ki = data.ki
        packed_data = struct.pack('ff', kp, ki)
        send_can_message(can1, can_id_map['SEND_OXIDISER_PRESSURE_GAINS'], packed_data)
        data = {'status': 'pending', 'can_id': can_id_map['SEND_OXIDISER_PRESSURE_GAINS'], 'data_field': packed_data.hex()}
        url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
        response = requests.post(url, json=data)
        return {"message": "PI gains post successful"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

class ControlSetpoints(BaseModel):
    ox_ref: float
    pr_ref: float
@app.post("/upload_control_setpoints")
async def process_data(data: ControlSetpoints):
    try:
        ox_ref = data.ox_ref
        pr_ref = data.pr_ref
        packed_data = struct.pack('ff', ox_ref, pr_ref)
        send_can_message(can1, can_id_map['SEND_CHAMBER_OXIDISER_SETPOINTS'], packed_data)
        data = {'status': 'pending', 'can_id': can_id_map['SEND_CHAMBER_OXIDISER_SETPOINTS'], 'data_field': packed_data.hex()}
        url = f'http://{FUELLING_STATION_PI_IP}:{FUELLING_STATION_PI_HTTP_PORT}/general_command_receipt'
        response = requests.post(url, json=data)
        return {"message": "PI gains post successful"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/set_logging")
async def process_data(data: Item):
    try:
        logging_state = data.state_request_value
        if logging_state == 2:
            #start logging here
            print('Start logging')
        else:
            #stop logging here
            print('Stop logging')
        return {"message": "PI gains post successful"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

class HeartbeatData(BaseModel):
    status: str
    timestamp: float
@app.post("/fuelling_station_to_rocket_heartbeat")
async def process_data(data: HeartbeatData, background_tasks: BackgroundTasks):
    try:
        status = data.status
        timestamp = data.timestamp
        if status == "pending":
            if timestamp in pending_requests:
                raise HTTPException(status_code=400, detail="Pending status already exists for this timestamp")
            
            send_can_message(can1, can_id_map['SEND_HB_FUELLING_TO_ROCKET'], double_to_can_msg(timestamp))
            print('CAN sent')
            timer = asyncio.get_event_loop().call_later(HEARTBEAT_INTERVAL, lambda: asyncio.ensure_future(check_timeout(can_bus, can_id, timestamp, handle_timeout_heartbeat, HEARTBEAT_INTERVAL)))
            pending_requests[timestamp] = timer
            return {"message": "Pending status received, timer started"}

        elif status == "completed":
            if timestamp not in pending_requests:
                raise HTTPException(status_code=400, detail="No pending request found for this timestamp")
            
            timer = pending_requests.pop(timestamp)
            timer.cancel()
            handle_completion(timestamp)
            return {"message": "Completed status received, timer canceled"}

        else:
            raise HTTPException(status_code=400, detail="Invalid status value")

    except Exception as e:
        return {"status": "Failed to send message", "error": str(e)}

class CommandReceipt(BaseModel):
    status: str
    can_id: str
    data_field: str
@app.post("/general_command_receipt")
async def process_data(data: CommandReceipt, background_tasks: BackgroundTasks):
    try:
        status = data.status
        communication_identifier = data.data_field
        can_id = data.can_id
        if status == "pending":
            if communication_identifier in pending_requests:
                raise HTTPException(status_code=400, detail="Pending status already exists for this timestamp")
            timer = asyncio.get_event_loop().call_later(COMMAND_TIMEOUT_INTERVAL, lambda: asyncio.ensure_future(check_timeout(can_bus, can_id, communication_identifier, handle_timeout_general_command_receipt,COMMAND_TIMEOUT_INTERVAL)))
            pending_requests[communication_identifier] = timer
            return {"message": "Pending status received, timer started"}

        elif status == "completed":
            if communication_identifier not in pending_requests:
                raise HTTPException(status_code=400, detail="No pending request found for this timestamp")
            
            # Cancel the timeout if it was set
            timer = pending_requests.pop(communication_identifier)
            timer.cancel()
            # Call the completion handler
            handle_completion_general_command_receipt(can_bus, can_id, communication_identifier)
            return {"message": "Completed status received, timer canceled"}

        else:
            raise HTTPException(status_code=400, detail="Invalid status value")

    except Exception as e:
        return {"status": "Failed to send message", "error": str(e)}

@app.post("/servo_command_receipt")
async def process_data(data: CommandReceipt, background_tasks: BackgroundTasks):
    try:
        print('hit')
        status = data.status
        communication_identifier = data.data_field
        can_id = data.can_id
        if status == "pending":
            if communication_identifier in pending_requests:
                raise HTTPException(status_code=400, detail="Pending status already exists for this timestamp")
            timer = asyncio.get_event_loop().call_later(COMMAND_TIMEOUT_INTERVAL, lambda: asyncio.ensure_future(check_timeout(can_bus, can_id, communication_identifier, handle_timeout_servo_command_receipt, COMMAND_TIMEOUT_INTERVAL)))
            pending_requests[communication_identifier] = timer
            return {"message": "Pending status received, timer started"}

        elif status == "completed":
            if communication_identifier not in pending_requests:
                raise HTTPException(status_code=400, detail="No pending request found for this timestamp")
            
            # Cancel the timeout if it was set
            timer = pending_requests.pop(communication_identifier)
            timer.cancel()
            # Call the completion handler
            handle_completion_servo_command_receipt(can_id, communication_identifier)
            return {"message": "Completed status received, timer canceled"}

        else:
            raise HTTPException(status_code=400, detail="Invalid status value")
    except Exception as e:
        return {"status": "Failed to send message", "error": str(e)}

@app.post("/fire_igniter_command_receipt")
async def process_data(data: CommandReceipt, background_tasks: BackgroundTasks):
    try:
        status = data.status
        communication_identifier = data.data_field
        can_id = data.can_id
        if status == "pending":
            if communication_identifier in pending_requests:
                raise HTTPException(status_code=400, detail="Pending status already exists for this timestamp")
            timer = asyncio.get_event_loop().call_later(COMMAND_TIMEOUT_INTERVAL, lambda: asyncio.ensure_future(check_timeout(can_bus, can_id, communication_identifier, handle_timeout_fire_igniter_command_receipt,COMMAND_TIMEOUT_INTERVAL)))
            pending_requests[communication_identifier] = timer
            return {"message": "Pending status received, timer started"}

        elif status == "completed":
            if communication_identifier not in pending_requests:
                raise HTTPException(status_code=400, detail="No pending request found for this timestamp")
            
            # Cancel the timeout if it was set
            timer = pending_requests.pop(communication_identifier)
            timer.cancel()
            # Call the completion handler
            handle_completion_fire_igniter_command_receipt(can_bus, can_id, communication_identifier)
            return {"message": "Completed status received, timer canceled"}

        else:
            raise HTTPException(status_code=400, detail="Invalid status value")

    except Exception as e:
        return {"status": "Failed to send message", "error": str(e)}


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=FUELLING_STATION_PI_HTTP_PORT)
    except Exception as e:
        print(e)
    finally:
        close_can(can1)
        close_GPIO()
