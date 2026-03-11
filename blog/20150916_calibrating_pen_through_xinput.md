# Calibrating pen through xinput

So, this is too long, I'm gonna just make a new post for it. When I connect the tablet to a projector, due to change of resolution the pen is not calibrated any more. I've tried `xinput_calibrator` to adjust it, but since it "auto-detect"s misclicks I can't really get it to work. I tried to turn it off using the option `--misclick 0`, but that also didn't work. The option `--precalib` doesn't get me anywhere.

Then I found this [wiki post from ArchLinux](https://wiki.archlinux.org/index.php/Calibrating_Touchscreen) and it does exactly what I need to do, except the numbers are a little off. For a discussion on this problem see the [SE post](http://unix.stackexchange.com/questions/229876/xinput-calibration-and-options) for the initial problem, and [this SE post](http://unix.stackexchange.com/questions/229908/calibrating-pen-and-touch-via-xinput) for the exact values.

Here is what I've done:

	- From `xrandr` I get:
```
Screen 0: minimum 8 x 8, current 1024 x 768, maximum 32767 x 32767
LVDS1 connected primary 1024x768+0+0 (normal left inverted right x axis y axis) 277mm x 156mm
   1366x768      60.02 +
   1280x720      60.00  
   1024x768      60.00* 
   1024x576      60.00  
   ...

```
The one with + is maximum resolution my monitor supports and the one with * is the current resolution. So, I conclude
```
total_width = 1024
touch_area_width = 1366
touch_area_x_offset = (1024 - 1366) /2 = -171
```
This is probably what I'm doing wrong, because at the end I don't get **exactly** what I need, but almost there.
	- Then I look at the output of `xinput list`
``
```
⎡ Virtual core pointer                        id=2    [master pointer  (3)]
⎜   ↳ Virtual core XTEST pointer                  id=4    [slave  pointer  (2)]
⎜   ↳ Logitech M325                               id=9    [slave  pointer  (2)]
**⎜   ↳ Wacom ISDv4 E6 Pen stylus                   id=10    [slave  pointer  (2)]**
**⎜   ↳ Wacom ISDv4 E6 Finger                       id=11    [slave  pointer  (2)]**
⎜   ↳ SynPS/2 Synaptics TouchPad                  id=13    [slave  pointer  (2)]
⎜   ↳ TPPS/2 IBM TrackPoint                       id=14    [slave  pointer  (2)]
**⎜   ↳ Wacom ISDv4 E6 Pen eraser                   id=16    [slave  pointer  (2)]**
⎣ Virtual core keyboard                       id=3    [master keyboard (2)]
    ↳ Virtual core XTEST keyboard                 id=5    [slave  keyboard (3)]
    ↳ Power Button                                id=6    [slave  keyboard (3)]
    ↳ Video Bus                                   id=7    [slave  keyboard (3)]
    ↳ Sleep Button                                id=8    [slave  keyboard (3)]
    ↳ AT Translated Set 2 keyboard                id=12    [slave  keyboard (3)]
    ↳ ThinkPad Extra Buttons                      id=15    [slave  keyboard (3)]
```
The bold lines are the ones that I need, so the `DEVICE NAME`s for me will be `"Wacom ISDv4 E6 Pen stylus"`, `"Wacom ISDv4 E6 Finger"`, and `"Wacom ISDv4 E6 Pen eraser"`.
	- `xinput list-props "device name" | grep Matrix` should list the current `Coordinate Transformation Matrix`. The default is the identity matrix which is listed by rows:
```
Coordinate Transformation Matrix (138):	1.000000, 0.000000, 0.000000, 0.000000, 1.000000, 0.000000, 0.000000, 0.000000, 1.000000
```

	- The transformation matrix is The matrix is
$\begin{bmatrix} c_0 & 0 & c_1 \\ 0 & c_2 & c_3 \\ 0 & 0 & 1\end{bmatrix}$You can see that when it's multiplied by the vector $\begin{bmatrix} x_1 \\ x_2 \\ 1\end{bmatrix}$ from left it produces $\begin{bmatrix} c_0 x_1 + c_1 \\ c_2 x_2 + c_3 \\ 1\end{bmatrix}$ which is just a scaling and shift on $x_1$ and $x_2$.
	- The tutorial says to calculate the matrix as follows:
```
$c_0$ = touch_area_width / total_width = 1366/1024 = 1.333984375
$c_2$ = touch_area_height / total_height = 768/768 = 1
$c_1$ = touch_area_x_offset / total_width = -171/768 = -0.22265625
$c_3$ = touch_area_y_offset / total_height = 0/768 = 0
```
The reason $c_2 = 1$ and $c_3 = 0$ for me is that in my situation the height is fine, so I only need to scale and shift the width.
	- All I need to do now is to represent my matrix as an array of rows, that is:
`c0 0 c1 0 c2 c3 0 0 1`
and that for me becomes:
`1.333984375 0 -0.22265625 0 1 0 0 0 1`
	- Then the following command should do the translation for me:
`xinput set-prop "DEVICE NAME" --type=float "Coordinate Transformation Matrix" 1.333984375 0 -0.22265625 0 1 0 0 0 1`
	- That almost gets me where I want to be except it's still a little off. So, I did a little bit of trial and error to get the following numbers and it's working quite well:
`xinput set-prop "DEVICE NAME" --type=float "Coordinate Transformation Matrix" 1.345 0 -0.17  0 1 0 0 0 1`
	- To do: I have to figure out how to find the exact values.
	- Final command that does it all for me in one line is:
`xinput set-prop "Wacom ISDv4 E6 Pen stylus" --type=float "Coordinate Transformation Matrix" 1.345 0 -0.17  0 1 0 0 0 1 && xinput set-prop "Wacom ISDv4 E6 Finger" --type=float "Coordinate Transformation Matrix" 1.345 0 -0.17  0 1 0 0 0 1 && xinput set-prop "Wacom ISDv4 E6 Pen eraser" --type=float "Coordinate Transformation Matrix" 1.345 0 -0.17  0 1 0 0 0 1`
	- And finally if you want to make a launcher for it, here is the one that I'm using:
[![calibrate](files/20150916/calibrate.png)](files/20150916/calibrate.png)
