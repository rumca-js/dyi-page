
# Overview

This is a python markdown page framework generation called 'DYI Page'.

It is similar in principle to Hugo, or Jeckyll.

The program uses pandoc to generate entries. It has to be installed on the target machine.

There are three directories that are relevant:
- blog-md Source directory. Contains markdown files.
- blog-html Output directory. Contains output HTML files.
- blog-template Template files directory.

Entries from blog-md are processed, and:
- if this is .md file then HTML is generated for it
- if this is .template file, then first .md is generated from it, then HTML is generated for the .md file
- otherwise the file is copied to the HTML output directory

To create a new section for pages (a new directory for pages):
```
 python3 dyi-page.py -s "section name"
```

To create a page:
```
 python3 dyi-page.py -p "page name"
```

To create a page for a section:
```
 python3 dyi-page.py -p "page name" -s "section name"
```

To convert markdown pages to html ones, just:
```
 python3 dyi-page.py
```

To generate backup file:
```
 python3 dyi-page.py -b
```

# TODO
Add rss generation.
