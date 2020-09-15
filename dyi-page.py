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
import zipfile
import datetime
import configparser

import pypandoc


html_dir = "blog-html"
markdown_dir = "blog-md"
template_dir = "blog-template"
rss_entries_dir = "blog-rss"
backup_dir = 'backup'


class Configuration(object):

    def __init__(self):

        self.config_file = "page_config.ini"

        if self.exists():
            self.read_config_file()
        else:
            self.page_url = "http://myserver.com/blog-html"
            self.page_title = "myserver - blog"
            self.page_description = 'myserver is a fun place to be'
            self.page_update_datetime = "Sun, Aug 16 2020"

    def exists(self):
        if os.path.isfile(self.config_file):
            return True
        return False

    def read_config_file(self):
        parser = configparser.ConfigParser()
        parser.read(self.config_file)

        self.page_url = parser['Page Info']['Page Url']
        self.page_title = parser['Page Info']['Page Title']
        self.page_description = parser['Page Info']['Page Description']
        self.page_update_datetime = parser['Page Info']['Page Update Time']

    def create(self):
        parser = configparser.ConfigParser()

        parser['Page Info'] = {'Page Url' : self.page_url,
                               'Page Title' : self.page_title,
                               'Page Description' : self.page_description,
                               'Page Update Time' : self.page_update_datetime}

        with open(self.config_file, 'w', encoding='utf-8') as fh:
            parser.write(fh)

        logging.info("Created page configuration file {0}. Please fill in the page details".format(self.config_file))


class Pandoc(object):

    def __init__(self, mdfile, htmlfile):
        self._mdfile = mdfile
        self._htmlfile = htmlfile
        self._real = False

    def convert(self):
        if self._real:
            subprocess.run(['pandoc', '-s', '-c', 'pandoc.css', self._mdfile, '-o', self._htmlfile])
        else:
            pypandoc.Panda2Html(self._mdfile, self._htmlfile)

    def use_pandoc(self, use_pandoc):
        self._real = use_pandoc

    def rss_generate(self):

        rss_entry = os.path.join(rss_entries_dir, 'rss_entry.xml.template')

        templ = TemplateFile( os.path.join(template_dir, 'rss_entry.xml.template'))
        templ.write(rss_entry)

        config = Configuration()

        subprocess.run(['pandoc','--template',rss_entry, self._mdfile, '-o', self._htmlfile])


class MdFile(object):

    def __init__(self, mdfile):
        self._mdfile = mdfile

        with open(self._mdfile, 'r', encoding='utf8') as fh:
            self._data = fh.read()

        if self._data.find("\r\n") >= 0:
            raise IOError("The file contains Windows encoding")

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


class TemplateFile(object):

    def __init__(self, template_name):
        self.template_name = template_name

        self.keys = {}

        config = Configuration()

        self.keys["PAGE_TITLE"] = config.page_title
        self.keys["PAGE_URL"] = config.page_url
        self.keys["PAGE_DESCRIPTION"] = config.page_description
        self.keys["PAGE_UPDATE_DATETIME"] = config.page_update_datetime
        self.keys["DATETIME"] = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.keys["DATE"] = datetime.datetime.today().strftime('%Y-%m-%d')
        self.keys["TIME"] = datetime.datetime.today().strftime('%H:%M:%S')

    def write(self, new_file_name):
        data = ""
        with open(self.template_name, 'r', encoding='utf-8') as fh:
            data = fh.read()

        for key in self.keys:
            data = data.replace("${0}$".format(key), self.keys[key])

        with open(new_file_name, 'w', encoding='utf-8') as fh:
            fh.write(data)

    def set(self, key, value):
        self.keys[key] = value


