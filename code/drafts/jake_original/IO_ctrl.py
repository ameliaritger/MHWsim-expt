import RPi.GPIO as GPIO

heater_on = GPIO.HIGH
heater_off = GPIO.LOW
chiller_on = GPIO.HIGH
chiller_off = GPIO.LOW

class IO_CTRL(object):
    def __init__(self, control_pins, heater_pins, chiller_pins):
        self.control_pins = control_pins
        self.heater_pins = heater_pins
        self.chiller_pins = chiller_pins
        self.heater_states = [0] * len(heater_pins)
        self.status = []

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        #GPIO.setmode(GPIO.BOARD)
#         GPIO.setup(self.control_pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #setup the control pins as inputs with a pull down
        GPIO.setup(self.control_pins[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #setup the control pins as inputs with a pull down
        GPIO.setup(self.control_pins[1], GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #setup the control pins as inputs with a pull down
        GPIO.setup(self.control_pins[2], GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #setup the control pins as inputs with a pull down
        
        GPIO.setup(self.heater_pins, GPIO.OUT, initial=heater_off) #setup the heater pins as outputs and initalize them as low
        GPIO.setup(self.chiller_pins, GPIO.OUT, initial=chiller_off) #setup the chiller pins as outputs and initalize them as low

        GPIO.add_event_detect(self.control_pins[0], GPIO.RISING, callback=self.start,     bouncetime=500)
        GPIO.add_event_detect(self.control_pins[1], GPIO.RISING, callback=self.save_data, bouncetime=500)
        GPIO.add_event_detect(self.control_pins[2], GPIO.RISING, callback=self.stop,      bouncetime=500)

    def start(self, pin): #start button was pressed, set status to start
        self.status = "start"
        print("start")

    def save_data(self, pin): #save button was pressed, set status to save
        self.status = "save"
        print("save")

    def stop(self, pin): #stop button was pressed, set status to stop
        self.status = "stop"
        print("stop")

    def clear(self): #clear the status, probably don't need to do this but that's ok
        self.status = []

    def heat(self, tank_num, heater_state): #turn on associated heater
        if heater_state:
            GPIO.output(self.heater_pins[tank_num], heater_on)
        else:
            GPIO.output(self.heater_pins[tank_num], heater_off)
        self.heater_states[tank_num] = heater_state
        
        #GPIO.output(self.chiller_pins[tank_num], chiller_off)
        
#     def heat_off(self, tank_num): #turn off associated heater
#         GPIO.output(self.heater_pins[tank_num], heater_off)
#         
    def chill(self, tank_num): #turn on associated chiller
        GPIO.output(self.heater_pins[tank_num], heater_off)
        GPIO.output(self.chiller_pins[tank_num], chiller_on)

    def cleanup(self): #cleanup
        GPIO.cleanup()
