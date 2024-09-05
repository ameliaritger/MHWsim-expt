import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)

try:
    while True:
        GPIO.output(21,True)  #turn on LED3
        time.sleep(1)
        GPIO.output(21,False) 
        GPIO.output(20,True) #turn on LED2
        time.sleep(1)
        GPIO.output(20,False) 
        GPIO.output(26,True) #turn on LED1
        time.sleep(1)
        GPIO.output(26,False)
        time.sleep(0.5)
    
finally:
    GPIO.cleanup()