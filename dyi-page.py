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

__version__ = '0.0.1'

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


class Pandoc(pypandoc.PyPandoc2Html):

    def __init__(self, mdfile, htmlfile):
        super().__init__()

        self._mdfile = mdfile
        self._htmlfile = htmlfile
        self._real = False

    def convert(self):
        if self._real:
            subprocess.run(['pandoc', '-s', '-c', 'pandoc.css', self._mdfile, '-o', self._htmlfile])
        else:
            self.convert2html(self._mdfile, self._htmlfile)

    def use_pandoc(self, use_pandoc):
        self._real = use_pandoc

    def get_html_header(self):
        return """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="Content-Style-Type" content="text/css" />
  <meta name="generator" content="pandoc" />
  <title>$PAGE_TITLE$</title>
  <style type="text/css">code{white-space: pre;}</style>
  <link rel="stylesheet" href="pandoc.css" type="text/css" />
</head>
<body>
<div id="header">
<h1 class="title">$PAGE_TITLE$</h1>
<h3 class="date">$PAGE_DATE$</h3>
</div>
    """

    def get_html_footer(self):
        data = "</p><p id=\"footer\">"
        data += "Generated using dyi-page {0}<br/>".format(__version__)
        data += "Generated using pypandoc {0}<br/>".format(pypandoc.__version__)
        data += "</p></body>\n</html>"
        return data

    def rss_generate(self):

        rss_entry = os.path.join(rss_entries_dir, 'rss_entry.xml.template')

        templ = TemplateFile( os.path.join(template_dir, 'rss_entry.xml.template'))
        templ.write(rss_entry)

        if self._real:
            subprocess.run(['pandoc','--template',rss_entry, self._mdfile, '-o', self._htmlfile])
        else:
            md = MdFile(self._mdfile)
            temp = TemplateFile( rss_entry)
            temp.keys.update(md.header)
            temp.write(self._htmlfile)


class MdFile(pypandoc.PyPandocDom):

    def __init__(self, mdfile):
        super().__init__(mdfile, True)

    def get_html_file_name(self):
        file_name_only = self.get_file_name()[:-3]
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
        self.keys["PAGE_DRAFT"] = "false"
        self.keys["DATETIME"] = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.keys["DATE"] = datetime.datetime.today().strftime('%Y-%m-%d')
        self.keys["TIME"] = datetime.datetime.today().strftime('%H:%M:%S')

    def write(self, new_file_name):
        data = ""
        with open(self.template_name, 'r', encoding='utf-8') as fh:
            data = fh.read()

        for key in self.keys:
            data = data.replace("${0}$".format(key), self.keys[key])

        with open(new_file_name, 'wb') as fh:
            fh.write(data.encode('utf-8') )

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
                key = lambda x : (x.header['date'], x.header['title'] ), 
                reverse = True)

    def establish_variables(self):

        file_entries = ""
        for key, mdobj in enumerate(self.pages):
            if not mdobj.is_index():
                title = mdobj.header["title"]
                updated = mdobj.header["date"]

                html_file_name = os.path.split(mdobj.get_html_file_name())[1]

                file_entries += " - [{0}](./{1})\n".format(title, html_file_name, updated)

        self.keys["FILE_ENTRIES"] = file_entries

        dir_entries = ""
        for adir in sorted(self.mddirs):
            title = adir
            if title.find("md_") == 0:
                title = title[3:]

            html_file_name = os.path.join(adir, "index.html")
            dir_entries += " - [{0}](./{1})\n".format(title, html_file_name)

        self.keys["DIR_ENTRIES"] = dir_entries


class RssFileCreator(object):

    def create_rss_file(self, file_name):
        big_rss_file = os.path.join(html_dir, file_name)

        logging.info("Generating RSS file {0}".format(big_rss_file))

        self.md_rss_files = self.get_md_entries()

        self.validate()

        xml_rss_files = self.create_xml_rss_entries(self.md_rss_files)

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

    def validate(self):
        for mdfile in self.md_rss_files:
            md = MdFile(mdfile)
            link = md.header['link']

            file_path = os.path.join(html_dir, link)
            if not os.path.isfile(file_path):
                raise IOError("{0}: The specified link does not exist {0}".format(mdfile, link))


def get_datetime_file_name():
    return datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')


