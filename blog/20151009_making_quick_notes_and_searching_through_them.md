# Making quick notes and searching through them

There are several times that I just want to jot down something and I don't have time to open a note, or I don't want it to get lost somewhere, or I don't want to decide where to save the file and what to call it. So I have the following little script does the job for me. I called it quicknote and assigned a short alias to it in my .bashrc: `alias n='~/opt/quicknote'`.
```
#!/bin/sh
## date format ##
NOW=$(date +"%F")
NOWT=$(date +"%T")

## path and file ##
BAK="~/Dropbox/Drafts"
FILE="$BAK/qnote-$NOW-$NOWT"

input=$*
echo "$input" >> "$FILE"
```
So, what this does is it takes whatever one line input that I have and puts it in a file in a folder in my dropbox folder with names qnote-CURRENT_DATE-DURENT_TIME.

But sometimes I actally want to write a real note with multiple lines, but still I don't want to decide where to put it and what to call it. So I have another script that makes a file named note-CURRENT_DATE-CURRENT_TIME, and puts it in that folder in my dropbox, then opens a text editor for me to edit it. Here it is:
```
#!/bin/sh

## date format ##
DATE=$(date +"%F")
TIME=$(date +"%T")
 
## Backup path ##
BAK="~/Dropbox/Drafts"
FILE="$BAK/note$DATE-$TIME"

gedit $FILE
```
So far so good, but the problem is, now I don't know what's in what file. So I just use grep to search for keywords. It might not be very fun to set up all the things for the grep command each time you want to run it for this specific task. So, here goes another little script, which I save it in a file called drafts.
```
#!/bin/bash

if [[ $(echo $*) ]]; then
    searchterm="$*"
else
    read -p "Enter your search term: " searchterm
fi

searchterm=$(echo $searchterm | sed -e 's/\ /+/g')

egrep -r -I -i -H "$searchterm" ~/Dropbox/Drafts/* --color

```
The good things about using this routine than just `input=$*` is that I can just run `drafts`, and then it asks me to enter my search words, in this case, if I want to search for either of two words I can use `word1 | word2`. Of course I could just run `drafts word1 \| word2` and it would do the same thing. Any ways, this will get my work done.

ToDo: I should sit and read Sed and Awk once. Maybe on the flights this January :D
