import numpy as np
    
def temp_ramp(ambient_temps, onset_rate, decline_rate, temp_threshold):
    # Generates a heat wave that ramps up from the ambient at an onset rate and then back down at the decline_rate up to specified threshold
    heatwave_temps = []
    ramp_up_days = 0
    heatwave_temps_current = ambient_temps[ramp_up_days]

    # Make incline and constant offset heat wave region
    while heatwave_temps_current < ambient_temps[ramp_up_days] + temp_threshold:
        heatwave_temps.append(heatwave_temps_current)
        heatwave_temps_current += onset_rate
        ramp_up_days+= 1

    heatwave_values = heatwave_values + [ambient_temps + temp_threshold for value in ambient_temps[ramp_up_days:]]
    #else:
    #    heatwave_temps = np.concatenate([heatwave_temps, ambient_temps[ramp_up_days:]+temp_threshold])

    # Make decline from end of data
    ramp_down_days = 1
    heatwave_temps_current = ambient_temps[-ramp_down_days]
    while (heatwave_temps_current < ambient_temps[-ramp_down_days]+temp_threshold):
        heatwave_temps[-ramp_down_days] = heatwave_temps_current
        heatwave_temps_current += decline_rate
        ramp_down_days+=1

    return heatwave_temps, ramp_up_days, ramp_down_days