def process_templates(dir_to_process):
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
        if mdobj.header['draft'].strip() != "true":
            htmlfile = mdobj.get_html_file_name()
            logging.info("Converting {0} to {1}".format(mdfile, htmlfile))

            pan = Pandoc(mdfile, htmlfile)
            pan.use_pandoc(use_pandoc)
            pan.convert()
        else:
            logging.info("Skipping draft {0}".format(mdfile))

    elif afile.endswith(".template"):
        pass

    else:
        dst_file = afile.replace(markdown_dir, html_dir)
        shutil.copy(afile, dst_file)


def convert(use_pandoc):
    shutil.rmtree(html_dir)
    os.makedirs(html_dir)

    process_templates(markdown_dir)

    for root, dirs, files in os.walk(markdown_dir):
        for adir in dirs:
            process_templates( os.path.join(root, adir))
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

    if page_name:
        if section_name:
            section_name = normalize_section_name(section_name)
            page_rss_link = section_name + "/" + page_name
        else:
            page_rss_link = page_name

        rss_entry_title = page_name
        rss_entry_link = page_rss_link + ".html"
        description = "Created a new page {0}".format(page_name)
    else:
        rss_entry_title = "New RSS entry"
        config = Configuration()
        rss_entry_link = config.page_url
        description = "New RSS entry"

    date = get_datetime_file_name()
    
    rss_md_file_name = date+".md"
    rss_md_template = os.path.join(template_dir, "rss_entry.md.template")
    rss_destination_file = os.path.join(rss_entries_dir, rss_md_file_name)

    temp = TemplateFile(rss_md_template)

    temp.set("RSS_ENTRY_TITLE", rss_entry_title)
    temp.set("RSS_ENTRY_LINK", rss_entry_link)
    temp.set("DESCRIPTION", description)

    temp.write( rss_destination_file)


def generate_new_page_inc(page_name, section_name = None, draft=False):
    full_section_name = section_name

    if section_name:
        section_name = normalize_section_name(section_name)
        dst_dir = os.path.join(markdown_dir, section_name)
    else:
        dst_dir = markdown_dir

    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    temp = TemplateFile(os.path.join(template_dir, 'page.md.template'))
    if draft:
        temp.set("PAGE_DRAFT", "true")

    if not page_name.endswith(".md"):
        page_name = page_name+".md"

    temp.write( os.path.join(dst_dir, page_name))

    if page_name.endswith(".md"):
        page_name = page_name[:-3]


def generate_new_page(page_name, section_name = None):
    generate_new_page_inc(page_name, section_name)

    create_new_rss_entry(page_name, section_name)


def generate_new_draft(page_name, section_name = None):
    generate_new_page_inc(page_name, section_name, True)


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
    parser.add_argument('-p', '--page', dest='generate_new_page', help='Creates new page with the specified name')
    parser.add_argument('-s', '--section', dest='generate_new_section', help='Creates new section with the specified name')
    parser.add_argument('-b', '--backup', dest='generate_backup', action="store_true", help='Creates backup file')
    parser.add_argument('-d', '--draft', dest='generate_new_draft', help='Creates draft page')
    parser.add_argument('-r', '--new-rss', dest='generate_rss_entry', action="store_true", help='Creates a new rss md file')
    parser.add_argument('-R', '--rss', dest='generate_rss', action="store_true", help='Creates output rss file')
    parser.add_argument('-P', '--pandoc', dest='use_pandoc', action="store_true", help='Uses pandoc for producing entries')

    args = parser.parse_args()

    return parser, args


def main():
    parser, args = read_arguments()

    if args.generate_new_section:
        if args.generate_new_page:
            generate_new_page(args.generate_new_page, args.generate_new_section)
        elif args.generate_new_draft:
            generate_new_draft(args.generate_new_draft, args.generate_new_section)
        else:
            generate_new_section(args.generate_new_section)
    
    elif args.generate_new_page:
        generate_new_page(args.generate_new_page)

    elif args.generate_new_draft:
        generate_new_draft(args.generate_new_draft)

    elif args.generate_backup:
        generate_backup()

    elif args.generate_rss:
        rss = RssFileCreator()
        rss.create_rss_file("rss.xml")

    elif args.generate_rss_entry:
        create_new_rss_entry(None, None)

    else:
        config = Configuration()
        if config.exists():
            convert(args.use_pandoc)
        else:
            config.create()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
