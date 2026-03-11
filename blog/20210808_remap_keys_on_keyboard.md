# Remap keys on keyboard

[source: https://dev-loki.blogspot.com/2006/04/mapping-unsupported-keys-with-xmodmap.html]

On my keyboard I have two annoying keys right next to the arrow keys that go to previous/next page and I've always used them accidentally and have lost my drafts. Here is how I'm going to remap them so that they work as home/end buttons instead. The following command opens a window and captures all key presses on keyboard. 

xev | grep -A2 --line-buffered '^KeyRelease' | sed -n '/keycode /s/^.*keycode \([0-9]*\).* (.*, \(.*\)).*$/\1 \2/p'</pre>

If I press the two annoying buttons and the home and end buttons, this is what I get:

166 XF86Back
167 XF86Forward
110 Home
115 End</pre>

The plan is to map 166 to 110 and 167 to 115. Create a file at `~/.Xmodmap` and add the following lines to it:

keycode 166 = Home
keycode 167 = End</pre>

Or if you don't want them to do anything, map them to something like F13 and F14 which are usually non-existent.

Save the file and run the code: `xmodmap ~/.Xmodmap` and you are good to go. Add the line to your `~/.bashrc` and you don't need to repeat this ever (hmm, this requires a new bash session to be initiated before the mapping takes effect). You can add this as a cron job whenever your computer boots so that you don't need to open a terminal every time before you go on your merry way of browsing the internet etc:

- Run `crontab -e`- add the line to the end of the file: `@reboot xmodmap ~/.Xmodmap`- Save and exit and check if it is there: `crontab -l`

Or you could do it other ways: https://www.simplified.guide/linux/automatically-run-program-on-startup
