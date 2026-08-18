---
tags: linux, python, sage
---

# What to do with a long list?

I mean a list in SAGE. The answer is to
```
save(mylist, 'mylist')

```
and then later
```
mynewlist = load('mylist')

```
This will save your list into a file called `mylist.sobj` and then loads it. The story is I calculated a list through a long calculation to do some other calculations with it. So I saved the list in a .txt file and in the file it looks like this:
```
[[[-1/10, 1.02421477975960],
  [-99/1000, 1.02369404664481],
  [-49/500, 1.02317986236459],
  [-97/1000, 1.02267219319285],
  ...

```
But then that I needed to read it, I had to open the text file and copy and paste it into SAGE. If the list is short, I think it's an easy way to do it, but if the list is long (a few gigabytes maybe?) you don't want to open that text file, forget about copying it! So, one way to read it was to strip all the `\n`'s and get rid of the brackets and all the other things in a nice way and then read it as a csv file, which I could save it as a csv in the first place with:
```
import csv 
with open('mylist.csv', 'w') as f1:
    writefile = csv.writer(f1)
    writefile.writerows(mylist)

```
And then read it with
```
import csv 
with open('mylist.csv','rU') as f1:
    mynewlist =load('myfile')

```
The problem is I still had to go through the list and change strings to numbers. Something I really don't want to do. So, the save and load file is the best thing.
```
save(mylist, 'mylist')
mynewlist = load('mylist')

```
Resource: [AskSageMath](http://ask.sagemath.org/question/33179/whats-a-common-way-to-save-and-load-a-list/) community.
