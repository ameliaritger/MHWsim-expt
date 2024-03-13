import glob
import time
import datetime
import pandas as pd
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import SensorAverage as savg
import CleanUp as clean
import PID

#heater set to 25/20, 20/18, 18/16 is TOO HOT
#10:30AM 5/8, chiller increased from 10/14C to 13/15C
#12:15 5/8, chiller increased to 57/59
#2:45 changed temp comparison to 0.04 threshold rather than "too hot/too cold"
#4:10 reduced to 0.01 threshold
#5:30, reduced to only 2 tanks and pumping chilled water to heating tank
#5/9 9:50 added PID loop
# 11:00 P 0.1
# 12:00 D 1/900
# heater #2 unplugged 3pm ish
# 5/10 flipped pid loop to chill from heat
#5/11 transitioned back to 3-tank setup
#5/12 moved cold sensor to different part of mix tank, swapped PID from chill to heat
#12:00 removed the "cold" sensor from mix tank because it's fucked, added chiller on flag, increased chillers from 56 to 57
#16:30 no longer round values, maybe that will help with overshoot?
#17:15 removed 5 probes (faster?) and changed sampling to once every 15 seconds where possible

#min temp is 58F, max temp is 60F

def mhw_sim():
    # Read the CSV file and convert to dictionary
    temp_profile = pd.read_csv("2015mhw_profile.csv", skiprows=1, usecols=[0,1], names=["datetime", "temp"])
    temp_profile["datetime"] = temp_profile["datetime"].apply(lambda x: pd.to_datetime(x) + pd.Timedelta(days=365.25 * 9)) #convert datetime column to dates and times, then add 9 years to make it 2024
    temp_profile["datetime"] = temp_profile["datetime"].dt.tz_localize(None) #Remove the timezone from datetime
    temp_profile = dict([(i,[x]) for i,x in zip(temp_profile["datetime"], temp_profile["temp"])])

    m = mem.MEM("./local/","./external/") #storage locations on RPi

    #Initialize temperature sensors
    base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
    device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders
    sensors_to_remove = ['/sys/bus/w1/devices/28-00000eb50e10', '/sys/bus/w1/devices/28-00000eb52c32', '/sys/bus/w1/devices/28-00000eb4619b', '/sys/bus/w1/devices/28-00000eb3f54e', '/sys/bus/w1/devices/28-00000eb496d2', '/sys/bus/w1/devices/28-00000eb501b0'] #remove sensors not in use (speed up system) 
    device_folders = [element for element in device_folders if element not in sensors_to_remove] #remove sensors not in use
    temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
    num_therm = len(device_folders)              #calculate the number of thermistor pairs
    print(f"The number of thermistors detected by RPi: {num_therm}")
    for index_num in range(num_therm):                   #loop through each pair
        ctrl = tm.TEMP(device_folders[index_num])        #create thermistor controller for a single pair
        temp_ctrl.append(ctrl)                   #add that thermistor controller to the list

