import glob
import Temperature as tm
import time
import Memory as mem

m = mem.MEM("./local/","./external/") #need to modify for RPi

base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders

Temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
num_therm = len(device_folders)              #calculate the number of thermistor pairs
print(f"The number of thermistors detected by RPi: {num_therm}")
for x in range(num_therm):                   #loop through each pair
    ctrl = tm.TEMP(device_folders[x])        #create thermistor controller for a single pair
    Temp_ctrl.append(ctrl)                   #add that thermistor controller to the list
    print(f"{device_folders[x]}")

#Establish sensor calibration parameters
ref_high = 99.9; #boiling water temperature
ref_low = 0; #ice bath temperature
ref_range = ref_high - ref_low
device_cal = {"28-3c01f0954653": [99.65, 0.297],
              "28-01144d35ebaa": [98.74, -0.062],
              "28-01144c456caa": [99.07, -0.187],
              "28-0114555ccfaa": [99.23, -0.062],
              "28-01144bb5d5aa": [98.50, -0.312],
              "28-011454fc11aa": [99.28, -0.321],
              "28-3c01f09549fb": [98.92, -0.031], 
              "28-3c01f095dbf9": [99, 0.497], #SENSOR 7, TRASH
              "28-011454ee16aa": [99.41, 0.065],
              "28-3c01f0954a3f": [99.37, 0.821],
              "28-01144c64e4aa": [99.64, -0.247]}
corrected_value = []

#Start timer
tic = time.perf_counter() 
toc = 0

# Testing Loop
test_period = 200 # seconds
while toc - tic < test_period:
    for i in range(num_therm):
        Temp_ctrl[i].load_temp()
        #print(f"sensor {i} Temperature: {Temp_ctrl[i].Temp}")
        i_cal = device_cal[Temp_ctrl[i].Name]
        raw_high =  i_cal[0]
        raw_low = i_cal[1]
        raw_range = raw_high - raw_low
        corrected_value.append((((Temp_ctrl[i].Temp  - raw_low) * ref_range) / raw_range) + ref_low)
        #print(f"{i_cal}, {raw_high}, {raw_low}")
        print(f"raw value of sensor {i} is {Temp_ctrl[i].Temp}, corrected value is {corrected_value[i]}.")
        time.sleep(0.1)
    
    toc = time.perf_counter() #grab current time
    m.save(corrected_value) #save data to csv
    corrected_value = [] #delete the corrected value list and re-initialize a blank list
    
print("All done!")