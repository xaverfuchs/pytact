'''
pytact: Presentation of tactile stimuli and assessment of button presses for neuroscience research using python.
Author: Xaver Fuchs, October 2020, xaver.fuchs@uni-bielefeld.de
'''

# XXXXXXXXXXXXXXXXXXXXXXXXX IMPORT MODULES XXXXXXXXXXXXXXXXXXXXXXXXXX
import time
from labjack import ljm
import numpy as np
import concurrent.futures #module for threading


# XXXXXXXXXXXXXXXXXXXXXXXXX LABJACK FUNCTIONS XXXXXXXXXXXXXXXXXXXXXXXXXX

#create a Labjack connection
def initiateLJ(device="T4"):
    global handle
    handle = ljm.openS(device, "ANY", "ANY")  # T4 device, Any connection, Any identifier
    info = ljm.getHandleInfo(handle)
    print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
          "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
          (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

#close the connection
def closeLJ():
   ljm.close(handle)


# XXXXXXXXXXXXXXXXXXXXXXXXX FUNCTIONS FOR STIMULI XXXXXXXXXXXXXXXXXXXXXXXXXX

#for a rectangular type of trial
def startTrialLJ(Stimulator=1, Onset=0, Duration=0.1, Intensity=1.5, returnTimers=False, LJWaitTime=0, rezeroDAC=True):
    '''
    Changes 2020-12: there is a flag now defining whether the DAC is returned to zero volts at the end or not. 
    In some instances, when  triggering  fast, this can be a disadvantage, hece the option
    '''
    
    
    StartTime=time.perf_counter()
    numFrames = 11
    names = ["DAC0", "EIO0", "EIO1", "EIO2", "EIO3", "EIO4", "EIO5", "EIO6", "EIO7", "CIO0", "CIO1"] #first for dac, the rest for switch box
    aValues = [Intensity, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] #intensity in volts, the rest are DIO states that are initially zero
    aValues[Stimulator]=1

    #active wait for the time constant to have passed
    while (time.perf_counter() - StartTime) < LJWaitTime:
        pass

    TrialStartTime=time.perf_counter()

    #set to target values
    ljm.eWriteNames(handle, numFrames, names, aValues)
    
    if rezeroDAC:
        aValues = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] #volts to zero and DIO also to zero
    else:
        aValues = [Intensity, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] #volts to zero and DIO also to zero

    while (time.perf_counter() - StartTime) < Duration:
        pass

    #interrupt connection to stimulator
    ljm.eWriteNames(handle, numFrames, names, aValues)
    TrialEndTime=time.perf_counter()

    if returnTimers==True:
        return StartTime, TrialStartTime, TrialEndTime


def startMultipleTrialsLJ(Stimulators=[1], Onsets=[0], Durations=[0.01], Intensities=[1.5], returnTimers=False, LJWaitTime=0.001):
    '''
    Functionality:
        there are three lists:
            one is for the stimulator numbers
            one is for the onset times
            one is for the intensities
        The functino loops over the list and then starts the trials.
        Trials are integers
        Times are secods. Returned times are milliseconds!
        
        NEW 2020-12: function can deal with  onsets in weird order
        and function handles cases where Durations and Intensities are lists with one element by repeatinng that element
        LJ Wait time is now a default value of 1 ms that the function prepares before actually starting the sstimuli
    '''
    #timer for the wait time
    StartTime=time.perf_counter()
    
    #check if Intensities and/or Durations are one-element lists
    if len(Intensities)==1:
        Intensities=[Intensities[0] for i in range(0, len(Stimulators))]
    if len(Durations)==1:
        Durations=[Durations[0] for i in range(0, len(Stimulators))]
    
    
    #bring stimli in correct order
    OnsetOrder=sorted(range(len(Onsets)), key=Onsets.__getitem__)
    Onsets=[Onsets[i] for i in OnsetOrder]
    Stimulators=[Stimulators[i] for i in OnsetOrder]
    Durations=[Durations[i] for i in OnsetOrder]
    Intensities=[Intensities[i] for i in OnsetOrder]
    
    #list for collecting trigger times
    TriggerTimes=[]
    
    #active wait for the time constant to have passed
    while (time.perf_counter() - StartTime) < LJWaitTime:
        pass

    Trial_StartTime=time.perf_counter()
    for i in range(0, len(Stimulators)):
        Stimulator=Stimulators[i]
        Onset=Onsets[i]
        Duration=Durations[i]
        Intensity=Intensities[i]


        while (float(TrialTimer.getTime())) < float(Onset):
            pass

        #record time and start trial
        TriggerTimes.append(time.perf_counter() - Trial_StartTime)
        startTrialLJ(Stimulator, Onset, Duration, Intensity, returnTimers=returnTimers, LJWaitTime=0, rezeroDAC=False)
    if returnTimers:
        return(TriggerTimes)



# XXXXXXXXXXXXXXXXXXXXXXXXX FUNCTIONS FOR RESPONSE BUTTONS XXXXXXXXXXXXXXXXXXXXXXXXXX
def intitRTChannels(channels=["FIO4", "FIO5"]):
    numFrames = len(channels)
    names = channels
    aValues = [1 for i in range(0,numFrames)]
    ljm.eWriteNames(handle, numFrames, names, aValues) #channels set to HIGH (pull down logic, ie connect to ground to trigger)