#Initialize variables and lists
    hot_set = [0 for i in range(2)] #initialize variables set to zero
    temp_set, heater_status, sump_temps = ([] for i in range(3)) #initialize blank list for treatment temperature set points and heater statuses

    sleep_repeat = 0.1 #number of seconds to sleep between repeated temperature measurements

    #Initialize MHW parameters
    today = datetime.datetime.today() #date and time for today
    mhw_end = datetime.datetime(2024, 4, 1) #date of end of "experiment"
    chill_on = False #initialize flag
    
    #Initialize heater pins
    control_pins = [26, 20, 21] #20=LED2, #21=LED3, #26=LED1; #26 is cold pump, #20 is hot pump, #21 is heaters
    io_inst = io.IO_CTRL(control_pins)
    temp_thresh = 1.5 
    
    #initalize PID parameters
    Kp = 1 #proportional gain, determines how fast the system responds
    Ki = 0 #integral, determines how fast steady-state error is removed
    Kd = 0 #derivative, determines how far into the future to predict rate of change
    pid_value = 0 #initialize PID output threshold parameter
    error_integral = 0 #initialize error integral values
    error_derivative = 0 #initialize error derivative values
    previous_temp = 15 #arbitrary, will be changed immediately after first loop
    fo = 1/900 #calculated frequency of oscillation

    #option 1: heater in 20G tank and pump control into 5G tanks; chiller in 20G tank and pump control into 5G tanks
    #option 2: heater in 5G tank and control to heater; chiller in 20G tank and pump control into 5G tanks
    # My experiment for the paper is going to be 2 temperatures (cold and hot), with replicates across 3 tanks each

    # Initialize power to off for all tanks
    heater_state = 0
    for heater_pin in range(len(control_pins)):
        io_inst.heat(heater_pin, heater_state)
        print(f"Sump tank {heater_pin} heater OFF")

    while today < mhw_end:
        current_datetime = datetime.datetime.now() #Read the current date and time
        if current_datetime.second in (0,15,30,45): # to run script on the 30 seconds or 00 seconds mark, change to current_datetime.second % 30 == 00:
            print(current_datetime)
            closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
            temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
            print(f"The current temperature set point is: {temp_set}")
            avg_temps_all, avg_temps = savg.get_avg_temp(temp_ctrl, sleep_repeat)
            #avg_temps[:] = [round(num, 2) for num in avg_temps] #round avg tank temperatures to 2 decimal places
            avg_tank = avg_temps[0]
            hot_set = temp_set[0]
            temp_set = [hot_set]
            pid_out, previous_temp, error_integral, error_derivative = PID.control_temps(hot_set, avg_tank, previous_temp, error_integral, error_derivative, Kp, Ki, Kd)
            print(f"PID output is {pid_out}")
            if pid_out < pid_value and avg_temps[0] > temp_set[0]: #if the tank is too hot
                if not chill_on: #if the chiller hasn't already been on once - do this to control for getting too cold too fast
                    chill_on = True #set flag to true
                    print(f"Tank too hot!")
                    io_inst.heat(1, 0) #turn the heater pump off
                    io_inst.heat(0, 1) #turn the cold pump on
                    heater_status.append("off")                    
                else:
                    chill_on = False #reset the flag
                    print(f"Tank still too hot but let's chill out")
                    io_inst.heat(1, 0) #turn the heater pump off
                    io_inst.heat(0, 0) #turn the cold pump off
                    heater_status.append("chill")
            elif avg_temps[0] < temp_set[0]: #if the tank is too cold
                print(f"Tank too cold!")
                io_inst.heat(0, 0) #turn the cold pump off
                io_inst.heat(1, 1) #turn the heater pump on
                heater_status.append("on")
            else: #if the temperature is just right
                print(f"Tank perfect temperature!")
                io_inst.heat(0, 0) #turn the cold pump off
                io_inst.heat(1, 0) #turn the heater pump off
                heater_status.append("off")
            sump_temps, avg_temps_all, heater_status, today = clean.save_and_sleep(m, temp_set, heater_status, avg_temps_all, sump_temps)
            if avg_temps[1] > temp_set[0]+temp_thresh: #if heater tank is too hot
                io_inst.heat(2,0) #turn the heaters off
                print(f"Heater off")
            elif avg_temps[1] > temp_set[0]:
                io_inst.heat(2,0) #keep the heaters off
                print(f"Heater staying off")
            else:
                io_inst.heat(2,1)
                print(f"Heater on")
        else:
            time.sleep(sleep_repeat)
            
    #Finish the experiment, turn everything off!
    heater_state = 0
    for heater_num in range(len(control_pins)):
        io_inst.heat(heater_num, heater_state)
        print(f"All power {heater_num} TOTALLY OFF")

    io_inst.cleanup() #cleanup