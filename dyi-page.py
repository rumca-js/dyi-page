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
        # TODO add support for lists

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


    def get_file_name(self):
        return self._mdfile

    def get_html_file_name(self):
        file_name_only = self._mdfile[:-3]
        htmlfile = file_name_only.replace(markdown_dir, html_dir)+".html"
        return htmlfile

    def is_index(self):
        if self.get_file_name().find("index") == -1:
            return False

        return True


class MdFileTemplate(object):

    def __init__(self, template_file_name, mdfiles):
        self.template_file_name = template_file_name
        self.get_destination_name()

        self.set_html_file_names(mdfiles)
        self.read_pages()
        self.sort_pages()

        self.establish_variables()

    def get_destination_name(self):
        self.md_file_name = self.template_file_name[:self.template_file_name.find(".template")]
        return self.md_file_name

    def set_html_file_names(self, mdfiles):
        self.mdfiles = mdfiles
        #self.htmls = [x.replace(".md", ".html").replace(markdown_dir+"/", "") for x in mdfiles]

    def read_pages(self):
        self.pages = []
        for key, mdfile in enumerate(self.mdfiles):
            mdobj = MdFile(mdfile)
            if not mdobj.is_index():
                self.pages.append(mdobj)

    def sort_pages(self):
        self.pages = sorted(self.pages, key = lambda x : x.get_header_var('date'), reverse = True)

    def establish_variables(self):

        self.vars = {}

        file_entries = ""
        for key, mdobj in enumerate(self.pages):
            if not mdobj.is_index():
                title = mdobj.get_header_var("title")
                updated = mdobj.get_header_var("date")

                html_file_name = os.path.split(mdobj.get_html_file_name())[1]

                file_entries += "[{0}](./{1})\t{2}\n\n".format(title, html_file_name, updated)

        self.vars["${FILE_ENTRIES}"] = file_entries

    def write(self):
        template_data = self.read_template()

        with open(self.md_file_name, 'w') as bigfile:
            template_data = template_data.replace("${FILE_ENTRIES}", self.vars["${FILE_ENTRIES}"])
            bigfile.write(template_data)

    def read_template(self):
        template_index_file = self.template_file_name
        if os.path.isfile(template_index_file):
            with open(template_index_file, 'r') as fh:
                return fh.read()

        return ""


def process_directory(dir_to_process):
    mdfiles = glob.glob(dir_to_process+"/*.md")

    templates = glob.glob(dir_to_process+"/*.template")

    for atemplate in templates:
        templ = MdFileTemplate(atemplate, mdfiles)
        templ.write()


def generate_html_path(dir_to_process):
    dir_to_process = dir_to_process.replace(markdown_dir, html_dir)
    if not os.path.isdir(dir_to_process):
        os.makedirs(dir_to_process)


def process_file(afile):
    if afile.endswith(".md"):
        mdfile = afile
        mdobj = MdFile(mdfile)
        htmlfile = mdobj.get_html_file_name()
        logging.info("Converting {0} to {1}".format(mdfile, htmlfile))

        pan = Pandoc(mdfile, htmlfile)
        pan.convert()

    elif afile.endswith(".template"):
        pass

    else:
        dst_file = afile.replace(markdown_dir, html_dir)
        shutil.copy(afile, dst_file)


def convert():
    shutil.rmtree(html_dir)
    os.makedirs(html_dir)

    process_directory(markdown_dir)

    for root, dirs, files in os.walk(markdown_dir):
        for adir in dirs:
            process_directory( os.path.join(root, adir))
            generate_html_path( os.path.join(root, adir))

        files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
        for afile in files:
            process_file( os.path.join(root, afile))


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
    logging.basicConfig(level=logging.INFO)
    main()
