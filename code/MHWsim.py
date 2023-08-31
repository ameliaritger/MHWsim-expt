import glob
import time
import datetime
import pandas as pd
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import MHWRamp as mhwr
import SensorAverage as savg
import SensorInfo as sinfo

# Read the CSV file and convert to dictionary
temp_profile = pd.read_csv("mhw_profile.csv", skiprows=1, usecols=[0,1,2,3], names=["datetime", "severe", "extreme", "chill"])
temp_profile["datetime"] = temp_profile["datetime"].apply(lambda x: pd.to_datetime(x) + pd.Timedelta(days=365.25 * 8)) #convert datetime column to dates and times, then add 8 years to make it 2023/2024
temp_profile["datetime"] = temp_profile["datetime"].dt.tz_localize(None) #Remove the timezone from datetime
temp_profile = dict([(i,[x,y,z]) for i,x,y,z in zip(temp_profile["datetime"], temp_profile["chill"], temp_profile["severe"],temp_profile["extreme"])])
    
m = mem.MEM("./local/","./external/") #storage locations on RPi

#Initialize temperature sensors
base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders
temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
num_therm = len(device_folders)              #calculate the number of thermistor pairs
print(f"The number of thermistors detected by RPi: {num_therm}")
for index_num in range(num_therm):                   #loop through each pair
    ctrl = tm.TEMP(device_folders[index_num])        #create thermistor controller for a single pair
    temp_ctrl.append(ctrl)                   #add that thermistor controller to the list

#Initialize variables and lists
chill_set, severe_set, extreme_set = [0 for i in range(3)] #initialize variables set to zero
temp_sets = ([] for i in range(1)) #initialize blank list for treatment temperature set points

sleep_measure = 1 #number of seconds to sleep between sampling (interval)
sleep_repeat = 0.1 #number of seconds to sleep between repeated temperature measurements
severe_thresh = 4 #initialize severe MHW parameter
extreme_thresh = 8 #initialize extreme MHW parameter
today = datetime.datetime.today() #date and time for today
mhw_date = datetime.datetime(2023, 9, 1) #date of start of MHW
post_mhw = datetime.datetime(2023, 10, 1) #date of start of recovery period

#Initialize heater pins
heater_pins = [26, 20, 21] #20=LED2, #21=LED3, #26=LED1
io_inst = io.IO_CTRL(heater_pins)
io_inst.clear() #clear status

# Initialize heaters to off in all tanks
heater_state = 0
for heater_pin in range(len(heater_pins)):
    io_inst.heat(heater_pin, heater_state)
    print(f"Sump tank {heater_pin} heater OFF")
    
################################################### Run the MHW simulation
#PRE MHW TIME
while today < mhw_date:
    current_datetime = datetime.datetime.now() #Read the current date and time
    if current_datetime.second % 30 == 00: #run script on the 30 seconds or 00 seconds mark
        closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
        temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
        print(f"The current temperature set points are: {temp_set}")
        chill_set = temp_set[0]
        avg_temps_all, avg_temps = savg.get_avg_temp(temp_ctrl, sleep_repeat)
        for index_num in range(len(heater_pins)):
            if io_inst.heater_states[index_num] == 0: #If tank heater is off
                if avg_temps[index_num] < chill_set:
                    io_inst.heat(index_num, 1)
                    print(f"Sump tank {index_num} heater ON!")
                else:
                    print(f"Sump tank {index_num} too hot! Need to chill.")
            else: #If tank heater is on
                if avg_temps[index_num] >= chill_set:
                    io_inst.heat(index_num, 0)
                    print(f"Sump tank {index_num} heater OFF!")
        m.save(avg_temps_all) #save data to csv
        print(f"Temperatures saved, going to sleep for {sleep_measure} seconds...")
        avg_temps_all = [] #delete the corrected list of all temps by re-initializing a blank list
        time.sleep(sleep_measure)
        today = datetime.datetime.today() #check the current date
    else:
        time.sleep(sleep_repeat)

#MHW TIME
start_ramp = time.perf_counter()
while today < post_mhw:
    current_datetime = datetime.datetime.now() #Read the current date and time
    if current_datetime.second % 30 == 00: #run script on the 30 seconds or 00 seconds mark
        closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
        temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
        print(f"The current temperature set points are: {temp_set}")
        delta_severe = mhwr.ramp_up(severe_thresh, start_ramp)
        delta_extreme = mhwr.ramp_up(extreme_thresh, start_ramp)
        chill_set = temp_set[0]
        severe_set = temp_set[0] + delta_severe
        extreme_set = temp_set[0] + delta_extreme
        temp_sets = [chill_set, severe_set, extreme_set]
        avg_temps_all, avg_temps = savg.get_avg_temp(temp_ctrl, sleep_repeat)
        for index_num in range(len(heater_pins)):
            if io_inst.heater_states[index_num] == 0: #If tank heater is off
                if avg_temps[index_num] < temp_sets[index_num]:
                    io_inst.heat(index_num, 1)
                    print(f"Sump tank {index_num} heater ON!")
                else:
                    print(f"Sump tank {index_num} too hot! Need to chill.")
            else: #If tank heater is on
                if avg_temps[index_num] >= temp_sets[index_num]:
                    io_inst.heat(index_num, 0)
                    print(f"Sump tank {index_num} heater OFF!")
        m.save(avg_temps_all) #save data to csv
        print(f"Temperatures saved, going to sleep for {sleep_measure} seconds...")
        avg_temps_all = [] #delete the corrected list of all temps by re-initializing a blank list
        time.sleep(sleep_measure)
        today = datetime.datetime.today() #check the current date                    
    else:
        time.sleep(sleep_repeat)
        
#RECOVERY TIME
start_ramp = time.perf_counter()
while today >= post_mhw:
    current_datetime = datetime.datetime.now() #Read the current date and time
    if current_datetime.second % 30 == 00: #run script on the 30 seconds or 00 seconds mark
        closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
        temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
        print(f"The current temperature set points are: {temp_set}")
        delta_severe = mhwr.ramp_down(severe_thresh, start_ramp)
        delta_extreme = mhwr.ramp_down(extreme_thresh, start_ramp)
        chill_set = temp_set[0]
        severe_set = temp_set[0] + delta_severe
        extreme_set = temp_set[0] + delta_extreme
        temp_sets = [chill_set, severe_set, extreme_set]
        avg_temps_all, avg_temps = savg.get_avg_temp(temp_ctrl, sleep_repeat)
        for index_num in range(len(heater_pins)):
            if io_inst.heater_states[index_num] == 0: #If tank heater is off
                if avg_temps[index_num] < temp_sets[index_num]:
                    io_inst.heat(index_num, 1)
                    print(f"Sump tank {index_num} heater ON!")
                else:
                    print(f"Sump tank {index_num} too hot! Need to chill.")
            else: #If tank heater is on
                if avg_temps[index_num] >= temp_sets[index_num]:
                    io_inst.heat(index_num, 0)
                    print(f"Sump tank {index_num} heater OFF!")
        m.save(avg_temps_all) #save data to csv
        print(f"Temperatures saved, going to sleep for {sleep_measure} seconds...")
        avg_temps_all = [] #delete the corrected list of all temps by re-initializing a blank list
        time.sleep(sleep_measure)
        today = datetime.datetime.today() #check the current date                    
    else:
        time.sleep(sleep_repeat)
        
###################################################
#Finish the experiment, turn everything off!
heater_state = 0
for heater_num in range(len(heater_pins)):
    io_inst.heat(heater_num, heater_state)
    print(f"Heater {heater_num} TOTALLY OFF")

io_inst.cleanup() #cleanup