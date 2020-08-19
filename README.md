
# Overview

This is a python markdown page framework generation called 'DYI Page'.

It is similar in principle to Hugo, or Jeckyll.

The program uses pandoc to generate entries. It has to be installed on the target machine.

There are three directories that are relevant:
- blog-md Markdown files directory.
- blog-html Output directory, where HTML files are generated.
- blog-template Templates directory

To create a page within the entry:
```
 python3 dyi-page.py -p "page name"
```

To create a new section for pages (a new directory for pages):
```
 python3 dyi-page.py -s "section name"
```

To convert markdown pages to html ones, just:
```
 python3 dyi-page.py
```

# TODO
Entries should be sorted:
- by time
- by name?
- by tag/category?

Add rss generation.
