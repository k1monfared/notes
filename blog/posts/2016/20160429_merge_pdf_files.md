---
tags: linux, pdf, terminal
---

# Merge PDF files

Try the good ghostscript:
```
gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile=merged.pdf mine1.pdf mine2.pdf

```
or even this way for an improved version for low resolution PDFs (thanks to Adriano for pointing this out):
```
gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress -sOutputFile=merged.pdf mine1.pdf mine2.pdf

```
In both cases the ouput resolution is much higher and better than this way using convert:
```
convert -density 300x300 -quality 100 mine1.pdf mine2.pdf merged.pdf

```
In this way you wouldn't need to install anything else, just work with what you already have installed in your system (at least both come by default in my rhel).

Source: [Stack Overflow](https://stackoverflow.com/questions/2507766/merge-convert-multiple-pdf-files-into-one-pdf#2507825)

---

## Old Comments

> **funkyfashion007** — June 16, 2016
> 
> This is so interesting, I love learning about math in the real world...coding included! :)
> https://mathsux.org/
