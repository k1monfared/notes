---
tags: bash, linux, tablet
---

# Rotating X and disabling/enabling touch

- I use my tablet to write with its pen quite a lot, whether for taking notes, annotating a pdf file, or teaching. Here is a nice little script that I've made to get the screen to rotate and disable the touchpad, trackpad and touchscreen so that I can easily write with pen:
```
#!/bin/bash
status=$(xrandr --verbose | grep LVDS1 | awk '{print $5}')
if test inverted = $status
then
xrandr -o normal && xsetwacom list | grep stylus | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate none && xsetwacom list | grep eraser | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate none && xinput list | grep TouchPad | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 1 && xinput list | grep TrackPoint | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 1 && xinput list | grep Finger | awk '{print $7}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 1 
fi

if test normal = $status
then
xrandr -o inverted && xsetwacom list | grep stylus | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate half && xsetwacom list | grep eraser | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate half && xinput list | grep TouchPad | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 0 && xinput list | grep TrackPoint | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 0 && xinput list | grep Finger | awk '{print $7}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 0 
fi

##xrandr --output LVDS1 --rotate inverted
##xsetwacom list | grep stylus | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate half
##there is no touch in xsetwacom anymore:
##xsetwacom list | grep touch | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate half && 
##xsetwacom list | grep touch | awk '{print $7}' | xargs -Idevice xsetwacom set device Rotate none &&
```
I'm keeping some of the old commands there so that I can refer back to them later. Add this to an sh file and run it. I'll have to add more details to it later. You could of course add two more cases of rotated `left` and `right` if you use them.
	- If you just want to disable the touchpad, trackpad and touch screen without rotating the screen try the following:
```
#!/bin/bash
status=$(xinput list-props "SynPS/2 Synaptics TouchPad" | grep 'Device Enabled' | awk '{print $4}')
if test 0 = $status
then
xinput list | grep TouchPad | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 1 && xinput list | grep TrackPoint | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 1 && xinput list | grep Finger | awk '{print $7}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 1 
fi

if test 1 = $status
then
xinput list | grep TouchPad | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 0 && xinput list | grep TrackPoint | awk '{print $6}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 0 && xinput list | grep Finger | awk '{print $7}' | sed 's/^id=//' | xargs -Idevice xinput set-prop device "Device Enabled" 0 
fi
```

	- And of course I've added them to my .bashrc and set launchers for them to access them easily with mouse:
[![launchers](files/20150920/selection_001.png)](files/20150920/selection_001.png)
	- You can get the icon files from here:
[![rotate](files/20150920/rotate.jpg)](files/20150920/rotate.jpg) [![touch](files/20150920/touch.png)](files/20150920/touch.png)
