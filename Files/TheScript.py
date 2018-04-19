import os
import RPi.GPIO as GPIO                    # Import GPIO library
import time
import httplib
import urllib                      # Import time library
from time import sleep

# PINS
pinLampOPEN = 23
pinLampCLOSED = 24
pinWaterSensorIN = 18
pinSonicSensorTrigger = 17
pinSonicSensorEcho = 27

class PushoverSender:
    def __init__(self, user_key, api_key):
        self.user_key = user_key
        self.api_key = api_key

    def send_notification(self, text):
        conn = httplib.HTTPSConnection('api.pushover.net')
        post_data = {'user': self.user_key, 'token': self.api_key, 'message': text}
        conn.request("POST", "/1/messages.json",
                     urllib.urlencode(post_data), {"Content-type": "application/x-www-form-urlencoded"})
        # print(conn.getresponse().read())

GPIO.setmode(GPIO.BCM)                     # Set GPIO pin numbering
GPIO.setup(pinLampOPEN,GPIO.OUT)
GPIO.setup(pinLampCLOSED,GPIO.OUT)
GPIO.setup(pinWaterSensorIN, GPIO.IN)
GPIO.setup(pinSonicSensorTrigger,GPIO.OUT)
GPIO.setup(pinSonicSensorEcho,GPIO.IN)

OPEN = False
FULL = False
lastOPEN = OPEN
refreshDelay = 1                           # Refresh information every x seconds
fullDistance = 10
pushover_sender = PushoverSender('u36t8bwat888xbt46knczszgzaxadi', 'acq8xyqco6gweobkqpiqwf9gm2mqzo')
message = ""
sendMessage = True


def isRaining():
    if (GPIO.input(pinWaterSensorIN) == 0):
        return True
    else:
        return False

def isFull(full):
    halfFull = 17
    halfFullSent = False
    almostFull = 19
    almostFullSent = False
    GPIO.output(pinSonicSensorTrigger, False)# Set TRIG as LOW
    time.sleep(2)                            # Delay of 2 seconds

    GPIO.output(pinSonicSensorTrigger, True) # Set TRIG as HIGH
    time.sleep(0.00001)                      # Delay of 0.00001 seconds
    GPIO.output(pinSonicSensorTrigger, False)# Set TRIG as LOW

    while GPIO.input(pinSonicSensorEcho)==0:# Check whether the ECHO is LOW
        pulse_start = time.time()               # Saves the last known time of LOW pulse

    while GPIO.input(pinSonicSensorEcho)==1:# Check whether the ECHO is HIGH
        pulse_end = time.time()                 # Saves the last known time of HIGH pulse

    pulse_duration = pulse_end - pulse_start# Get pulse duration to a variable

    distance = pulse_duration * 17150       # Multiply pulse duration by 17150 to get distance
    distance = round(distance, 2)           # Round to two decimal points

    if (halfFullSent == False and distance > halfFull):
        halfFull -= 2
        sendInfo('Your water storage is half-full!')
        halfFullSent = True

    if (almostFullSent == False and distance > almostFull):
        almostFull -= 2
        sendInfo('Your water storage is almost full!')
        halfFullSent = True

    if (halfFullSent == True and distance < halfFull):
        halfFull += 2
        sendInfo('Your water supplies ar running low!')
        halfFullSent = False

    if (almostFullSent == True and distance < almostFull):
        almostFull += 2
        halfFullSent = False

    # print distance
    if (full == False and distance < 13 ):
        full = True
    if (full == True and distance > 15):
        full = False
    return full

def turnOnCLOSEDLight():
    GPIO.output(pinLampOPEN,GPIO.LOW)       # turning off OPEN light
    GPIO.output(pinLampCLOSED,GPIO.HIGH)    # turning on CLOSED light
    print "CLOSED LIGHT"

def turnOnOPENLight():
    GPIO.output(pinLampCLOSED,GPIO.LOW)     # turning off CLOSED light
    GPIO.output(pinLampOPEN,GPIO.HIGH)      # turning on OPEN light
    print "OPEN LIGHT"

def sendInfo(msg):
    pushover_sender.send_notification(msg)

turnOnCLOSEDLight()
sendInfo('Water collection system booted successfully. Lids are currently closed.')
while True:
    if (isRaining()):                      # check if its raining
        FULL = isFull(FULL)
        if (FULL):                     # check if full
            if(OPEN):
                OPEN = False               # if full AND open >> CLOSE
                message = 'Your water storage is full! Lids are closing..'
                sendMessage = True
        else:
            if(OPEN != True):
                OPEN = True                # if NOT full and CLOSED >> OPEN
                message = 'It started raining! Lids are opening..'
                sendMessage = True
    elif (OPEN):                           # if not raining, and OPEN >> CLOSE
        OPEN = False
        message = 'It stopped raining! Lids are closing..'
        sendMessage = True

    if (OPEN != lastOPEN):
        lastOPEN = OPEN
        if (OPEN):
            turnOnOPENLight()
        else:
            turnOnCLOSEDLight()

    if (sendMessage):
        sendInfo(message)
        sendMessage = False
        message = ''

    time.sleep(refreshDelay)                # Delay of "refreshDelay" seconds
