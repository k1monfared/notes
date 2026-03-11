# converting time to color

So, Danny pointed out this [website](http://whatcolourisit.scn9a.org/) and asked if one can write a script to do this on a computer. Here is what I came up with:
```

#!/bin/bash
while true
do
	#read time
	TIME=$(date +"%T") 

	#delete colons and add a pound sign to the begining
	COLOR=$(echo "$(echo $TIME | sed 's/://g')" | sed 's/^/#/') 

	#to change the background color I need to change it in the profile, so first I find the ID, here I'm acutally assuming there's only 1 ID
	MYID=$(dconf list /org/gnome/terminal/legacy/profiles:/ | sed '1d' | sed 's/\///g' ) 

	#this is where things need to be changed
	BAK=/org/gnome/terminal/legacy/profiles:/$MYID/background-color 

	#clear the terminal screen
	clear 
	#change the color of background
	dconf write $BAK "'$COLOR'" 

	#this is to center the text
	MyX=$(stty size | awk '{print $1}') #get the number of rows of terminal
	MyY=$(stty size | awk '{print $2}') #get the number of columns of terminal

	HalfX=$((($MyX)/2)) #divide the x by two
	HalfY=$((($MyY-5)/2)) #divide the y by 2. Here -5 is accounting for the half of the length of the stirng to be printed
	
	#puch the cursor to the middle of the screen
	tput cup $HalfX $HalfY
	#write time
	echo ${TIME}
	#push the cursor to the last line
	tput cup $MyX 0
	#wait for a second
	sleep 1
done

```

I bet one can make it look nicer :)
