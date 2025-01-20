import subprocess
import logging
import time

def run_script(script_name):
    try:
        logging.info(f"Starting {script_name}...")
        # Using Popen to run scripts in parallel
        process = subprocess.Popen(["python3", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return process
    except Exception as e:
        logging.error(f"Failed to start {script_name}: {e}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    scripts = ["http_server.py", "receive_can.py", "node_control.py"]

    # List to hold processes
    processes = []

    # Start all scripts with a 1-second delay in between
    for script in scripts:
        process = run_script(script)
        if process:
            processes.append((script, process))
        time.sleep(1)  # Add a 1-second delay between starting each script

    # Monitor the processes
    for script, process in processes:
        stdout, stderr = process.communicate()  # This will wait for the process to finish
        logging.info(f"{script} finished with output:\n{stdout}")
        if stderr:
            logging.error(f"{script} encountered an error:\n{stderr}")
