import re


def find_matching_bracket(text, bracket_start, bracket_stop, pos=None, end=None):
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


class StackInfo(object):

    HEADER = 0
    HEADING = 1
    LINK = 2
    IMAGE = 3

    def __init__(self, atype):
        self._type = atype
        self._attr = {}
        self._text = ""

    def add_attr(self, key, value):
        self._attr[key] = value

    def add_text(self, text):
        self._text.append(text)


class MyPanda(object):
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
    CHARACTERS = "char"
    LIST = "List"

    def __init__(self, file_name = None):
        self._file_name = file_name

        self._header = False
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
            self.process_token(token)
            if self._pos == self._prev_pos:
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

    def is_token_first_in_line(self, token):
        prev_token = self.prev_token()

        if self._pos == 0:
            return True

        text = self._data[prev_token.start(0) : token.start(0)]
        if text.find("\n") != -1:
            return True
        return False

    def shift_pos(self, token):
        if token.end(0) > self._pos:
            self._pos = token.end(0)

    def process_token(self, token):
        text = token.group(0)

        #print("'{0}'".format(text))

        if self._header:
            self.process_header(token)

            if not self._header:
                self.process_whitespaces()
        else:
            #print("Token: "+text)
            processed = False
            if self.is_token_first_in_line(token):
                if text == "---":
                    self.process_header(token)
                    processed = True
                elif text.startswith("###"):
                    self.process_headings(token, '###')
                    processed = True
                elif text.startswith("##"):
                    self.process_headings(token, '##')
                    processed = True
                elif text.startswith("#"):
                    self.process_headings(token, '#')
                    processed = True
                elif text.startswith("-"):
                    self.process_list(token)
                    processed = True

            if not processed:
                if text.startswith("!["):
                    self.process_image(token)
                elif text.startswith("["):
                    self.process_link(token)
                else:
                    self.process_characters(token)

            if not self._header:
                self.process_whitespaces()

    def process_whitespaces_s(self):
        next_token = self.read_token()
        if next_token:
            leng = next_token.start()-self._pos
            if leng > 0:
                inner = self._data[self._pos:next_token.start()]

                if inner.find("\n\n") >= 0:
                    self.process_big_break(inner)
        else:
            leng = len(self._data)-self._pos
            if leng > 0:
                inner = self._data[self._pos:]
                if inner.find("\n\n") >= 0:
                    self.process_big_break(inner)

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
        self.startElement(MyPanda.CHARACTERS, {'text' : text})
        self.endElement(MyPanda.CHARACTERS)
        self._pos += len(text)

    def process_characters(self, token):
        self.characters(token)
        self._pos = token.end()

    def process_big_break(self, inner_text):
        if self._list:
            self.endElement(MyPanda.LIST)
            self._list = False

        self.startElement(MyPanda.BREAK, {})
        self.endElement(MyPanda.BREAK)

        self._pos = self._pos + len(inner_text)

    def process_list(self, token):
        if self._list:
            self.endElement(MyPanda.LIST)

        self.startElement(MyPanda.LIST, {'text' : token.group(0) })
        self._list = True

        self._pos = token.end()

    def process_image(self, token):
        end_where = None

        text = token.group(0)

        wh0 = find_matching_bracket(self._data, "[", "]", token.start(0))
        wh1 = self._data.find("(", wh0)
        wh2 = find_matching_bracket(self._data, "(", ")", wh1)

        text = self._data[token.start(0):wh2+1]
        name = self._data[token.start(0)+2:wh0]
        link = self._data[wh1+1:wh2]

        text = text.strip()
        name = name.strip()
        link = link.strip()

        if wh2 == -1:
            raise IOError("Could not find")

        self._attr = {}
        self._attr['text'] = text
        self._attr['name'] = name
        self._attr['link'] = link

        self.startElement(MyPanda.IMAGE, self._attr)
        self.endElement(MyPanda.IMAGE)

        if wh2 >= 0:
            self._pos = wh2+1
            end_where = wh2+1

    def process_link(self, token):
        end_where = None

        text = token.group(0)

        wh0 = find_matching_bracket(self._data, "[", "]", token.start(0))
        wh1 = self._data.find("(", wh0)
        wh2 = find_matching_bracket(self._data, "(", ")", wh1)

        text = self._data[token.start(0):wh2+1]
        name = self._data[token.start(0)+1:wh0]
        link = self._data[wh1+1:wh2]

        text = text.strip()
        name = name.strip()
        link = link.strip()

        if wh2 == -1:
            raise IOError("Could not find")

        self._attr = {}
        self._attr['text'] = text
        self._attr['name'] = name
        self._attr['link'] = link

        self.startElement(MyPanda.LINK, self._attr)

        pat = re.compile("\!\[")
        m = pat.search(self._data, token.start()+1, wh2)
        if m:
            self.process_image(m)

        self.endElement(MyPanda.LINK)

        if wh2 >= 0:
            self._pos = wh2+1
            end_where = wh2+1

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
            heading = MyPanda.H1
        if text == "##":
            heading = MyPanda.H2
        if text == "###":
            heading = MyPanda.H3

        self.startElement( heading, attributes)
        self.endElement( heading)

    def process_header(self, token):
        text = token.group(0)

        if not self._header:
            if text == "---":
                self._header = True
            self._pos = token.end()
        else:
            if text == "---":
                self.startElement(MyPanda.HEADER, self._attr)
                self.endElement(MyPanda.HEADER)
                self._header = False
                self._pos = token.end()
            else:
                if self.is_token_first_in_line(token):
                    key = self.get_header_key(token)
                    value, end_place = self.get_header_value(token)

                    self._attr[key] = value
                    self._pos = end_place
                else:
                    self._pos = token.end()

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


