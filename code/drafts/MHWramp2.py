import numpy as np

def ramp_up(start_temp, end_temp, onset_rate, sampling_rate):
    values = []
    
    for i in range(sampling_rate):
        value = start_temp + onset_rate * i / (sampling_rate - 1)
        if value > end_temp:
            value = end_temp
        values.append(value) #I need to make this a loop so that when t = 0, follow this, but then verything after follow the most recent temp measurement?
    
    return(values)
    
def ramp_down(start_temp, end_temp, decline_rate, sampling_rate):
    values = []
    
    for i in range(sampling_rate):
        value = start_temp - decline_rate * i / (sampling_rate - 1)
        if value < end_temp:
            value = end_temp
        values.append(value)
        
    return(values)