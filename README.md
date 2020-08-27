
# Overview

This is a python markdown page framework generation called 'DYI Page'.

It is similar in principle to Hugo, or Jeckyll.

At the very first time of run dyi-page.py, without any arguments it creates a configuration file.

Please set the page data, which will be used later on during page generation, like page title, etc. The page configuration file is named 'page_config.ini'.

# Prerequisites

The program uses pandoc to generate entries. It has to be installed on the target machine.

# Functionality

There are three directories that are relevant:
- blog-md Source directory. Contains markdown files.
- blog-html Output directory. Contains output HTML files.
- blog-template Template files directory.
- blog-rss RSS markdown entry files
- backup The backup directory, where the backup data is placed. All the directories above are zipped and put into a backup file.

Entries from blog-md are processed, and:
- if this is .md file then HTML is generated for it
- if this is .template file, then first .md is generated from it, then HTML is generated for the .md file
- otherwise the file is copied to the HTML output directory

The rss.xml file is generated in the blog-html directory.

# CLI

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
create an rss template file.
The RSS structure is baked in the python file.
The url needs to be put into some sort of configuration file.
It is baked into the python file as well.