def readRT(buttons=[1, 2], channels=["FIO4", "FIO5"], pollInterval=0.001, postResponseWaitTime=0.5, maxTime=3, debounceTime=0.03):
    '''
    returns a list of the shape:
        Presses (buttons)
        RTs of presses
        Releases (buttons)
        RTs of releases

        Function deals with button bounces using a defined debounce time
        Flags: most are obvious apart from
        maxTime: if no response has been given, the function ends and returns empty lists
        postResponseWaitTime: if this is set to a value shorter than maxTime this means that after a first response, the function waits for further responses for that time and if thex don't occur the function stops

    '''
    numFrames = len(channels)
    names = channels

    #start timer and get initial state
    lastState=ljm.eReadNames(handle, numFrames, names)
    TimeStart=time.perf_counter()
    lastTime=TimeStart

    #initial values
    pollNow = 0
    Presses=[]
    Releases=[]
    Presses_RT=[]
    Releases_RT=[]
    Responded=False
    RTNow=[]
    ButtonBounceTimes=[0 for i in range(0, len(buttons))] #an array of last event times for the buttons. state changes will be ignored if time is not larger than all the change times plus debounce time

    #start listening loop
    TimeNow=time.perf_counter()
    while (TimeNow - TimeStart) < maxTime:
        TimeNow=time.perf_counter()
        if TimeNow > (TimeStart + pollInterval * pollNow): #if this is true then it is time to poll
            newState=ljm.eReadNames(handle, numFrames, names)
            if not newState == lastState:
                RTNow = round((TimeNow - TimeStart)*1000, 2) #code as ms
                #print(pollNow)
                #now toggle through the buttons
                for i in range(0,len(buttons)):
                    if ButtonBounceTimes[i] < TimeNow: #only interpret button event if it happens after teh debounce time
                        if newState[i] < lastState[i]: #means a press
                            Presses.append(buttons[i])
                            Presses_RT.append(RTNow)
                            ButtonBounceTimes[i] = TimeNow + debounceTime #adds element to the list for debouncing
                        elif newState[i] > lastState[i]: #means a release
                            Releases.append(buttons[i])
                            Releases_RT.append(RTNow)
                            ButtonBounceTimes[i] = TimeNow + debounceTime #adds element to the list for debouncing
                Responded=True
                lastState = newState
                pollNow += 1
        if Responded and TimeNow > (TimeStart + RTNow/1000 + postResponseWaitTime):
            break
    return([Presses, Presses_RT, Releases, Releases_RT])


def sortResponses(Responses):
     #reshape data in a way that output is a list of lists and each list is one button presses and releases
    Presses=np.array(Responses[0])
    Presses_RT=np.array(Responses[1])
    Releases=np.array(Responses[2])
    Releases_RT=np.array(Responses[3])
    newPressesRT=[]
    newReleasesRT=[]
    #events belonging to each button
    newPressesButtons=list(np.unique(Presses))
    for i in newPressesButtons:
        Presses_RT_filter = np.array(Presses)==i
        Presses_RT_now = Presses_RT[Presses==i]
        newPressesRT.append(list(Presses_RT_now))

    newReleasesButtons=list(np.unique(Releases))
    for i in newReleasesButtons:
        Releases_RT_filter = np.array(Releases)==i
        Releases_RT_now = Releases_RT[Releases==i]
        newReleasesRT.append(list(Releases_RT_now))

    return(newPressesButtons, newPressesRT, newReleasesButtons, newReleasesRT)



# SOME CONVENIENCE FUNCTIONS TO FURTHER ANALYZE RESPONSES
#note the functions expect sortedResponses, ie output of the sortResponse() funtion
def wasPressed(RTList):
    #this function returns whether a button has been pressed (given a list)
    if len(RTList[0])>0:
        return(True)
    else:
        return(False)

def wasReleased(RTList):
    #this function returns whether a button has been released (given a list)
    if len(RTList[2])>0:
        return(True)
    else:
        return(False)

def getPressTime(RTList, Button=1):
    if Button in RTList[0]:
        RTs=RTList[1][RTList[0].index(Button)]
    else:
        RTs=[]
    return(RTs)

def getReleaseTime(RTList, Button=1):
    if Button in RTList[2]:
        RTs=RTList[3][RTList[2].index(Button)]
    else:
        RTs=[]
    return(RTs)

#these are extensions to ask whether specific buttons have been used
def wasPressedButton(RTList, Button=1):
    if wasPressed(RTList) and len(getPressTime(RTList, Button=Button)) > 0:
        return(True)
    else:
        return(False)

def wasReleasedButton(RTList, Button=1):
    if wasReleased(RTList) and len(getReleaseTime(RTList, Button=Button)) > 0:
        return(True)
    else:
        return(False)



# XXXXXXXXXXXXXXXXXXXXXXXXX HIGHER ORDER FUNCTIONS WITH PARALLEL FUNCTIONALITY XXXXXXXXXXXXXXXXXXXXXXXXXX

#usually one wants to start a stimulus and simultaneously start recording response times
def stimAndRecord(Stimulators=[1], Onsets=[0], Durations=[0.01], Intensities=[1.5], returnTimers=False, LJWaitTime=0, buttons=[1, 2], channels=["FIO4", "FIO5"], pollInterval=0.001, postResponseWaitTime=0.5, maxTime=3, debounceTime=0.03):
    executor=concurrent.futures.ThreadPoolExecutor()

    #these functions inherit input from main function
    Stimulator = executor.submit(startMultipleTrialsLJ, Stimulators, Onsets, Durations, Intensities, returnTimers, LJWaitTime)
    RTReader = executor.submit(readRT, buttons, channels, pollInterval, postResponseWaitTime, maxTime, debounceTime)

    #now wait for both processes to finish
    while Stimulator.running() or RTReader.running():
        pass

    Responses = RTReader.result()

    #this is optionally but probably useful: reshape the output format
    RTList=sortResponses(Responses)
    return(RTList)


