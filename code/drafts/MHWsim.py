import glob
import time
import datetime
#mport collections
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
#print(temp_profile)
    
m = mem.MEM("./local/","./external/") #need to modify for RPi

base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders

temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
num_therm = len(device_folders)              #calculate the number of thermistor pairs
print(f"The number of thermistors detected by RPi: {num_therm}")
for x in range(num_therm):                   #loop through each pair
    ctrl = tm.TEMP(device_folders[x])        #create thermistor controller for a single pair
    temp_ctrl.append(ctrl)                   #add that thermistor controller to the list
    #print(f"{device_folders[x]}")

#Establish sensor calibration parameters
ref_high = 49 #Oakley lab water bath temperature
ref_low = 0 #ice bath temperature
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
chill_devices = [0,1,2,3,4]
severe_devices = [5,6,7,8,9]
extreme_devices = [10,11,12,13,14]
avg_temps, chill_temps, severe_temps, extreme_temps = ([] for i in range(4)) #initialize blank lists for each treatment plus sensor temp correction
avg_chill, avg_severe, avg_extreme, chill_set, severe_set, extreme_set = [0 for i in range(6)] #initialize variables set to zero

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

#Establish experimental time periods
today = datetime.datetime.today()
mhw_date = datetime.datetime(2023, 9, 1) #date of start of MHW
post_mhw = datetime.datetime(2023, 10, 1) #date of start of recovery period

# Initialize heaters to off in all tanks
heater_state = 0
for heater_pin in range(len(heater_pins)):
    io_inst.heat(heater_pin, heater_state)
    print(f"Heater {heater_pin} OFF")
    
################################################### Run the MHW simulation
#PRE MHW TIME
while today < mhw_date:
    current_datetime = datetime.datetime.now() #Read the current date and time
    closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
    temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
    print(f"The current temperature set points are: {temp_set}")
    chill_set = temp_set[0]
    for temp_list in range(3):
        for device_list in [chill_devices, severe_devices, extreme_devices]:
            for device in device_list:
                temp_ctrl[device].load_temp() #Read temperatures on chill tank sensors
                device_cal_val = device_cal[temp_ctrl[device].Name] #Get calibration values for sensor
                raw_high =  device_cal_val[0] #Read in high calibration value for sensor
                raw_low = device_cal_val[1] #Read in low calibration value for sensor
                raw_range = raw_high - raw_low #Calculate the calibration value range
                corrected_round = round(((((temp_ctrl[device].Temp  - raw_low) * ref_range) / raw_range) + ref_low),3) #Calibrate sensor readings 
                #corrected_value.append(corrected_round) #Save this value to the corrected_value dataframe
                if device in chill_devices:
                    chill_temps.append(corrected_round) #corrected_value[device])
                elif device in severe_devices:
                    severe_temps.append(corrected_round)
                else:
                    extreme_temps.append(corrected_round)
                time.sleep(0.1) #wait for x seconds
            if device in chill_devices:
                avg_chill = sum(chill_temps) / len(chill_temps)
            elif device in severe_devices:
                avg_severe = sum(severe_temps) / len(severe_temps)
            else:
                avg_extreme = sum(extreme_temps) / len(extreme_temps)
            time.sleep(1) #wait for x seconds
    print(f"The chill tank temp average is {avg_chill}")
    print(f"The severe tank temp average is {avg_severe}")
    print(f"The extreme tank temp average is {avg_extreme}")
    avg_temps = [avg_chill, avg_severe, avg_extreme] #---> WHEN I PUT THIS OUTSIDE BEFORE FOR LOOP, VALUES DID NOT UPDATE (stayed 0) - WHY?
    heater_dict = {} #initialize blank heater dictionary to fill in following for loop
    for heater_num in range(len(avg_temps)):
        heater_dict[heater_num] = (avg_temps[heater_num], chill_set) #fill in the dictionary with average temps and set temps
    for heater_num, expt_temps in heater_dict.items():
        if io_inst.heater_states[heater_num] == 0: #If tank num heater is off
            if expt_temps[0] < expt_temps[1]:
                io_inst.heat(heater_num, 1)
                print(f"Sump tank {heater_num} heater ON!")
            else:
                print(f"Sump tank {heater_num} too hot! Need to chill.")
        else: #If tank 0 heater is on
            if expt_temps[0] >= expt_temps[1]:
                io_inst.heat(heater_num, 0)
                print(f"Sump tank {heater_num} heater OFF!")
    m.save(avg_temps) #save data to csv, --> NEED TO FIGURE OUT HOW TO AVERAGE TEMPS FROM EACH SENSOR/DEVICE AND SAVE IT
    avg_temps = [] #delete the corrected value list and re-initialize a blank list
    today = datetime.datetime.today()
    time.sleep(30) #wait for x seconds before checking temps again

