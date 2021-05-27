This file shows some example calls of functions from the module

# Initialization

```python
from pytact import *
initiateLJ() #runs the initialization function (see defaults: by defaults expects Labjack T4)
intitRTChannels(channels=["FIO4", "FIO5"]) #actually this just sets the ports to HIGH (which they mostly are anyway after turning devive on
```

# Stimuli 
## Single trial function

This call starts a single stimulus with the given parameters. Note that Intensity is defined in putput voltage of the Labjack. So intensity ranges from 0 to 3.3 V.

```python
startTrialLJ(Stimulator=1, Onset=0, Duration=0.1, Intensity=1.5, returnTimers=False, LJWaitTime=0, rezeroDAC=True)
```


## Multiple trial function
```python
#multiple trial function with list input
startMultipleTrialsLJ(Stimulators=[1, 1, 1], Onsets=[0, 0.1, 1], Durations=[0.01, 0.01, 0.1], Intensities=[1.5, 2.5, 3.5], returnTimers=True)

#multiple trials that is a 15ms vibratory stimulus at 200 hz with half of each cycle at max. at 200 hz one scle is 5 ms long
startMultipleTrialsLJ(Stimulators=[3, 3, 3], Onsets=[0, 0.005, 0.01], Durations=[0.0025, 0.0025,0.0025], Intensities=[4.5, 4.5, 4.5], returnTimers=True)

#train of 6 stimuli with list comrehension as arguments
startMultipleTrialsLJ(Stimulators=[3 for i in range(0,6)], Onsets=[0, 0.005, 0.01, 0.015, 0.02, 0.025], Durations=[0.005 for i in range(0,6)], Intensities=[4.3 for i in range(0,6)], returnTimers=True)

#multiple trial that is really just one
startMultipleTrialsLJ(Stimulators=[3], Onsets=[0], Durations=[0.01], Intensities=[5])

#6 stimuli with equal intensity and duration: the function accepts list with 1 element for repeated parameters
startMultipleTrialsLJ(Stimulators=[3, 4, 5, 6, 7, 8], Onsets=[0, 0.1, 0.2, 0.3, 0.4, 0.6], Durations=[0.1], Intensities=[2.5], returnTimers=True)

```

# Measure and analyze response times

## read responses from two buttons
```python
Responses = readRT(buttons=[1, 2], channels=["FIO4", "FIO5"], pollInterval=0.001, postResponseWaitTime=0.5, maxTime=3, debounceTime=0.03) 
```

## Convert response outout
```python
print(Responses) #original output

RList=sortResponses(Responses) different format with a list with 4 lists: presses (buttons), RTs of pressses, releases (buttons), RTs of relaeses. In the RT lists, there are sublists for the buttons
print(RList)
```

## Analyze these responses
```python
wasPressed(RTList) #were the buttons pressed?
getPressTime(RTList, Button=1)
```

## Use of 4 buttons simultaneosuly

```python
intitRTChannels(channels=["FIO4", "FIO5", "FIO6","FIO7"])
RTList = sortResponses(readRT(buttons=[1, 2, 3, 4], channels=["FIO4", "FIO5", "FIO6","FIO7"], pollInterval=0.001, postResponseWaitTime=0.5, maxTime=3, debounceTime=0.03))

getPressTime(RTList, Button=3)
```

## Stimulate and measure response times simultaneously
Usually, we want to listen to responses already while the stimuli are presented. This needs parallel computing, or threading. 
This is implemented in the stimAndRecord function

```python
#this starts a trial and in parallel listens to the timers
Responses = stimAndRecord(Stimulators=[3], Onsets=[0], Durations=[0.01], Intensities=[2.5], returnTimers=False, LJWaitTime=0, buttons=[1, 2], channels=["FIO4", "FIO5"], pollInterval=0.001, postResponseWaitTime=0.5, maxTime=3, debounceTime=0.03)
```

# Close the connection

```python
closeLJ()
```
