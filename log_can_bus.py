import can
import subprocess
from datetime import datetime, timedelta
import threading
import os
from helpers.can_commands import initialise_can, close_can

# Constants
LOG_FILE_PATH_TEMPLATE = 'can_logging/{can_id}/can_log_{timestamp}.txt'
LOG_FILE_DURATION = timedelta(minutes=10)  # Duration for each log file

# Global variables to keep track of file rotation
log_file_lock = threading.Lock()
last_log_file_time = {}
    
def get_log_file_path(can_id):
    """Returns the path of the current log file based on the CAN ID and current time."""
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
    """Initializes the CAN interface."""
    try:
        result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
        if 'UP' not in result.stdout:
            print(f'{interface} needs to be up before logging.')
            can0 = initialise_can('can0')
            raise
        return can.interface.Bus(channel=interface, interface='socketcan')
    except Exception as e:
        print(f'Error initializing CAN interface: {e}')
        raise

def log_can_message(msg):
    """Logs detailed CAN messages to a file with a timestamp."""
    can_id = hex(msg.arbitration_id)  # Use CAN ID in hexadecimal as the folder name
    with log_file_lock:
        log_file_path = get_log_file_path(can_id)
        with open(log_file_path, 'a') as log_file:
            timestamp_str = datetime.utcnow().isoformat()
            # Extract details from CAN message
            channel = msg.channel
            timestamp = msg.timestamp
            message_id = msg.arbitration_id
            is_extended_id = msg.is_extended_id
            is_remote_frame = msg.is_remote_frame
            data = msg.data.hex()  # Convert data to hexadecimal string

            # Format the message
            log_entry = (
                f'{timestamp_str} - '
                f'Channel: {channel}, '
                f'Timestamp: {timestamp}, '
                f'ID: {message_id}, '
                f'Extended ID: {is_extended_id}, '
                f'Remote Frame: {is_remote_frame}, '
                f'Data: {data}\n'
            )
            log_file.write(log_entry)

def can_listener(bus):
    """Listens to a CAN bus and logs messages."""
    try:
        print(f'Listening on {bus.channel_info}')
        while True:
            try:
                msg = bus.recv(1)  # Receive CAN message with a 1-second timeout
                if msg is not None:
                    log_can_message(msg)  # Log the detailed message
                    print(msg)  # Optionally print the message to the console
            except Exception as e:
                print(f'Error receiving CAN message: {e}')
    except KeyboardInterrupt:
        print(f'Keyboard interrupt detected on {bus.channel_info}. Exiting...')
    finally:
        bus.shutdown()  # Close the CAN interface
        print(f'CAN interface {bus.channel_info} closed.')

def main():
    # Initialize CAN interfaces
    try:
        can0 = initialize_can_interface('can0')
        #can1 = initialize_can_interface('can1')
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



# import can
# import subprocess
# from datetime import datetime, timedelta
# import threading
# import os

# # Constants
# LOG_FILE_PATH_TEMPLATE = 'can_logging/can_log_{timestamp}.txt'
# LOG_FILE_DURATION = timedelta(minutes=10)  # Duration for each log file

# # Global variables to keep track of file rotation
# log_file_lock = threading.Lock()
# last_log_file_time = datetime.utcnow()

# def get_log_file_path():
#     """Returns the path of the current log file based on the current time."""
#     global last_log_file_time
#     current_time = datetime.utcnow()
    
#     # Rotate log file if 10 minutes have passed
#     if current_time - last_log_file_time >= LOG_FILE_DURATION:
#         last_log_file_time = current_time
#         timestamp = current_time.strftime('%d_%m_%y %H-%M')
#         return LOG_FILE_PATH_TEMPLATE.format(timestamp=timestamp)
    
#     # Return the current file path
#     return LOG_FILE_PATH_TEMPLATE.format(timestamp=last_log_file_time.strftime('%d_%m_%y %H-%M'))

# def initialize_can_interface(interface):
#     """Initializes the CAN interface."""
#     try:
#         result = subprocess.run(['ifconfig', interface], capture_output=True, text=True)
#         if 'UP' not in result.stdout:
#             print(f'{interface} needs to be up before logging.')
#             raise
#         return can.interface.Bus(channel=interface, interface='socketcan')
#     except Exception as e:
#         print(f'Error initializing CAN interface: {e}')
#         raise

# def log_can_message(msg):
#     """Logs detailed CAN messages to a file with a timestamp."""
#     with log_file_lock:
#         log_file_path = get_log_file_path()
#         with open(log_file_path, 'a') as log_file:
#             timestamp_str = datetime.utcnow().isoformat()
#             # Extract details from CAN message
#             channel = msg.channel
#             timestamp = msg.timestamp
#             message_id = msg.arbitration_id
#             is_extended_id = msg.is_extended_id
#             is_remote_frame = msg.is_remote_frame
#             data = msg.data.hex()  # Convert data to hexadecimal string

#             # Format the message
#             log_entry = (
#                 f'{timestamp_str} - '
#                 f'Channel: {channel}, '
#                 f'Timestamp: {timestamp}, '
#                 f'ID: {message_id}, '
#                 f'Extended ID: {is_extended_id}, '
#                 f'Remote Frame: {is_remote_frame}, '
#                 f'Data: {data}\n'
#             )
#             log_file.write(log_entry)

# def can_listener(bus):
#     """Listens to a CAN bus and logs messages."""
#     try:
#         print(f'Listening on {bus.channel_info}')
#         while True:
#             try:
#                 msg = bus.recv(1)  # Receive CAN message with a 1-second timeout
#                 if msg is not None:
#                     log_can_message(msg)  # Log the detailed message
#                     print(msg)  # Optionally print the message to the console
#             except Exception as e:
#                 print(f'Error receiving CAN message: {e}')
#     except KeyboardInterrupt:
#         print(f'Keyboard interrupt detected on {bus.channel_info}. Exiting...')
#     finally:
#         bus.shutdown()  # Close the CAN interface
#         print(f'CAN interface {bus.channel_info} closed.')

# def main():
#     # Initialize CAN interfaces
#     try:
#         can0 = initialize_can_interface('can0')
#         can1 = initialize_can_interface('can1')
#     except Exception as e:
#         print(f'Initialization failed: {e}')
#         return

#     print('CAN interfaces initialized. Logging started.')

#     # Create and start threads for each CAN interface
#     try:
#         can0_thread = threading.Thread(target=can_listener, args=(can0,))
#         can1_thread = threading.Thread(target=can_listener, args=(can1,))
        
#         can0_thread.start()
#         can1_thread.start()
        
#         # Wait for threads to finish
#         can0_thread.join()
#         can1_thread.join()
#     except KeyboardInterrupt:
#         print('Keyboard interrupt detected. Exiting...')

# if __name__ == '__main__':
#     main()
