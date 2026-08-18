---
tags: linux, windows
---

# Things to do on a windows machine

And while I'm at it, let me get this post started. A lot of times it happens that I have to work on a windows machine for a period of time. While I'm still trying to figure out how to get rid of the annoying obligatory update which breaks the computer each time, I use some apps that do the basic things for me. Here are a few (I'll add more as I go):

	- There is a directory of all free softwares available here: [FSF](http://directory.fsf.org/wiki/Main_Page)
	- You can install tons of KDE software on windows: [https://windows.kde.org](https://windows.kde.org), for example you can install okular for reading pdf files and annotating them.
	- [Light Screen](http://lightscreen.com.ar/) is a nice screen capturing app. It provides a simple taskbar icon and it has the ability to copy the captured area of the screen directly to the clipboard, so I can paste it in whatever app I use (usualy Journal). On a Linux machine I prefer to use [shutter](http://shutter-project.org/downloads/). It is light and it provides much more.
	- [MS Journal](https://en.wikipedia.org/wiki/Windows_Journal) in my opinion is the only app by microsoft that's not only worth working with, also it satisfies me. I take all my notes with it when I'm on a windows machine, and its linux clown [xournal](http://xournal.sourceforge.net) is comparable to it, and in many cases much better.
	- Firefox plays the the HTML5 and flash content automatically. To stop that I did several things that I'm not sure which one helped. But here is a list of all of them:

	<li>Install `adobe falsh plugin` from adobe's site (this is ironic but I need it to access the shockwave options)
	- In `about:config` set the followings:

	<li>`plugins.click_to_play` to `true`
	- `media.windows-media-foundation.enabled` to `false`
	- `media.autoplay.enabled` to `false`

</li>
	- In `about:addons` set the Shockwave flash to `ask to activate`
This will result in firefox asking you to allow flash content to be played each time. So if you allowed it and then it started to keep autoplaying those content again click on the icon on the left side of the URL and go to permissions tab and fix the permissions.

</li>
	- For compiling tex files I use [MikTex](http://www.miktex.org/download). Don't forget to install [updates ](http://www.miktex.org/howto/update-miktex)after installation.
	- For editing tex files I prefer [TexMaker](http://www.xm1math.net/texmaker/download.html), since I also use it on my Linux. It also comes with a portable version. It's dark theme is also very comfortable.
	- [Notepad++](https://notepad-plus-plus.org/) for the win.