class MyPandaDom(MyPanda):

    def __init__(self, mdfile, only_header=False):
        self.text = ""
        self.header = {}
        self.only_header = only_header

        super().__init__()

        self.parse(mdfile)

    def startElement(self, tag, attributes):
        if tag == MyPanda.HEADER:
            self.header = attributes
        elif tag == MyPanda.CHARACTERS:
            self.text += attributes['text']
        else:
            self.text += attributes['text']

    def endElement(self, tag):
        if tag == MyPanda.HEADER and self.only_header:
            self.stop()

    def characters(self, token):
        """ TODO this should be text instead of token? """
        self.text += token.group(0)


class Panda2Html(MyPanda):

    def __init__(self, from_file, to_file):
        super().__init__()

        self._list = False
        self._link = False

        self._tag = None
        self._prev_tag = None

        self._fh = open(to_file, 'wb')

        self.parse(from_file)

        data = "</body>\n</html>"
        self._fh.write(data.encode("utf-8"))

    def startElement(self, tag, attributes):

        if tag == MyPanda.HEADER:

            title = attributes['title']
            date = attributes['date']

            header = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="Content-Style-Type" content="text/css" />
  <meta name="generator" content="pandoc" />
  <title>{0}</title>
  <style type="text/css">code{white-space: pre;}</style>
  <link rel="stylesheet" href="pandoc.css" type="text/css" />
</head>
<body>
<div id="header">
<h1 class="title">{1}</h1>
<h3 class="date">{2}</h3>
</div>
    """
            header = header.replace("{0}",title)
            header = header.replace("{1}",title)
            header = header.replace("{2}",date)
            self._fh.write(header.encode("utf-8"))

        elif tag == MyPanda.BREAK:

            data = '</p><p>\n\n'
            self._fh.write(data.encode("utf-8"))

        elif tag == MyPanda.H1:

            text = attributes['text']
            data = '<h1>{0}</h1>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == MyPanda.LINK:
            self._link = True

        elif tag == MyPanda.H2:

            text = attributes['text']
            data = '<h2>{0}</h2>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == MyPanda.H3:

            text = attributes['text']
            data = '<h3>{0}</h3>\n'.format(text)
            self._fh.write(data.encode("utf-8"))

        elif tag == MyPanda.LIST:

            if self._list:
                data = '</li><li>\n'
            else:
                data = '<ul><li>\n'
            self._list = True
            self._fh.write(data.encode("utf-8"))

        elif tag == MyPanda.CHARACTERS:

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

        if tag != MyPanda.CHARACTERS:
            #print("Stopping element: "+tag)
            None

        if tag == MyPanda.LINK:

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

        elif tag == MyPanda.IMAGE:

            if not self._link:
                link = self._tag[1]['link']
                name = self._tag[1]['name']
                data = '<img src="{0}" alt="{1}"/>'.format(link, name)
                self._fh.write(data.encode("utf-8"))

        #data = "Stopping element {0}<br/>\n".format(tag)
        #self._fh.write(data.encode("utf-8"))
        pass

    def characters(self, token):
        data = token.group(0)
        self._fh.write(data.encode("utf-8"))


if ( __name__ == "__main__"):
   
   parser = MyPanda()
   #parser.parse("blog-md/index.md")
   parser.parse("blog-md/anonymity.md")
   #parser.parse("blog-md/internet-security.md")
   #parser.parse("blog-md/sheepy.md")
