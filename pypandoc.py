
import re


__version__ = '0.0.1'


def find_matching_bracket(text, bracket_start, bracket_stop, pos=None, end=None):
    """
    if matching bracket can be found returns integer id of bracket
    otherwise returns None
    """
    stack = [] 

    if pos:
        _pos = pos
    else:
        _pos = 0

    if end:
        _end = end
    else:
        _end = len(text)

    string = text[_pos:_end]

    for key, i in enumerate(string):
        if i == bracket_start:
            stack.append(i)
        elif i == bracket_stop: 
            if len(stack) > 0:
                stack.pop()

                if len(stack) == 0:
                    return key+_pos
            else:
                return key+_pos


class PyPandoc(object):
    """
    @brief Suggesting
    https://www.tutorialspoint.com/python3/python_xml_processing.htm
    """

    HEADER = "Header"
    H1 = "Heading1"
    H2 = "Heading2"
    H3 = "Heading3"
    LINK = "Link"
    IMAGE = "Image"
    BREAK = "Break"
    CODE = "Code"
    PRE = "Pre"
    HR = "Hr"
    BOLD = "Bold"
    ITALIC = "Italic"
    BOLD_ITALIC = "BoldItalic"
    CHARACTERS = "char"
    LIST = "List"
    EMBED = "Embed"
    EMBED_YT = "EmbedYt"

    def __init__(self, file_name = None):
        self._file_name = file_name

        self._header = True
        self._header_cnt = 0

        self._list = False
        self._stop = False

        self._attr = {}

        self.stack = []

    def startElement(self, tag, attributes):
        print("Starting element: "+tag)

        print(attributes)

    def endElement(self, tag):
        print("Stopping element: "+tag)

    def characters(self, token):
        print("Characters: "+token.group(0) )

    def parse(self, file_name):
        self._file_name = file_name

        with open(self._file_name, 'r', encoding="utf-8") as fh:
            self._data = fh.read()

        self.parse_data()

    def parse_data(self, data = None):
        self._pos = 0
        self._prev_pos = self._pos

        if data:
            self._data = data

        token = self.read_token()
        while token:
            if self._stop:
                break

            self._prev_pos = self._pos

            if self._header:
                self.process_header(token)
            else:
                self.process_token(token)

            if self._pos == self._prev_pos:
                print(token.group(0) )
                print(self._data[self._pos-1])
                print(self._data[self._pos])
                print(self._data[self._pos+1])
                raise IOError("Token has not been processed")

            #self.shift_pos(token)
            token = self.read_token()

    def read_token(self, shift=None):
        pattern = re.compile("\S+")
        if shift is None:
            obj = pattern.search(self._data, self._pos)
        else:
            obj = pattern.search(self._data, self._pos+shift)

        return obj

    def prev_token(self):
        data = self._data[:self._pos]
        data = data[::-1]

        pattern = re.compile("\S+")
        obj = pattern.search(data)

        if obj:
            pos = obj.end()

            pattern = re.compile("\S+")
            obj = pattern.search(self._data, self._pos-pos)

            return obj

    def is_new_line_between_tokens(self, token_one, token_two):
        text = self._data[token_one.end(0) : token_two.start(0)]
        if text.find("\n") != -1:
            return True
        return False

    def is_token_first_in_line(self, token):
        prev_token = self.prev_token()

        if self._pos == 0:
            return True

        return self.is_new_line_between_tokens(prev_token, token)

    def is_token_alone_in_line(self, token):
        prev_token = self.prev_token()
        next_token = self.read_token(len(token.group()) )

        if self._pos == 0:
            return True

        prev_new_line = self.is_new_line_between_tokens(prev_token, token)

        if next_token:
            next_new_line = self.is_new_line_between_tokens(token, next_token)
        else:
            next_new_line = True

        if prev_new_line and next_new_line:
            return True
        else:
            return False

    def is_token_only_char(self, token, achar):
        text = set(token.group())
        allowed_chars = set(achar)
        if text.issubset(allowed_chars):
            return True
        return False

    def shift_pos(self, token):
        if token.end(0) > self._pos:
            self._pos = token.end(0)

    def process_header(self, token):
        if self.process_header_token(token):
            self._header = False

        if not self._header:
            self.process_whitespaces()

    def process_token(self, token):
        text = token.group(0)

        processed = False

        if self.is_token_alone_in_line(token):
            if len(token.group()) >= 3:
                if self.is_token_only_char(token, '#'):
                    self.process_hr(token, "#")
                    processed = True
                elif self.is_token_only_char(token, '-'):
                    self.process_hr(token, "-")
                    processed = True
                elif self.is_token_only_char(token, '*'):
                    self.process_hr(token, "*")
                    processed = True

        if self.is_token_first_in_line(token):
            if text.startswith("###"):
                if self.process_headings(token, '###'):
                    processed = True
            elif text.startswith("##"):
                if self.process_headings(token, '##'):
                    processed = True
            elif text.startswith("#"):
                if self.process_headings(token, '#'):
                    processed = True
            elif text.startswith("-"):
                if self.process_list(token):
                    processed = True
            elif text.startswith("*"):
                if self.process_list(token):
                    processed = True
            elif text.startswith("+"):
                if self.process_list(token):
                    processed = True

        if not processed:
            if text.startswith("!["):
                if self.process_embed(token, PyPandoc.IMAGE):
                    processed = True
            elif text.startswith("$["):
                if self.process_embed(token, PyPandoc.EMBED):
                    processed = True
            elif text.startswith("$YT["):
                if self.process_embed(token, PyPandoc.EMBED_YT):
                    processed = True
            elif text.startswith("["):
                if self.process_link(token):
                    processed = True
            elif text.startswith("```"):
                if self.process_enclosed_token(token, "```", PyPandoc.PRE):
                    processed = True
            elif text.startswith("`"):
                if self.process_enclosed_token(token, "`", PyPandoc.CODE):
                    processed = True
            elif text.startswith("***"):
                if self.process_enclosed_token(token, "***", PyPandoc.BOLD_ITALIC):
                    processed = True
            elif text.startswith("**"):
                if self.process_enclosed_token(token, "**", PyPandoc.BOLD):
                    processed = True
            elif text.startswith("*"):
                if self.process_enclosed_token(token, "*", PyPandoc.ITALIC):
                    processed = True
            else:
                self.process_characters(token)
                processed = True

        if not processed:
            if self.process_characters(token):
                processed = True

        if not self._header:
            self.process_whitespaces()

    def process_whitespaces(self):
        next_token = self.read_token()
        if next_token:
            leng = next_token.start()-self._pos
            if leng > 0:
                inner = self._data[self._pos:next_token.start()]

                self.process_text(inner)
        else:
            leng = len(self._data)-self._pos
            if leng > 0:
                inner = self._data[self._pos:]

                self.process_text(inner)

    def process_text(self, text):
        self.startElement(PyPandoc.CHARACTERS, {'text' : text})
        self.endElement(PyPandoc.CHARACTERS)
        self._pos += len(text)

    def process_characters(self, token):
        self.characters(token)
        self._pos = token.end()
        return True

    def process_big_break(self, inner_text):
        if self._list:
            self.endElement(PyPandoc.LIST)
            self._list = False

        self.startElement(PyPandoc.BREAK, {})
        self.endElement(PyPandoc.BREAK)

        self._pos = self._pos + len(inner_text)

    def process_enclosed_token(self, token, text, code):
        text_end_pos = self._data.find(text,token.start()+len(text) )
        if text_end_pos >= 0:
            token_text = self._data[token.start()+len(text):text_end_pos]

            self.startElement(code, {'text' : token_text })
            self.endElement(code)

            self._pos = text_end_pos + len(text)

            return True

        return False

    def process_hr(self, token, text):
        self.startElement(PyPandoc.HR, {'text' : token.group()})
        self.endElement(PyPandoc.HR)

        self._pos = token.end()

    def process_list(self, token):
        if self._list:
            self.endElement(PyPandoc.LIST)

        self.startElement(PyPandoc.LIST, {'text' : token.group(0),
                                         'list_type': token.group(0)[0] })

        self._list = True

        self._pos = token.end()

        return True

    def process_embed(self, token, tok_type):
        text = token.group(0)

        st0 = self._data.find("[", token.start(0))
        wh0 = find_matching_bracket(self._data, "[", "]", token.start(0))
        wh1 = self._data.find("(", wh0)
        wh2 = find_matching_bracket(self._data, "(", ")", wh1)

        if wh2 == None:
            return False

        text = self._data[token.start(0):wh2+1]
        name = self._data[st0+1:wh0]
        link = self._data[wh1+1:wh2]

        text = text.strip()
        name = name.strip()
        link = link.strip()

        self._attr = {}
        self._attr['text'] = text
        self._attr['name'] = name
        self._attr['link'] = link
        self._attr['type'] = tok_type

        self.startElement(tok_type, self._attr)
        self.endElement(tok_type)

        if wh2 >= 0:
            self._pos = wh2+1
            end_where = wh2+1

        return True

    def process_link(self, token):
        end_where = None

        text = token.group(0)

        wh0 = find_matching_bracket(self._data, "[", "]", token.start(0))
        wh1 = self._data.find("(", wh0)
        wh2 = find_matching_bracket(self._data, "(", ")", wh1)

        if wh2 == None:
            return False

        text = self._data[token.start(0):wh2+1]
        name = self._data[token.start(0)+1:wh0]
        link = self._data[wh1+1:wh2]

        text = text.strip()
        name = name.strip()
        link = link.strip()

        self._attr = {}
        self._attr['text'] = text
        self._attr['name'] = name
        self._attr['link'] = link

        self.startElement(PyPandoc.LINK, self._attr)

        pat = re.compile("\!\[")
        m = pat.search(self._data, token.start()+1, wh2)
        if m:
            self.process_embed(m, PyPandoc.IMAGE)

        self.endElement(PyPandoc.LINK)

        if wh2 >= 0:
            self._pos = wh2+1
            end_where = wh2+1

        return True

    def process_headings(self, token, level):
        text = token.group(0)

        wh = self._data.find("\n", token.end(0) )
        if wh >= 0:
            full_text = self._data[token.start(0):wh]
            self._pos = wh
        else:
            full_text = self._data[token.start(0):]

            self._pos = len(self._data)

        tt = re.search(level+"\s*", full_text)

        attributes = { 'text': full_text[tt.end():] }

        if text == "#":
            heading = PyPandoc.H1
        if text == "##":
            heading = PyPandoc.H2
        if text == "###":
            heading = PyPandoc.H3

        self.startElement( heading, attributes)
        self.endElement( heading)

        return True

    def process_header_token(self, token):
        text = token.group(0)

        if text == "---":
            self._header_cnt += 1

        if text == "---" and self._header_cnt > 1:
            self.startElement(PyPandoc.HEADER, self._attr)
            self.endElement(PyPandoc.HEADER)
            self._header = False
            self._pos = token.end()
            return True
        else:
            if self.is_token_first_in_line(token):
                key = self.get_header_key(token)
                value, end_place = self.get_header_value(token)

                self._attr[key] = value
                self._pos = end_place
            else:
                self._pos = token.end()

        return False

    def get_header_key(self, token):
        text = token.group(0)

        wh = text.find(":")
        if wh >= 0:
            self._pos = token.start() + wh+1
            return text[:wh]
        else:
            tok = self.read_token(token.end(0)-self._pos )
            if tok and tok.group(0) == ":":
                self._pos = tok.end()+1
                return text

    def get_header_value(self, token):
        next_token = self.read_token()
        end_place = None

        start_place = next_token.start(0)

        if next_token.group(0).startswith('"'):
            start_place += 1
            end_place = self._data.find('"', start_place)
        elif next_token.group(0).startswith("'"):
            start_place += 1
            end_place = self._data.find("'", start_place)
        elif next_token.group(0).startswith("["):
            start_place += 1
            end_place = self._data.find("]", start_place)
        else:
            end_place = self._data.find("\n", start_place)

        value = self._data[start_place: end_place]

        return value, end_place+1

    def get_file_name(self):
        return self._file_name

    def stop(self):
        self._stop = True


