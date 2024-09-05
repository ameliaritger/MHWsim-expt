import glob
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import time

#temp_profile = open("./tempProfile.csv", "r").read().split("\n")[1:-1] #grab all temps from profile file

m = mem.MEM("./local/","./external/") #need to modify for RPi

base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders

Temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
num_therm = len(device_folders)              #calculate the number of thermistor pairs
print(f"The number of thermistors detected by RPi: {num_therm}")
for x in range(num_therm):                   #loop through each pair
    ctrl = tm.TEMP(device_folders[x])        #create thermistor controller for a single pair
    Temp_ctrl.append(ctrl)                   #add that thermistor controller to the list

start = 18     #pin start button is attached to
save_data = 12 #pin save button is attached to
stop = 15      #pin stop button is attached to

control_pins = [start, save_data, stop]
heater_pins = [26, 20, 21] #20=LED2, #21=LED3, #26=LED1
chiller_pins = [13, 16, 19]
io_inst = io.IO_CTRL(control_pins, heater_pins, chiller_pins)
io_inst.clear() #clear status

#Start timer
tic = time.perf_counter() 
toc = 0

# Initialize Temperature and heaters to off of Tanks
heater_state = 0
for i in range(len(heater_pins)):
    io_inst.heat(i, heater_state)
    print(f"Heater {i} OFF")

# Testing Loop
test_period = 60 # seconds
while toc - tic < test_period:
    for i in range(num_therm):
        Temp_ctrl[i].load_temp()
    if io_inst.heater_states[0] == 0:
        if (Temp_ctrl[0].Temp <= Temp_ctrl[1].Temp + 6): # && (toc_value < test_period):
            io_inst.heat(0, 1)
            print("heater ON!")
    else:
        if (Temp_ctrl[0].Temp > Temp_ctrl[1].Temp + 6):
            io_inst.heat(0, 0)
            print("heater OFF!")
    
    toc = time.perf_counter() #grab current time
    print(f"Tank 1 Temperature: {Temp_ctrl[0].Temp}")
    print(f"Tank 2 Temperature: {Temp_ctrl[1].Temp}")
    m.save(Temp_ctrl[0].Temp, Temp_ctrl[1].Temp) #save data to csv
    
heater_state = 0
for i in range(len(heater_pins)):
    io_inst.heat(i, heater_state)
    print(f"Heater {i} TOTALLY OFF")
    
io_inst.cleanup() #cleanup
