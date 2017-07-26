from html.parser import HTMLParser
from re import sub
from sys import stderr
from traceback import print_exc


class OceanHTMLParser(HTMLParser):
    """
        继承HTMLParser，用于解析html文本，得到ASCII纯文本字符串
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + '')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n\n')

    @property
    def text(self):
        return ''.join(self.__text).strip()


def html_to_text(markup):
    try:
        parser = OceanHTMLParser()
        parser.feed(markup)
        parser.close()
        return parser.text
    except:
        print_exc(file=stderr)
        return markup
