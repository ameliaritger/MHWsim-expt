import time
import CleanUp as clean

wait_time = time.perf_counter()
now = time.perf_counter()

class TEMP(object):
    def __init__(self, device_folder):
        self.Probe = device_folder + '/w1_slave'
        self.Name = device_folder.split('/')[-1]
        self.Temp = []

    def load_temp(self): #unnecessary, from when there were two thermistors per tank
        self.Temp = self.read_temp(self.Probe)
        return self.Temp

    # https://www.circuitbasics.com/raspberry-pi-ds18b20-temperature-sensor-tutorial/
    def read_temp_raw(self, device_file):
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close
        return lines

    def read_temp(self, device_file):
        try:
            lines = self.read_temp_raw(device_file)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2) #wait for the YES before trying again
                lines = self.read_temp_raw(device_file)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string)/1000.0
                now = time.perf_counter()
                return temp_c
        except:
            temp_c = float(-1)
            now = time.perf_counter()
            if now > wait_time:
                clean.send_email()
                wait_time = now+5*60
            return temp_c
        
def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close
    return lines
    
def read_temp(device_file):
    try:
        lines = read_temp_raw(device_file)
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2) #wait for the YES before trying again
            lines = read_temp_raw(device_file)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string)/1000.0
            return temp_c
    except:
        temp_c = float(-1)
        now = time.perf_counter()
        if now > wait_time:
            clean.send_email()
            wait_time = now+5*60
        return temp_c
