# pytact
Presentation of tactile stimuli and assessment of button presses for neuroscience research using python

Author: Xaver Fuchs, October 2020, xaver.fuchs@uni-bielefeld.de

Module to control Tactamp and switchboxes by Dancer Design and response buttons using Labjack T series DAC devices

## To do 
- add detailed description of experimental setup
- write functions for timing self-test
- implement support for National Instruments (NI) devices

## Issues/limitations
- At the moment the functionality is not well suited to produce overalapping or simultaneous stimuli with different intensities. The reason is that it is mainly based on using one DAC and switch it's output between channels/stimulators
- Triggering severl stimulators at the same time (or after one another with overlaps) is possible but with the restriction taht they have the same intensity


## A word about units
- to minimize computations inside the time critical functions, time units are always defined as seconds
- for convenience and to avoid long and hard to read floats, reaction times are returned as milliseconds
