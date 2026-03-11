# TeXing with databases

It is happened to me many times that I have a database and I need to build multiple files PDF based on that database. Say, you have a list of people and their addresses and you want to send a generic letter to each of them with their names and addresses on it. Or you have a questionnaire online and you collect the responses in a single spreadsheet (like using google forms). And you want to generate a PDF file for the responses to each question. Here is how you can combine the power of $\LaTeX$ with some simple terminal commands to do this in a few minutes.

Here is how you can do it: http://tex.stackexchange.com/questions/157060/import-data-from-a-spreadsheet-into-latex-and-create-multiple-pdf-files-for-each?noredirect=1#comment359536_157060

You might need to do some tweaks though. For example change some characters, take care of 'new line's, add $ signs for math parts, etc.

And you'll need this package: http://web.mit.edu/jhawk/mnt/spo/tex-new/share/texmf/tex/latex/misc/textmerg.sty
