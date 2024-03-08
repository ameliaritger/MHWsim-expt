import glob
import time
import datetime
import pandas as pd
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import SensorAverage as savg
import CleanUp as clean

#heater set to 25/20, 20/18, 18/16 is TOO HOT
#10:30AM 5/8, chiller increased from 10/14C to 13/15C
#12:15 5/8, chiller increased to 57/59
#next step, reduce to only 2 tanks and pump chilled water to heating tank

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

    #Initialize heater pins
    control_pins = [26, 20, 21] #20=LED2, #21=LED3, #26=LED1; #26 is cold pump, #20 is hot pump, #21 is heaters
    io_inst = io.IO_CTRL(control_pins)

    #option 1: heater in 20G tank and pump control into 5G tanks; chiller in 20G tank and pump control into 5G tanks
    #option 2: heater in 5G tank and control to heater; chiller in 20G tank and pump control into 5G tanks
    # My experiment for the paper is going to be 2 temperatures (cold and hot), with replicates across 3 tanks each
    # I need 5-6 thermistors (not 15+...) 

    # Initialize power to off for all tanks
    heater_state = 0
    for heater_pin in range(len(control_pins)):
        io_inst.heat(heater_pin, heater_state)
        print(f"Sump tank {heater_pin} heater OFF")

    while today < mhw_end:
        current_datetime = datetime.datetime.now() #Read the current date and time
        if current_datetime.second % 30 == 00: #run script on the 30 seconds or 00 seconds mark
            closest_datetime = min(temp_profile.keys(), key=lambda x: abs(x - current_datetime)) #Find the date/time row in the temperature profile closest to current date and time
            temp_set = temp_profile[closest_datetime] #Extract the temperature values from the closest date and time
            print(f"The current temperature set point is: {temp_set}")
            avg_temps_all, avg_temps = savg.get_avg_temp(temp_ctrl, sleep_repeat)
            avg_temps[:] = [round(num, 2) for num in avg_temps] #round avg tank temperatures to 2 decimal places
            hot_set = temp_set[0]
            temp_set = [hot_set]
            if avg_temps[0] > temp_set[0]: #if the tank is too hot
                print(f"Tank too hot!")
                io_inst.heat(1, 0) #turn the hot pump off
                io_inst.heat(0, 1) #turn the cold pump on
                heater_status.append("off")
            elif avg_temps[0] < temp_set[0]: #if the tank is too cold
                print(f"Tank too cold!")
                io_inst.heat(0, 0) #turn the cold pump off
                io_inst.heat(1, 1) #turn the hot pump on
                heater_status.append("on")
            else: #if the temperature is just right
                print(f"Tank perfect temperature!")
                io_inst.heat(0, 0) #turn the cold pump off
                io_inst.heat(1, 0) #turn the hot pump off
                heater_status.append("off")
            sump_temps, avg_temps_all, heater_status, today = clean.save_and_sleep(m, temp_set, heater_status, avg_temps_all, sump_temps)
            if avg_temps[1] > (temp_set[0]+2): #if the heater tank is too hot
                io_inst.heat(2, 0) #turn the heaters off
                print(f"Heaters off")
            elif avg_temps[1] > temp_set[0]:
                io_inst.heat(2, 0) #keep the heaters off
                print(f"Heaters staying off")
            else:
                io_inst.heat(2, 1) #turn the heaters on
                print(f"Heaters on")
        else:
            time.sleep(sleep_repeat)

    #Finish the experiment, turn everything off!
    heater_state = 0
    for heater_num in range(len(control_pins)):
        io_inst.heat(heater_num, heater_state)
        print(f"All power {heater_num} TOTALLY OFF")

    io_inst.cleanup() #cleanup