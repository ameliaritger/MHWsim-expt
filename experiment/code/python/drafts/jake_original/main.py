import glob
import Temperature as tm
import IO_ctrl as io
import Memory as mem
import time

if __name__ == "__main__":
    temp_profile = open("./tempProfile.csv", "r").read().split("\n")[1:-1] #grab all temps from profile file
    print(len(temp_profile))

    m = mem.MEM("./local/","./external/") #need to modify for RPi

    base_dir = '/sys/bus/w1/devices/'            #directory where thermistor files are populated
    device_folders = glob.glob(base_dir + '28*') #get list of all thermistor folders

    Temp_ctrl = []                               #create empty list that we will populate with thermistor controllers
    num_therm = len(device_folders)              #calculate the number of thermistor pairs
    print(num_therm)
    for x in range(num_therm):                   #loop through each pair
        ctrl = tm.TEMP(device_folders[x])        #create thermistor controller for a single pair
        Temp_ctrl.append(ctrl)                   #add that thermistor controller to the list
        temp = ctrl.load_temp()
        temp_raw = ctrl.read_temp_raw(ctrl.Probe)
        print(f"Raw Temp Read {temp_raw}")
        print(f"Temperature Celsius {temp}")
#     start = 12     #pin start button is attached to
#     save_data = 18 #pin save button is attached to
#     stop = 15      #pin stop button is attached to

    start = 18     #pin start button is attached to
    save_data = 12 #pin save button is attached to
    stop = 15      #pin stop button is attached to

    control_pins = [start, save_data, stop]
    #heater_pins = [21,26]
    heater_pins = [20, 21, 26]
    #heater_pins = [22, 23]
    chiller_pins = [13, 16, 19]
    io_inst = io.IO_CTRL(control_pins, heater_pins, chiller_pins)

    #while(io_inst.status != "start"): #wait for start
    #    pass

#     for j in range(2): #loop over thermistors
#         io_inst.heat(0)
#         io_inst.heat(1)
#         time.sleep(1)
#         io_inst.chill(0)
#         io_inst.chill(1)
#         time.sleep(1)

    io_inst.clear() #clear status

    for i in temp_profile: #loop over each temperature
        # i = float(i) + 1
        i = 50
        tic = time.perf_counter() #start timer
        tocvalue = 0
        while(tocvalue < 20): #wait until 2 minutes is up
            for j in range(num_therm): #loop over thermistors
                temp = Temp_ctrl[j].load_temp() #measure temp
                if (temp > float(i)): #compare temp # set up more indepth control settings here 
                    io_inst.chill(j)
                else:
                    io_inst.heat(j)
            toc = time.perf_counter() #grab current time
            tocvalue = toc - tic #calculate how long we have been in this while loop

            if(io_inst.status == "stop"): break #if stop button is pressed, break

        if(io_inst.status == "stop"): break #if stop button is pressed, break. Need to discuss ways to make this better
        
        print(i, temp)
        m.save(i, temp) #save data to csv

    io_inst.cleanup() #cleanup