class MdFileTemplate(TemplateFile):

    def __init__(self, template_file_name, mdfiles, mddirs):
        super().__init__(template_file_name)

        self.get_destination_name()

        self.mdfiles = mdfiles
        self.mddirs = mddirs

        self.read_pages()
        self.sort_pages()

        self.establish_variables()

    def get_destination_name(self):
        self.md_file_name = self.template_name[:self.template_name.find(".template")]
        return self.md_file_name

    def read_pages(self):
        self.pages = []
        for key, mdfile in enumerate(self.mdfiles):
            mdobj = MdFile(mdfile)
            if not mdobj.is_index():
                self.pages.append(mdobj)

    def sort_pages(self):
        self.pages = sorted(self.pages, 
                key = lambda x : (x.get_header_var('date'), x.get_header_var('title') ), 
                reverse = True)

    def establish_variables(self):

        file_entries = ""
        for key, mdobj in enumerate(self.pages):
            if not mdobj.is_index():
                title = mdobj.get_header_var("title")
                updated = mdobj.get_header_var("date")

                html_file_name = os.path.split(mdobj.get_html_file_name())[1]

                file_entries += "[{0}](./{1})\t{2}\n\n".format(title, html_file_name, updated)

        self.keys["FILE_ENTRIES"] = file_entries

        dir_entries = ""
        for adir in sorted(self.mddirs):
            title = adir
            if title.find("md_") == 0:
                title = title[3:]

            html_file_name = os.path.join(adir, "index.html")
            dir_entries += "[{0}](./{1})\n\n".format(title, html_file_name)

        self.keys["DIR_ENTRIES"] = dir_entries


class RssFileCreator(object):

    def create_rss_file(self, file_name):
        big_rss_file = os.path.join(html_dir, file_name)

        logging.info("Generating RSS file {0}".format(big_rss_file))

        md_rss_files = self.get_md_entries()

        xml_rss_files = self.create_xml_rss_entries(md_rss_files)

        xml_rss_files = self.get_xml_entries()
        xml_rss_files = sorted(xml_rss_files)

        rss_entries_data = self.get_xml_rss_entries_data(xml_rss_files)

        big_rss_template = os.path.join(template_dir, "rss_main.template")
        temp = TemplateFile(big_rss_template)
        temp.set("RSS_ENTRIES", rss_entries_data)

        temp.write(big_rss_file)

        self.remove_xml_entries()

    def get_md_entries(self):
        return glob.glob( os.path.join(rss_entries_dir, "*.md"))

    def get_xml_entries(self):
        return glob.glob( os.path.join(rss_entries_dir, "*.xml"))

    def get_xml_rss_entries_data(self, xml_rss_files):
        rss_entries_data = ""
        for xml_file in xml_rss_files:
            with open(xml_file, 'r', encoding='utf-8') as fh:
                rss_entries_data += fh.read()
        return rss_entries_data

    def create_xml_rss_entries(self, files):
        files = sorted(files)

        for afile in files:
            pan = Pandoc( afile, afile+'.xml')
            pan.rss_generate()

    def remove_xml_entries(self):
        # remove unwanted entries XML entries
        files = glob.glob( os.path.join(rss_entries_dir, "*.xml"))
        for afile in files:
            os.remove(afile)


def get_datetime_file_name():
    return datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')


def process_directory(dir_to_process):
    mdfiles = glob.glob(dir_to_process+"/*.md")
    mddirs = glob.glob(dir_to_process+"/md_*")

    templates = glob.glob(dir_to_process+"/*.template")

    mddirs = [x.replace(dir_to_process+os.sep,"") for x in mddirs]

    for atemplate in templates:
        templ = MdFileTemplate(atemplate, mdfiles, mddirs)
        templ.write(templ.get_destination_name() )


def generate_html_path(dir_to_process):
    dir_to_process = dir_to_process.replace(markdown_dir, html_dir)
    if not os.path.isdir(dir_to_process):
        os.makedirs(dir_to_process)


def process_file(afile, use_pandoc):
    if afile.endswith(".md"):
        mdfile = afile
        mdobj = MdFile(mdfile)
        htmlfile = mdobj.get_html_file_name()
        logging.info("Converting {0} to {1}".format(mdfile, htmlfile))

        pan = Pandoc(mdfile, htmlfile)
        pan.use_pandoc(use_pandoc)
        pan.convert()

    elif afile.endswith(".template"):
        pass

    else:
        dst_file = afile.replace(markdown_dir, html_dir)
        shutil.copy(afile, dst_file)


