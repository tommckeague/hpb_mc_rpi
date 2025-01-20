import RPi.GPIO as GPIO
import time

#GPIO.setmode(GPIO.BCM)
#gpio_pin = 17
#gpio_pin = 32
#GPIO.setup(gpio_pin, GPIO.OUT)
#
#try:
#
#	while True:
#		print('Here')
#		GPIO.output(gpio_pin, GPIO.LOW)
#		time.sleep(1)
#
#finally:
#	GPIO.cleanup()
	
	
import RPi.GPIO as GPIO
import time

# Set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

def servoMover(servoPIN):
    GPIO.setup(servoPIN, GPIO.OUT)
    servo = GPIO.PWM(servoPIN, 50)
    servo.start(0)
    servo.ChangeDutyCycle(12)
    time.sleep(0.3)

servoMover(32)