#MHW TIME
while today < post_mhw:
    for i in range(num_therm):
        if i == 0:
            current_datetime = datetime.datetime.now() #Read the current date and time
            closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
            temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
            print(f"The current temperature set points are: {temp_set}")
            chill_set = temp_set[0]
            severe_set = temp_set[1]
            extreme_set = temp_set[2]
    for temp_list in range(3): #read temperature from each sensor 3x
        for device_list in [chill_devices, severe_devices, extreme_devices]:
            for device in device_list:
                temp_ctrl[device].load_temp() #Read temperatures on chill tank sensors
                device_cal_val = device_cal[temp_ctrl[device].Name] #Get calibration values for sensor
                raw_high =  device_cal_val[0] #Read in high calibration value for sensor
                raw_low = device_cal_val[1] #Read in low calibration value for sensor
                raw_range = raw_high - raw_low #Calculate the calibration value range
                corrected_round = round(((((temp_ctrl[device].Temp  - raw_low) * ref_range) / raw_range) + ref_low),3) #Calibrate sensor readings 
                if device in chill_devices:
                    chill_temps.append(corrected_round) #corrected_value[device])
                elif device in severe_devices:
                    severe_temps.append(corrected_round)
                else:
                    extreme_temps.append(corrected_round)
                time.sleep(0.1) #wait for x seconds
            if device in chill_devices:
                avg_chill = sum(chill_temps) / len(chill_temps)
            elif device in severe_devices:
                avg_severe = sum(severe_temps) / len(severe_temps)
            else:
                avg_extreme = sum(extreme_temps) / len(extreme_temps)
            time.sleep(1) #wait for x seconds
    print(f"The chill tank temp average is {avg_chill}")
    print(f"The severe tank temp average is {avg_severe}")
    print(f"The extreme tank temp average is {avg_extreme}")
    avg_temps = [avg_chill, avg_severe, avg_extreme]
    for heater_num, expt_temp in heater_dict.items():
        if io_inst.heater_states[heater_num] == 0:
            if expt_temp[0] < expt_temp[1]:
                io_inst.heat(heater_num, 1)
                print("heater ON!")
            else:
                print("Too hot! Need to chill.")
        else:
            if expt_temp[0] >= expt_temp[1]:
                io_inst.heat(heater_num, 0)
                print("heater OFF!")
    m.save(avg_temps) #save data to csv, --> NEED TO FIGURE OUT HOW TO AVERAGE TEMPS FROM EACH SENSOR/DEVICE AND SAVE IT
    avg_temps = [] #delete the corrected value list and re-initialize a blank list
    today = datetime.datetime.today()
    print("saved!")
    time.sleep(30) #wait for x seconds before checking temps again
    
###################################################
#Finish the experiment, turn everything off!
heater_state = 0
for i in range(len(heater_pins)):
    io_inst.heat(i, heater_state)
    print(f"Heater {i} TOTALLY OFF")
    
io_inst.cleanup() #cleanup