class PyPandocDom(PyPandoc):

    def __init__(self, mdfile, only_header=False):
        self.text = ""
        self.header = {}
        self.only_header = only_header

        super().__init__()

        self.parse(mdfile)

    def startElement(self, tag, attributes):
        if tag == PyPandoc.HEADER:
            self.header = attributes
        elif tag == PyPandoc.CHARACTERS:
            self.text += attributes['text']
        else:
            self.text += attributes['text']

    def endElement(self, tag):
        if tag == PyPandoc.HEADER and self.only_header:
            self.stop()

    def characters(self, token):
        """ TODO this should be text instead of token? """
        self.text += token.group(0)


class PyPandoc2Html(PyPandoc):

    def __init__(self):
        super().__init__()

        self._list = False
        self._link = False

        self._tag = None
        self._prev_tag = None
        self.embed_width = "500"
        self.embed_height = "400"

    def convert2html(self, from_file, to_file):
        self._fh = open(to_file, 'wb')

        self.parse(from_file)

        data = self.get_html_footer()
        self._fh.write(data.encode("utf-8"))

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
        data = "</p><p id=\"footer\">Generated using pypandoc {0}</p></body>\n</html>".format(__version__)
        return data

    def startElement(self, tag, attributes):

        if tag == PyPandoc.HEADER:

            title = attributes['title']
            date = attributes['date']

            header = self.get_html_header()

            header = header.replace("$PAGE_TITLE$",title)
            header = header.replace("$PAGE_TITLE$",title)
            header = header.replace("$PAGE_DATE$",date)

            self._fh.write(header.encode("utf-8"))

        elif tag == PyPandoc.BREAK:

            data = '</p><p>\n\n'
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.H1:

            text = attributes['text']
            data = '<h1>{0}</h1>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.LINK:
            self._link = True

        elif tag == PyPandoc.H2:

            text = attributes['text']
            data = '<h2>{0}</h2>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.H3:

            text = attributes['text']
            data = '<h3>{0}</h3>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.PRE:

            text = attributes['text']
            data = '<pre>{0}</pre>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.CODE:

            text = attributes['text']
            data = '<code>{0}</code>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.BOLD:

            text = attributes['text']
            data = '<strong>{0}</strong>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.ITALIC:

            text = attributes['text']
            data = '<em>{0}</em>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.BOLD_ITALIC:

            text = attributes['text']
            data = '<strong><em>{0}</em></strong>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.HR:

            text = attributes['text']
            data = '<hr>\n'
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.LIST:

            list_type = attributes['list_type']

            if self._list:
                if list_type == "*":
                    data = '</li><li class="list-mult">\n'
                elif list_type == "+":
                    data = '</li><li class="list-plus">\n'
                else:
                    data = '</li><li>\n'
            else:
                if list_type == "*":
                    data = '<ul class="list-mult"><li class="list-mult">\n'
                elif list_type == "+":
                    data = '<ul class="list-plus"><li class="list-plus">\n'
                else:
                    data = '<ul><li>\n'

            self._list = True
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.CHARACTERS:

            text = attributes['text']

            text = text.replace("\n\n", "</p><p>")
            text = text.replace("\r\n\r\n", "</p><p>")
            text = text.replace("\r\r", "</p><p>")

            data = '{0}'.format(text)

            if text.find("</p><p>") >= 0 and self._list:
                data += '</ul>\n'
                self._list = False

            self._fh.write(data.encode("utf-8"))

        else:
            None

            #print("Starting element: "+tag)
            #print(attributes)

            #data = "Starting element {0} {1}<br/>\n".format(tag, attributes)
            #self._fh.write(data.encode("utf-8"))

        self._prev_tag = self._tag
        self._tag = [tag, attributes]

    def endElement(self, tag):

        if tag != PyPandoc.CHARACTERS:
            #print("Stopping element: "+tag)
            None

        if tag == PyPandoc.LINK:

            if tag == self._tag[0]:
                link = self._tag[1]['link']
                name = self._tag[1]['name']
                data = '<a href="{0}">{1}</a>'.format(link, name)
                self._fh.write(data.encode("utf-8"))
            else:
                link_link = self._prev_tag[1]['link']
                img_link = self._tag[1]['link']
                data = '<a href="{0}"><img src="{1}"/></a>'.format(link_link, img_link)
                self._fh.write(data.encode("utf-8"))

            self._link = False

        elif tag == PyPandoc.IMAGE:

            if not self._link:
                link = self._tag[1]['link']
                name = self._tag[1]['name']
                data = '<img src="{0}" alt="{1}"/>'.format(link, name)
                self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.EMBED:
            link = self._tag[1]['link']
            name = self._tag[1]['name']
            ltype = self._tag[1]['type']
            data = """<iframe width="{0}" height="{1}" src="{2}"></iframe>""".format(self.embed_width, self.embed_height, link)
            self._fh.write(data.encode("utf-8"))

        elif tag == PyPandoc.EMBED_YT:
            link = self._tag[1]['link']
            name = self._tag[1]['name']
            ltype = self._tag[1]['type']
            data = """<iframe width="{0}" height="{1}" src="https://www.youtube.com/embed/{2}"></iframe>""".format(self.embed_width, self.embed_height, link)
            self._fh.write(data.encode("utf-8"))

        #data = "Stopping element {0}<br/>\n".format(tag)
        #self._fh.write(data.encode("utf-8"))
        pass

    def characters(self, token):
        data = token.group(0)
        self._fh.write(data.encode("utf-8"))
