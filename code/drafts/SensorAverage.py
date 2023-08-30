import time
import pandas as pd
import numpy as np
import Temperature as tm #don't think I need this?

#Establish temperature sensor calibration parameters
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

#Iniitialize lists and variables
avg_temps, all_temps_avg = ([] for i in range(2)) #initialize blank list for each treatment plus sensor temp correction

#Initialize sleep times
sleep_process = 0.1 #number of seconds to sleep between ever sensor reading (to allow processor to catch up)

repeat_measurements = 3

def get_avg_temp(chill_devices, severe_devices, extreme_devices, sump_devices, temp_ctrl, sleep_repeat):
    all_temps_df = pd.DataFrame(0, index = np.arange(3), columns = pd.MultiIndex.from_tuples([("chill_devices", x) for x in chill_devices] + [("severe_devices", x) for x in severe_devices] + [("extreme_devices", x) for x in extreme_devices] + [("sump_devices", x) for x in sump_devices], names=["treatment", "measurement"]))
    for number_of_rows in range(repeat_measurements):  
        for treatment, device in all_temps_df.columns:
            temp_ctrl[device].load_temp() #Read temperatures on chill tank sensors
            device_cal_val = device_cal[temp_ctrl[device].Name] #Get calibration values for sensor
            raw_high =  device_cal_val[0] #Read in high calibration value for sensor
            raw_low = device_cal_val[1] #Read in low calibration value for sensor
            raw_range = raw_high - raw_low #Calculate the calibration value range
            corrected_round = round(((((temp_ctrl[device].Temp  - raw_low) * ref_range) / raw_range) + ref_low),3) #Calibrate sensor readings 
            all_temps_df.iloc[(number_of_rows, device)] = corrected_round
            time.sleep(sleep_process)
        time.sleep(sleep_repeat)
    avg_chill = all_temps_df["chill_devices"].mean().mean()
    avg_severe = all_temps_df["severe_devices"].mean().mean()
    avg_extreme = all_temps_df["extreme_devices"].mean().mean()
    print(f"The chill tank temp average is {avg_chill}")
    print(f"The severe tank temp average is {avg_severe}")
    print(f"The extreme tank temp average is {avg_extreme}")
    avg_temps = [avg_chill, avg_severe, avg_extreme] #create list of average temperatures for each treatment
    all_temps_sorted = all_temps_df.sort_index(level=1, axis=1) #put columns in numerical order
    all_temps_avg = all_temps_sorted.mean(axis=0).tolist() #create a list of the mean average temps for each sensor

    return all_temps_df, all_temps_avg, avg_temps
