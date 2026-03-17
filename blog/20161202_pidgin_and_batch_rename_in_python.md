---
tags: linux, python, shell
---

# Pidgin and batch rename in python

I remembered that I can use pidgin! I don't know what I haven't been using it for a while. But now that I've installed it again, I went and downloaded yahoo smilies (from [here](https://developer.pidgin.im/wiki/ThirdPartySmileyThemes)) and the according to [this page](https://developer.pidgin.im/wiki/SmileyThemes) I had to copy the unzipped file to `~/.purple/smileys` folder. Everything worked fine, expect since the file I downloaded had a bunch of files that were all named like `yahoo\26.gif` and that made pidgin not to recognize them! So I had to change them, but it seems like also shell doesn't like `\` in file names either. So I asked python to help me. Here is the code:
```
import os
directory = '/home/k1/.purple/smileys/yahoo/'
for filename in os.listdir(directory):
    if filename.startswith('yahoo'):
            print('renaming', filename)               
            os.rename(directory+filename, directory+filename[6:])

```
This deletes `yahoo\` part of each file that has it. In the `if` part I couldn't write `if filename.startswith('yahoo\'):` and if I wanted to be precise I had to write `if filename.startswith('yahoo\\'):`. Anyways, going to pidgin, tools, preferences, themes, I chose the yahoo smilies from the dropdown list.
The following is the info from the [mentioned page](https://developer.pidgin.im/wiki/SmileyThemes) above:

> # Smiley Themes
> ## Installing
> One important thing to remember is that these smileys only show up on your side. Unless the person you're talking to has the same theme as you installed in the same client, it's not guaranteed that they will see the same pictures as you for the smileys.
> 
> The way smiley themes work is quite simple. We'll use an example to explain how it works. The name of this theme will be "Hello World!".
> 
> If we wanted to install Hello World! into pidgin, we would have to do one of three things:
> 
> 	- Copy a folder, whose contents are described below, into <tt>~/.purple/smileys</tt> (See [the FAQ](https://developer.pidgin.im/wiki/Using%20Pidgin#Whereismy.purpledirectory) for the location of <tt>~/.purple</tt> on Windows)
> 	- Drag a tar.gz file (it must be a gzipped tarball), whose contents are described below, onto the list of smiley themes in Tools -> Preferences
> 	- Click the "Add" button in the "Smiley Themes" tab in the preferences, navigate to your <theme>.tar.gz file, and click "Open".
> 
> ## Creating
> The first thing you need to know is the contents of the tarball you drag into the smiley themes list. It contains the folder that is described in option 1 above. In our case, this folder would probably be called "Hello_World".
> 
> Now to describe the contents of Hello_World. This folder contains all the information Pidgin needs to use your theme. It has a lot of picture files that will be how your smileys show up (to you) and a text file named "theme", which tells pidgin what to do with all those pictures. For this example, lets let our list of picture files be:
> 
> 	- happy.png
> 	- sad.png
> 	- grin.png
> 	- hidden.png
> 	- MSN_only.gif
> 	- GoogleTalk.gif
> 
> Then let our theme file look like so:
> 
Name=Hello World!
> Description=Smiley Theme How-To
> Icon=happy.png
> Author=Ankit Singla
> 
> [default]
> ! hidden.png			C:-) C:)
> sad.png				:( :-(
> happy.png			:) :-)
> grin.png		:-D :-d
> 
> #These show up only in MSN
> [MSN]
> sad.png				:( :-(
> happy.png			:) :-)
> grin.png		:-D :-d
> MSN_only.gif	:-M :-$
> 
> #These show up only in XMPP
> [XMPP]
> sad.png				:( :-(
> happy.png			:) :-)
> grin.png		:-D :-d
> GoogleTalk		:-G :T
> </pre>
> Blank lines and lines that start with # are ignored. The # means this line is a comment. Lines starting with a ! means to hide that particular emoticon from the emoticon selector dialog.
> 
> The first four lines are part of any theme. The first line is the name of our theme, in our case "Hello World!". This shows up in the theme selector in bold. The second line is the description of our theme. This shows up underneath the name and author in the theme selector. The third line is the icon to show in the theme selector, which is a quick way for the user to see which theme they're selecting. The last line is the author of the theme. This shows up next to the name of the theme in the theme selector.
> 
> Next come the protocol specific sets of smileys. A set of smileys is defined in the following format:
> 
[<protocol>]
> <picture to use>	<text to replace>
> .
> .
> .
> </pre>
> For example:
> 
[MSN]
> sad.png				:( :-(
> happy.png			:) :-)
> grin.png		:-D :-d
> MSN_only.gif	:-M :-$
> </pre>
> This means, the first line defines which protocol this set defines. In our example, this set will define all of the MSN pictures. Each line after that specifies how to handle each picture you want to use in that protocol. The first element on this line is the name of the picture, so for our first picture, we have sad.png. This must be followed by some whitespace and then a list of strings, separated by whitespace, that will be replaced by the picture sad.png in conversation. So in our case, we're telling pidgin that if it ever sees ":(" or ":-(", it shouln't show us ":(" or ":-(". Instead, it should replace it with sad.png so we see that picture instead.
> 
> The first set defined in a theme file is usually the default set. This is the set of smileys that pidgin uses if it doesn't find a protocol specific set for that protocol in the rest of the file. So in our file, it will use the default set for AIM, ICQ, IRC, etc. If you notice, in the default set there's a line that starts with an exclamation point. This means the smiley is hidden. If someone types the text associated with that picture, you'll see the picture, but you won't be able to pick that smiley from the smiley selector that pops up from the formatting toolbar.
> 
> That's it! Congratulations, you know how to make a theme file.