def convert(use_pandoc):
    shutil.rmtree(html_dir)
    os.makedirs(html_dir)

    process_directory(markdown_dir)

    for root, dirs, files in os.walk(markdown_dir):
        for adir in dirs:
            process_directory( os.path.join(root, adir))
            generate_html_path( os.path.join(root, adir))

        files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
        for afile in files:
            process_file( os.path.join(root, afile), use_pandoc)

    rss = RssFileCreator()
    rss.create_rss_file("rss.xml")


def normalize_section_name(section_name):
    if not section_name.find("md_") == 0:
        section_name = "md_"+section_name
    return section_name


def generate_new_section(section_name):
    section_name = normalize_section_name(section_name)

    dst_dir = os.path.join( markdown_dir, section_name)

    if os.path.isdir(dst_dir):
        logging.info("Directory already exists: {0}".format(dst_dir))
        return

    os.makedirs(dst_dir)

    shutil.copy( os.path.join(template_dir, 'index.md.template'), dst_dir)
    shutil.copy( os.path.join(template_dir, 'pandoc.css'), dst_dir)


def create_new_rss_entry(page_name, section_name):
    section_name = normalize_section_name(section_name)

    date = get_datetime_file_name()
    
    rss_md_file_name = date+".md"

    rss_md_template = os.path.join(template_dir, "rss_entry.md.template")

    temp = TemplateFile(rss_md_template)

    rss_destination_file = os.path.join(rss_entries_dir, rss_md_file_name)

    if section_name:
        page_rss_link = section_name + "/" + page_name
    else:
        page_rss_link = page_name

    temp.set("PAGE_ENTRY_TITLE", page_name)
    temp.set("PAGE_ENTRY_LINK", page_rss_link+".html")
    temp.set("DESCRIPTION", "Created a new page {0}".format(page_name))

    temp.write( rss_destination_file)


def generate_new_page(page_name, section_name = None):
    full_section_name = section_name

    if section_name:
        section_name = normalize_section_name(section_name)
        dst_dir = os.path.join(markdown_dir, section_name)
    else:
        dst_dir = markdown_dir

    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    temp = TemplateFile(os.path.join(template_dir, 'page.md.template'))

    if not page_name.endswith(".md"):
        page_name = page_name+".md"

    temp.write( os.path.join(dst_dir, page_name))

    if page_name.endswith(".md"):
        page_name = page_name[:-3]

    create_new_rss_entry(page_name, full_section_name)


def generate_backup():
    date = get_datetime_file_name()

    zip_file_name = os.path.join(backup_dir, date+'_backup.zip')

    ziph = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(markdown_dir):
        for afile in files:
            ziph.write(os.path.join(root, afile))

    for root, dirs, files in os.walk(html_dir):
        for afile in files:
            ziph.write(os.path.join(root, afile))

    for root, dirs, files in os.walk(template_dir):
        for afile in files:
            ziph.write(os.path.join(root, afile))

    for root, dirs, files in os.walk(rss_entries_dir):
        for afile in files:
            ziph.write(os.path.join(root, afile))

    ziph.close()


def read_arguments():
    parser = argparse.ArgumentParser(description='DYI Page generator.')
    parser.add_argument('-p', '--page', dest='generate_new_page', help='Generates new page with the specified name')
    parser.add_argument('-s', '--section', dest='generate_new_section', help='Generates new section with the specified name')
    parser.add_argument('-b', '--backup', dest='generate_backup', action="store_true", help='Generates backup file')
    parser.add_argument('-r', '--rss', dest='generate_rss', action="store_true", help='Generates rss file')
    parser.add_argument('-P', '--pandoc', dest='use_pandoc', action="store_true", help='Uses pandoc for producing entries')

    args = parser.parse_args()

    return parser, args


def main():
    parser, args = read_arguments()

    if args.generate_new_section:
        if args.generate_new_page:
            generate_new_page(args.generate_new_page, args.generate_new_section)
        else:
            generate_new_section(args.generate_new_section)

    elif args.generate_new_page:
        generate_new_page(args.generate_new_page)

    elif args.generate_backup:
        generate_backup()

    elif args.generate_rss:
        rss = RssFileCreator()
        rss.create_rss_file("rss.xml")

    else:
        config = Configuration()
        if config.exists():
            convert(args.use_pandoc)
        else:
            config.create()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
