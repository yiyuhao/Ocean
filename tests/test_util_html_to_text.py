from unittest import TestCase
from app.utils.html_to_text import html_to_text


class HTMLToTextTestCase(TestCase):
    """
        测试个人模块 utils/html_to_text
    """
    def test_html_to_text(self):
        markup_1 = r'''
                <html> 
                    <body> 
                        <b>Project:</b> DeHTML<br> 
                        <b>Description</b>:<br> 
                        This small script is intended to allow conversion from HTML markup to  
                        plain text. 
                    </body> 
                </html> 
            '''
        markup_2 = r'<a href="https://www.baidu.com/">百度</a>'
        markup_3 = r'''<h1>ckeditor是一款富文本编辑器</h1>


<p>非常强大</p>
'''
        markups = [markup_1, markup_2, markup_3]

        for markup in markups:
            text = html_to_text(markup)
            self.assertNotIn('<', text)
            self.assertNotIn('>', text)

        text = html_to_text(markup_2)
        self.assertEqual('百度', text)

        text = html_to_text(markup_3)
        self.assertEqual('ckeditor是一款富文本编辑器\n\n非常强大', text)
