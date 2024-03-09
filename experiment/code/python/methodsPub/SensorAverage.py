import time
import pandas as pd
import numpy as np
import SensorInfo as sinfo

#Iniitialize lists and variables
avg_temps, all_temps_avg = ([] for i in range(2)) #initialize blank list for each treatment plus sensor temp correction

#Initialize sleep times
sleep_process = 0.1 #number of seconds to sleep between ever sensor reading (to allow processor to catch up)

repeat_measurements = 3

def get_avg_temp(temp_ctrl, sleep_repeat):
    all_temps_df = pd.DataFrame(0, index = np.arange(3), columns = (sinfo.mix_tank + sinfo.hot_tank + sinfo.cold_tank + sinfo.no_tank))
    #print(all_temps_df)
    for number_of_rows in range(repeat_measurements):
        for index in range(len(temp_ctrl)):
            temp_ctrl[index].load_temp() #Read temperatures on chill tank sensors
            device_cal_val = sinfo.device_cal[temp_ctrl[index].Name] #Get calibration values for sensor
            raw_high =  device_cal_val[0] #Read in high calibration value for sensor
            raw_low = device_cal_val[1] #Read in low calibration value for sensor
            raw_range = raw_high - raw_low #Calculate the calibration value range
            calibrated_val = (((temp_ctrl[index].Temp  - raw_low) * sinfo.ref_range) / raw_range) + sinfo.ref_low #Calibrate sensor readings
            matching_cell = all_temps_df.columns.get_loc(temp_ctrl[index].Name)
            all_temps_df.iloc[(number_of_rows, matching_cell)] = calibrated_val
            time.sleep(sleep_process)
        time.sleep(sleep_repeat)
    avg_cold = all_temps_df[all_temps_df.columns.intersection(sinfo.cold_tank)].mean().mean()
    avg_mix = all_temps_df[all_temps_df.columns.intersection(sinfo.mix_tank)].mean().mean()
    avg_hot = all_temps_df[all_temps_df.columns.intersection(sinfo.hot_tank)].mean().mean()
    avg_no = all_temps_df[all_temps_df.columns.intersection(sinfo.no_tank)].mean().mean()
    print(f"The mixing tank temp average is {avg_mix}")
    print(f"The cold tank temp average is {avg_cold}")
    avg_temps = [avg_mix, avg_hot, avg_cold, avg_no] #create list of average temperatures for each tank
    all_temps = all_temps_df.mean(axis=0).apply(lambda x: round(x,3)).tolist() #create a list of the mean average temps for each sensor, rounded to 3 digits
    all_temps = all_temps[:7] #remove no_tank
    
    return all_temps, avg_temps
