# MHWsim 

<p align="center"><img src="/media/mhw_tanks.png" alt="5 gallon tanks in lab containing strabwerry anemones on coral frag tiles" width="50%"/></p>

## What's in this repository?
This repository contains the scripts and files related to the development of a Marine Heatwave Simulator (MHWsim) using a Raspberry Pi, and the data collected during a MHWsim experiment using Corynactis californica as a study organism.

This repository is maintained by Hofmann Lab graduate student Amelia Ritger (GitHub: [@ameliaritger](https://github.com/ameliaritger)) at the University of California, Santa Barbara in the Department of Ecology, Evolution, & Marine Biology. Please direct any questions or comments about this repository to [Amelia Ritger](mailto:aritger@ucsb.edu).

## How is this repository structured?
```
.
├── experiment/                                 # directory containing all files related to the Amelia's MHWsim experiment
|
├── media/                                      # directory containing media files for project repo
|
├── simulator/                                  # directory containing resources for building and running the RPi MHWsim system
|   └── code/                                   # directory with scripts for the MHWsim
|      └── Alert.py                             # script for sending SMS alerts
|      └── CleanUp.py                           # script for saving data, clearing lists/variables, and going to sleep 
|      └── drafts/                              # directory containing draft .py scripts
|      └── IO_ctrl.py                           # script for initializing relay board
|      └── main.py                              # main script to run all code associated with MHWsim
|      └── Memory.py                            # script for constructing and saving to .csv file
|      └── mhw_profile.csv                      # DESCRIPTION
|      └── MHWRamp.py                           # script for ramping up and down temperatures at start/end of MHW event
|      └── MHWsim.py                            # script for initializing MHWsim objects, parameters and then running the MHWsim 
|      └── PID.py                               # script for Proportional–integral–derivative controller algorithm
|      └── SensorAverage.py                     # DESCRIPTION
|      └── SensorInfo.py                        # DESCRIPTION
|      └── Temperature.py                       # DESCRIPTION
|
|   └── documentation/                          # directory containing MHWsim system build documentation
|      └── rpiMHWsimConstruction.docx           # document for building the RPi MHWsim system
|
├── .gitignore
|
├── LICENSE
|
├── README.md
|
└── MHWsim.Rproj
```

## PUBLICATION TO COME, STAY TUNED!
