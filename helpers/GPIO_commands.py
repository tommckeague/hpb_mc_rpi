import RPi.GPIO as GPIO
import time

def initialise_GPIO(PIN):
    # Set the GPIO mode
    GPIO.setmode(GPIO.BCM)
    # Set up the pin as an output
    GPIO.setup(PIN, GPIO.OUT)

def close_GPIO():
    GPIO.cleanup()

def duty_cycle_from_angle(angle):
    return ((angle / 180) * (12-2)) + 2 # this is saying 2 duty cycle is 0 deg and 12 duty cycle is 180 deg
