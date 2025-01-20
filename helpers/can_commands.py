import os
import can
import struct
import time
import math

def initialise_can(can_channel, filters=[]):
    # Set up the CAN interface
    os.system(f'sudo ip link set {can_channel} type can bitrate 500000')
    os.system(f'sudo ifconfig {can_channel} up')
    if filters:
        _can = can.interface.Bus(channel=can_channel, interface='socketcan', can_filters=filters)
    else:
        _can = can.interface.Bus(channel=can_channel, interface='socketcan')
    print(f'{can_channel} is up')
    return _can


def send_can_message(can_channel, arbitration_id, data):
    msg = can.Message(is_extended_id=False, arbitration_id=arbitration_id, data=data)
    can_channel.send(msg)

def receive_can_message(can_channel):
    msg = can_channel.recv(1)
    if msg is not None:
        return msg

def close_can(can_channel):
    # Shut down the CAN interface
    can_channel_str = str(can_channel).split(' ')[2].replace("'", '')
    os.system(f'sudo ifconfig {can_channel_str} down')
    # Ensure the CAN bus is properly shut down
    can_channel.shutdown()
    print(f'Closed CAN bus: {can_channel}')

def can_msg_to_double(data):
    return struct.unpack('d', data)[0]

def double_to_can_msg(data):
    return struct.pack('d',data)

def can_msg_to_uint8(data):
    return list(data)

def uint8_to_can_msg(data):
    return bytearray(data)

def can_msg_to_str(data):
    return data.decode('utf-8')

def str_to_can_msg(data):
    return bytearray(data, 'utf-8')