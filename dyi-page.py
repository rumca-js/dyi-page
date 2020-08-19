"""
@name DYI-page
@author rozbujnik
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
template_dir = "blog-template"


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


class MdFileIndex(object):

    def __init__(self, index_file_name, mdfiles):
        self.index_file_name = index_file_name
        self.mdfiles = mdfiles
        self.htmls = [x.replace(".md", ".html").replace(markdown_dir+"/", "") for x in mdfiles]

    def write(self):
        template_data = self.read_template()
        dynamic_data = ""

        with open(self.index_file_name, 'w') as bigfile:

            for key, mdfile in enumerate(self.mdfiles):
                if mdfile.find("index") == -1:
                    mdobj = MdFile(mdfile)
                    title = mdobj.get_header_var("title")
                    updated = mdobj.get_header_var("date")
                    dynamic_data += "[{0}](./{1})\t{2}\n\n".format(title, self.htmls[key], updated)

            template_data = template_data.replace("${FILE_ENTRIES}", dynamic_data)

            bigfile.write(template_data)

    def read_template(self):
        template_index_file = self.index_file_name + ".template"
        if os.path.isfile(template_index_file):
            with open(template_index_file, 'r') as fh:
                return fh.read()

        return ""


def generate_index(dir_to_process):
    mdfiles = glob.glob(dir_to_process+"/*.md")

    index_file = MdFileIndex( os.path.join(dir_to_process, 'index.md') , mdfiles)
    index_file.write()


def generate_html_path(dir_to_process):
    dir_to_process = dir_to_process.replace(markdown_dir, html_dir)
    if not os.path.isdir(dir_to_process):
        os.makedirs(dir_to_process)


def process_file(afile):
    if afile.endswith(".md"):
        fname_only = afile[:-3]
        mdfile = afile
        htmlfile = fname_only.replace(markdown_dir, html_dir)+".html"
        logging.info("Converting {0} to {1}".format(mdfile, htmlfile))

        pan = Pandoc(mdfile, htmlfile)
        pan.convert()

    elif afile.endswith(".template"):
        pass

    else:
        dst_file = afile.replace(markdown_dir, html_dir)
        shutil.copy(afile, dst_file)


def convert():
    # TODO walk over markdown directory and process all directories

    shutil.rmtree(html_dir)
    os.makedirs(html_dir)

    generate_index(markdown_dir)
    #generate_htmls_for_dir(markdown_dir)

    for root, dirs, files in os.walk(markdown_dir):
        for adir in dirs:
            generate_index( os.path.join(root, adir))
            generate_html_path( os.path.join(root, adir))

        files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
        for afile in files:
            process_file( os.path.join(root, afile))
            #generate_htmls_for_dir(os.path.join(root, adir))


def read_arguments():
    parser = argparse.ArgumentParser(description='DYI Page generator.')
    parser.add_argument('-p', '--page', dest='generate_new_page', help='Generates new page with the specified name')
    parser.add_argument('-s', '--section', dest='generate_new_section', help='Generates new section with the specified name')

    args = parser.parse_args()

    return parser, args


def generate_new_section(section_name):
    dst_dir = os.path.join( markdown_dir, section_name)

    if os.path.isdir(dst_dir):
        logging.info("Directory already exists: {0}".format(dst_dir))
        return

    os.makedirs(dst_dir)

    shutil.copy( os.path.join(template_dir, 'index.md.template'), dst_dir)
    shutil.copy( os.path.join(template_dir, 'pandoc.css'), dst_dir)


def generate_new_page(page_name, section_name = None):
    dst_dir = os.path.join(markdown_dir, section_name)

    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    shutil.copy( os.path.join(template_dir, 'page.md'), os.path.join(dst_dir))

    if not page_name.endswith(".md"):
        page_name = page_name+".md"

    os.rename( os.path.join(dst_dir, 'page.md'), os.path.join(dst_dir, page_name))


def main():
    parser, args = read_arguments()

    if args.generate_new_section:
        if args.generate_new_page:
            generate_new_page(args.generate_new_page, args.generate_new_section)
        else:
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
