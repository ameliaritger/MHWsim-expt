import numpy as np

numberOfDays = 7
hours = 24*numberOfDays
minutes = hours*60

# rampRate = 24 #24 hour ramp up time

rampDay = np.arange(start=0, stop=60*12, step=1)

A = 0.0000135
rampUp = A*(rampDay**2) +16
numberOfDays -=1
rampDown = np.flip(rampUp)
numberOfDays -=1
steady = 23*np.ones(24*1*60)
holdThree = 10*np.ones(3*60)

data = np.concatenate((rampUp, steady), axis=0)
data = np.concatenate((data, rampDown), axis=0)
data = np.concatenate((data, holdThree), axis=0)
data = np.concatenate((data, rampUp), axis=0)
data = np.concatenate((data, rampDown), axis=0)


print(len(data))
np.savetxt("/home/pi/tempSeries.csv", data, delimiter=",")