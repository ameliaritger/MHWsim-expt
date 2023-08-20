import glob
import time
import datetime
import collections
import pandas as pd
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import MHWramp as mhwr

# Read the CSV file and convert to dictionary
temp_profile = pd.read_csv("mhw_profile.csv", skiprows=1, usecols=[0,1,2,3], names=["datetime", "severe", "extreme", "chill"])
temp_profile["datetime"] = temp_profile["datetime"].apply(lambda x: pd.to_datetime(x) + pd.Timedelta(days=365.25 * 8)) #convert datetime column to dates and times, then add 8 years to make it 2023/2024
temp_profile["datetime"] = temp_profile["datetime"].dt.tz_localize(None) #Remove the timezone from datetime
temp_profile = dict([(i,[x,y,z]) for i,x,y,z in zip(temp_profile["datetime"], temp_profile["chill"], temp_profile["severe"],temp_profile["extreme"])])
print(temp_profile)
    
m = mem.MEM("./local/","./external/") #need to modify for RPi

base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders

temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
num_therm = len(device_folders)              #calculate the number of thermistor pairs
print(f"The number of thermistors detected by RPi: {num_therm}")
for x in range(num_therm):                   #loop through each pair
    ctrl = tm.TEMP(device_folders[x])        #create thermistor controller for a single pair
    temp_ctrl.append(ctrl)                   #add that thermistor controller to the list
    print(f"{device_folders[x]}")

#Establish sensor calibration parameters
ref_high = 49; #Oakley lab water bath temperature
ref_low = 0; #ice bath temperature
ref_range = ref_high - ref_low
device_cal = {"28-00000eb42add": [48.687, 0.25], #0
              "28-00000ec23ab6": [48.812, 0.125],
              "28-00000eb50e10": [48.75, 0.187],
              "28-00000eb5045f": [48.687, 0.187], #3
              "28-00000eb4a798": [48.562, 0.125],
              "28-00000eb4cb62": [48.687, 0.25],
              "28-00000eb51050": [48.75, 0.25], #6
              "28-00000ec25534": [48.937, 0.25],
              "28-00000eb501b0": [48.75, 0.25],
              "28-00000eb496d2": [48.75, 0.187], #9
              "28-00000eb4b7e0": [48.812, 0.25],
              "28-00000eb3fd89": [48.937, 0.187],
              "28-00000ec24f93": [48.812, 0.062], #12
              "28-00000eb3cf7d": [48.875, 0.25],
              "28-00000eb3f54e": [48.75, 0.25], 
              "28-00000eb4619b": [48.812, 0.187], #15
              "28-00000eb52c32": [49.0, 0.25],
              "28-00000eb3e681": [48.937, 0.312]}
corrected_value = []

#Sensor 0, Heater 0 = Ambient
#Sensor 1, Heater 1 = Severe
#Sensor 3, Heater 3 = Extreme
#Sensors 4-8 = Ambient treatments
#Sensors 9-13 = Severe treatments
#Sensors 13-17 = Extreme treatments

heater_pins = [26, 20, 21] #20=LED2, #21=LED3, #26=LED1
io_inst = io.IO_CTRL(heater_pins)
io_inst.clear() #clear status

#Initialize MHW parameters
#severe_temp = 5
#extreme_temp = 8
#onset_rate = 0.6
#decline_rate = 1.04
severe_temp_threshold = 5 # Celsius
extreme_temp_threshold = 8 # Celsius
sampling_rate_per_day = 240
onset_rate = 0.6/sampling_rate_per_day
decline_rate = 1.04/sampling_rate_per_day

#severe_heatwave_temps, severe_up_days, severe_down_days = mhwr.temp_ramp(amb_temp, onset_rate, decline_rate, severe_temp_threshold)
#extreme_heatwave_temps, max3, max4 = mhwr.temp_ramp(ambient_temps, onset_rate, decline_rate, extreme_temp_threshold)

#print(severe_heatwave_temps)

#Start timer
tic = time.perf_counter() 
toc = 0

# Initialize heaters to off in all tanks
heater_state = 0
for i in range(len(heater_pins)):
    io_inst.heat(i, heater_state)
    print(f"Heater {i} OFF")

# Run the MHW simulation
test_period = 600 # seconds, 262800*60 for 6 months 
while toc - tic < test_period:
    for i in range(num_therm):
        if i == 0:
            current_datetime = datetime.datetime.now() #Read the current date and time
            closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
            temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
            print(f"The current temperature set points are: {temp_set}")
            chill_set = temp_set[0]
            severe_set = temp_set[1]
            extreme_set = temp_set[2]
        temp_ctrl[i].load_temp() #Read temperatures on all sensors
        i_cal = device_cal[temp_ctrl[i].Name] #Get calibration values for sensor
        raw_high =  i_cal[0] #Read in high calibration value for sensor
        raw_low = i_cal[1] #Read in low calibration value for sensor
        raw_range = raw_high - raw_low #Calculate the calibration value range
        corrected_value.append((((temp_ctrl[i].Temp  - raw_low) * ref_range) / raw_range) + ref_low) #Calibrate sensor readings 
        print(f"raw value of sensor {i} is {temp_ctrl[i].Temp}, corrected value is {corrected_value[i]}.")
        time.sleep(0.1) #sleep for x seconds
    if io_inst.heater_states[2] == 0: #If tank 0 heater is off
        if (corrected_value[17] > chill_set): #Ambient tank conditions
        #if (corrected_value[0] <= corrected_value[2] + severe_temp): # && (toc_value < test_period):
            io_inst.heat(2, 1)
            print("heater ON!")
            time.sleep(60) #sleep for 1 minute before checking again
    else: #If tank 0 heater is on
        if (corrected_value[17] > chill_set):
        #if (corrected_value[0] > corrected_value[2] + severe_temp):
            io_inst.heat(2, 0)
            print("heater OFF!")
            time.sleep(60) #lseep for 1 minute before checking again
    
    toc = time.perf_counter() #grab current time
    m.save(corrected_value) #save data to csv
    corrected_value = [] #delete the corrected value list and re-initialize a blank list

heater_state = 0
for i in range(len(heater_pins)):
    io_inst.heat(i, heater_state)
    print(f"Heater {i} TOTALLY OFF")
    
io_inst.cleanup() #cleanup