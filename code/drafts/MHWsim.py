import glob
import csv
import time
import datetime
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import MHWramp as mhwr

with open("./mhw_profile.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=",")
    temp_profile = {}
    for row in reader:
        year, month, day = datetime.datetime.strptime(row["t"], "%Y-%m-%d").year, datetime.datetime.strptime(row["t"], "%Y-%m-%d").month, datetime.datetime.strptime(row["t"], "%Y-%m-%d").day
        # Create a new date without the year
        date = f"{month}-{day}"
        try:
            temperature = float(row["temp"])
            temperature = round(temperature, 3)
        except ValueError:
            temperature = None
        temp_profile[date] = temperature
    #print(temp_profile)
    amb_temp = []
    for date, temperature in temp_profile.items():
        if temperature is not None:
            amb_temp.append(temperature)
print(len(amb_temp))
      
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
ref_high = 100; #boiling water temperature
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

severe_heatwave_temps, severe_up_days, severe_down_days = mhwr.temp_ramp(amb_temp, onset_rate, decline_rate, severe_temp_threshold)
#extreme_heatwave_temps, max3, max4 = mhwr.temp_ramp(ambient_temps, onset_rate, decline_rate, extreme_temp_threshold)

print(severe_heatwave_temps)

#Start timer
tic = time.perf_counter() 
toc = 0

# Initialize heaters to off in all tanks
heater_state = 0
for i in range(len(heater_pins)):
    io_inst.heat(i, heater_state)
    print(f"Heater {i} OFF")

# Run the MHW simulation
test_period = 60 # seconds, 262800*60 for 6 months 
while toc - tic < test_period:
    for i in range(num_therm):
        if i == 0:
            current_date = datetime.datetime.today() #Read Today's date
            month, day = current_date.month, current_date.day #Define the month and day for Today
            temp_set_point = temp_profile[f"{month}-{day}"] #Get temperature set point for today
            print(f"The temperature set point for today is: {temp_set_point}")
        temp_ctrl[i].load_temp() #Read temperatures on all sensors
        i_cal = device_cal[temp_ctrl[i].Name] #Get calibration values for sensor
        raw_high =  i_cal[0] #Read in high calibration value for sensor
        raw_low = i_cal[1] #Read in low calibration value for sensor
        raw_range = raw_high - raw_low #Calculate the calibration value range
        corrected_value.append((((temp_ctrl[i].Temp  - raw_low) * ref_range) / raw_range) + ref_low) #Calibrate sensor readings 
        print(f"raw value of sensor {i} is {temp_ctrl[i].Temp}, corrected value is {corrected_value[i]}.")
        time.sleep(0.1) #sleep for x seconds
    if io_inst.heater_states[0] == 0: #If tank 0 heater is off
        if (corrected_value[0] <= temp_set_point): #Ambient tank conditions
        #if (corrected_value[0] <= corrected_value[2] + severe_temp): # && (toc_value < test_period):
            io_inst.heat(0, 1)
            print("heater ON!")
            time.sleep(60) #sleep for 1 minute before checking again
    else: #If tank 0 heater is on
        if (corrected_value[0] > temp_set_point):
        #if (corrected_value[0] > corrected_value[2] + severe_temp):
            io_inst.heat(0, 0)
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
