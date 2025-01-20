import struct
import time
import random
from helpers.can_commands import initialise_can, send_can_message, close_can

can1 = initialise_can('can1')

try:
    # For sending a double
    # user_input_double = 65.9999
    # user_input_double = struct.pack('d',user_input_double)
    # # print(user_input_double)
    # send_can_message(can1, 1, user_input_double)

    # For sending a list of uint8 
    while True:
        time.sleep(1)
        num = random.randint(0,100)
        data_to_send = [num,0,0,0,0,0,0,0]
        data_to_send = bytearray(data_to_send)
        send_can_message(can1, 5, data_to_send)

    # For sending a string 
    # user_input_string = 'hello'
    # data_to_send = bytearray(user_input_string, 'utf-8')
    # data_to_send = [0x48, 0x20, 0x48]
        
finally:
    close_can(can1)