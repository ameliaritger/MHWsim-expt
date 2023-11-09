import glob
import Temperature as tm
import time

#temp_profile = open("./tempProfile.csv", "r").read().split("\n")[1:-1] #grab all temps from profile file

base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders

Temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
num_therm = len(device_folders)              #calculate the number of thermistor pairs
print(f"The number of thermistors detected by RPi: {num_therm}")
for x in range(num_therm):                   #loop through each pair
    ctrl = tm.TEMP(device_folders[x])        #create thermistor controller for a single pair
    Temp_ctrl.append(ctrl)                   #add that thermistor controller to the list
    #print(f"{device_folders[x]}")

#Start timer
tic = time.perf_counter() 
toc = 0

# Testing Loop
test_period = 60 # seconds
while toc - tic < test_period:
    for i in range(num_therm):
        Temp_ctrl[i].load_temp()
        print(f"Tank {i} Temperature: {Temp_ctrl[i].Temp}")
        time.sleep(0.1)
    toc = time.perf_counter() #grab current time

print("All done!")