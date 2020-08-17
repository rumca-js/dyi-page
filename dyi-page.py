"""
@name MarkdownPagesFramework
@author Piotr Zieliński
@e-mail rozbujnik@gmail.com

@description
This is a markdown pages framework. You can write your own pages in blog-md directory. The pages are converted into blog-html directory.
A index.html file is also generated.

The pages need to have a 'md' extension.
"""

import os
import subprocess
import shutil
import glob
import logging
import argparse


html_dir = "blog-html"
markdown_dir = "blog-md"


class Pandoc(object):

    def __init__(self, mdfile, htmlfile):
        self._mdfile = mdfile
        self._htmlfile = htmlfile

    def convert(self):
        subprocess.run(['pandoc', '-s', '-c', 'pandoc.css', self._mdfile, '-o', self._htmlfile])


class MdFile(object):

    def __init__(self, mdfile):
        self._mdfile = mdfile

        with open(self._mdfile, 'r') as fh:
            self._data = fh.read()

    def get_header_var(self, variable_name):
        variable_delim = ":"
        wh1 = self._data.find(variable_name + variable_delim)
        if wh1 != -1:
            wh2 = self._data.find('"', wh1)
            wh2a = self._data.find("\n", wh1)

            if wh2 < wh2a:
                wh3 = self._data.find('"', wh2+1)
                return self._data[wh2+1:wh3]
            else:
                wh2 = self._data.find("\n", wh1)
                return self._data[wh1+len(variable_name+variable_delim):wh2]


class IndexFile(object):

    def __init__(self, index_file_name, mdfiles):
        self.index_file_name = index_file_name

        htmls = [x.replace(".md", ".html").replace(markdown_dir+"/", "") for x in mdfiles]

        template_data = self.read_template()
        dynamic_data = ""

        with open(index_file_name, 'w') as bigfile:

            for key, mdfile in enumerate(mdfiles):
                if mdfile.find("index") == -1:
                    mdobj = MdFile(mdfile)
                    title = mdobj.get_header_var("title")
                    updated = mdobj.get_header_var("date")
                    dynamic_data += "[{0}](./{1}/{2})\t{3}\n\n".format(title, html_dir, htmls[key], updated)

            template_data = template_data.replace("${FILE_ENTRIES}", dynamic_data)

            bigfile.write(template_data)

    def redistribute(self):
        pan = Pandoc(self.index_file_name, "index.html")
        pan.convert()

    def read_template(self):
        template_index_file = self.index_file_name + ".template"
        if os.path.isfile(template_index_file):
            with open(template_index_file, 'r') as fh:
                return fh.read()

        return ""


def convert():
    logging.info("Converting pages")

    files = os.listdir(markdown_dir)

    mdfiles = [os.path.join('./', markdown_dir, x) for x in files]

    index_file = IndexFile('./{0}/index.md'.format(markdown_dir), mdfiles)

    files = glob.glob(markdown_dir+"/*.md")

    for mdfile in files:
        fname_only = os.path.splitext(mdfile)[0]
        htmlfile = fname_only.replace(markdown_dir, html_dir) + ".html"
        logging.info("Converting {0} to {1}".format(mdfile, htmlfile))

        pan = Pandoc(mdfile, htmlfile)
        pan.convert()

    index_file.redistribute()


def read_arguments():
    parser = argparse.ArgumentParser(description='DYI Page generator.')
    parser.add_argument('-p', '--page', dest='generate_new_page', help='Generates new page with the specified name')
    parser.add_argument('-s', '--section', dest='generate_new_section', help='Generates new section with the specified name')

    args = parser.parse_args()

    return parser, args


def generate_new_section(section_name):
    logging.info("Generate new section")


def generate_new_page(page_name):
    logging.info("Generate new page")


def main():
    parser, args = read_arguments()

    if args.generate_new_section:
        generate_new_section(args.generate_new_section)

    elif args.generate_new_page:
        generate_new_page(args.generate_new_page)

    else:
        convert()


if __name__ == "__main__":
    #FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(level=logging.INFO) #, format=FORMAT)

    # execute only if run as a script
    main()
