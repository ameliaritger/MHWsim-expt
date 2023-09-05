import time
import datetime

sleep_measure = 1 #number of seconds to sleep between sampling (interval)

def save_and_sleep(m, temp_set, heater_status, avg_temps_all):
    all_temps = temp_set + heater_status + avg_temps_all
    m.save(all_temps) #save data to csv
    print(f"Temperatures saved, going to sleep for {sleep_measure} seconds...")
    heater_status, avg_temps_all = ([] for i in range(2) )#delete the list(s) by re-initializing a blank list
    time.sleep(sleep_measure)
    today = datetime.datetime.today() #check the current date
    
    return avg_temps_all, heater_status, today