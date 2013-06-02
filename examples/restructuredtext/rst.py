
from io import BytesIO

from docutils.core import publish_doctree, publish_from_doctree

import pyte as rt

from pyte.font import TypeFace, TypeFamily
from pyte.font.style import REGULAR, BOLD, ITALIC
from pyte.font.type1 import Type1Font
from pyte.font.opentype import OpenTypeFont
from pyte.dimension import PT, CM, INCH
from pyte.backend import pdf
from pyte.frontend.xml import element_factory

import pyte.frontend.xml.elementtree as xml_frontend


pagella_regular = OpenTypeFont("../fonts/texgyrepagella-regular.otf",
                               weight=REGULAR)
pagella_italic = OpenTypeFont("../fonts/texgyrepagella-italic.otf",
                              weight=REGULAR, slant=ITALIC)
pagella_bold = OpenTypeFont("../fonts/texgyrepagella-bold.otf", weight=BOLD)
pagella_bold_italic = OpenTypeFont("../fonts/texgyrepagella-bolditalic.otf",
                                   weight=BOLD, slant=ITALIC)

pagella = TypeFace("TeXGyrePagella", pagella_regular, pagella_italic,
                   pagella_bold, pagella_bold_italic)
cursor_regular = Type1Font("../fonts/qcrr", weight=REGULAR)
cursor = TypeFace("TeXGyreCursor", cursor_regular)

fontFamily = TypeFamily(serif=pagella, mono=cursor)


styles = rt.StyleStore()

styles['title'] = rt.ParagraphStyle(typeface=fontFamily.serif,
                                    font_size=16*PT,
                                    line_spacing=rt.DEFAULT,
                                    space_above=6*PT,
                                    space_below=6*PT,
                                    justify=rt.CENTER)

styles['body'] = rt.ParagraphStyle(typeface=fontFamily.serif,
                                   font_weight=REGULAR,
                                   font_size=10*PT,
                                   line_spacing=rt.DEFAULT,
                                   #indent_first=0.125*INCH,
                                   space_above=0*PT,
                                   space_below=10*PT,
                                   justify=rt.BOTH)

styles['literal'] = rt.ParagraphStyle(base='body',
                                      #font_size=9*PT,
                                      justify=rt.LEFT,
                                      indent_left=1*CM,
                                      typeface=fontFamily.mono)
#                                      noWrap=True,   # but warn on overflow
#                                      literal=True ?)

styles['block quote'] = rt.ParagraphStyle(base='body',
                                          indent_left=1*CM)

styles['heading1'] = rt.HeadingStyle(typeface=fontFamily.serif,
                                     font_size=14*PT,
                                     line_spacing=rt.DEFAULT,
                                     space_above=14*PT,
                                     space_below=6*PT,
                                     numbering_style=None)

styles['heading2'] = rt.HeadingStyle(base='heading1',
                                     font_slant=ITALIC,
                                     font_size=12*PT,
                                     line_spacing=rt.DEFAULT,
                                     space_above=6*PT,
                                     space_below=6*PT)

styles['monospaced'] = rt.TextStyle(typeface=fontFamily.mono)

styles['enumerated list'] = rt.ListStyle(base='body',
                                         indent_left=5*PT,
                                         ordered=True,
                                         item_spacing=0*PT,
                                         numbering_style=rt.NUMBER,
                                         numbering_separator='.')

styles['bullet list'] = rt.ListStyle(base='body',
                                     indent_left=5*PT,
                                     ordered=False,
                                     item_spacing=0*PT)

styles['definition list'] = rt.DefinitionListStyle(base='body')


class Mono(rt.MixedStyledText):
    def __init__(self, text, y_offset=0):
        super().__init__(text, style=styles['monospaced'], y_offset=y_offset)



# input parsing
# ----------------------------------------------------------------------------

CustomElement, NestedElement = element_factory(xml_frontend, styles)

class Section(CustomElement):
    def parse(self, document, level=1):
        for element in self.getchildren():
            if isinstance(element, Title):
                elem = element.process(document, level=level,
                                       id=self.get('id', None))
            elif type(element) == Section:
                elem = element.process(document, level=level + 1)
            else:
                elem = element.process(document)
            if isinstance(elem, rt.Flowable):
                yield elem
            else:
                for flw in elem:
                    yield flw


class Paragraph(NestedElement):
    def parse(self, document):
        return rt.Paragraph(super().process_content(document),
                            style=self.style('body'))


class Title(CustomElement):
    def parse(self, document, level=1, id=None):
        #print('Title.render()')
        return rt.Heading(document, self.text, level=level, id=id,
                          style=self.style('heading{}'.format(level)))

class Tip(NestedElement):
    def parse(self, document):
        return rt.Paragraph('TIP: ' + super().process_content(document),
                            style=self.style('body'))


class Emphasis(CustomElement):
    def parse(self, document):
        return rt.Emphasized(self.text)


class Strong(CustomElement):
    def parse(self, document):
        return rt.Bold(self.text)


class Literal(CustomElement):
    def parse(self, document):
        return rt.LiteralText(self.text, style=self.style('monospaced'))


class Literal_Block(CustomElement):
    def parse(self, document):
        return rt.Paragraph(rt.LiteralText(self.text),
                            style=self.style('literal'))


class Block_Quote(NestedElement):
    def parse(self, document):
        return rt.Paragraph(super().process_content(document),
                            style=self.style('block quote'))


class Reference(CustomElement):
    def parse(self, document):
        return self.text


class Footnote(CustomElement):
    def parse(self, document):
        return rt.Paragraph('footnote', style=self.style('body'))


class Footnote_Reference(CustomElement):
    def parse(self, document):
        return self.text


class Target(CustomElement):
    def parse(self, document):
        return rt.MixedStyledText([])


class Enumerated_List(CustomElement):
    def parse(self, document):
        # TODO: handle different numbering styles
        return rt.List([item.process(document) for item in self.list_item],
                       style=self.style('enumerated list'))


class Bullet_List(CustomElement):
    def parse(self, document):
        return rt.List([item.process(document) for item in self.list_item],
                       style=self.style('bullet list'))


class List_Item(NestedElement):
    pass


class Definition_List(CustomElement):
    def parse(self, document):
        return rt.DefinitionList([item.process(document)
                                  for item in self.definition_list_item],
                                 style=self.style('definition list'))

class Definition_List_Item(CustomElement):
    def parse(self, document):
        return (self.term.process(document),
                self.definition.process(document))


class Term(NestedElement):
    pass


class Definition(NestedElement):
    pass


class Image(CustomElement):
    def parse(self, document):
        return rt.Image(self.get('uri').rsplit('.png', 1)[0])



class SimplePage(rt.Page):
    topmargin = bottommargin = 2*CM
    leftmargin = rightmargin = 2*CM

    def __init__(self, document):
        super().__init__(document, rt.A5, rt.PORTRAIT)

        body_width = self.width - (self.leftmargin + self.rightmargin)
        body_height = self.height - (self.topmargin + self.bottommargin)
        self.body = rt.Container(self, self.leftmargin, self.topmargin,
                                 body_width, body_height)

        self.content = document.content

        self.footnote_space = rt.FootnoteContainer(self.body, 0*PT, body_height)
        self._footnote_number = 0

        self.content = rt.Container(self.body, 0*PT, 0*PT,
                                    bottom=self.footnote_space.top,
                                    chain=document.content)

##        self.content._footnote_space = self.footnote_space
##
##        self.header = rt.Container(self, self.leftmargin, self.topmargin / 2,
##                                   body_width, 12*PT)
##        footer_vert_pos = self.topmargin + body_height + self.bottommargin /2
##        self.footer = rt.Container(self, self.leftmargin, footer_vert_pos,
##                                   body_width, 12*PT)
##        header_text = Header(header_style)
##        self.header.append_flowable(header_text)
##        footer_text = Footer(footer_style)
##        self.footer.append_flowable(footer_text)


# main document
# ----------------------------------------------------------------------------
class ReStructuredTextDocument(rt.Document):
    def __init__(self, filename):
        with open(filename) as file:
            doctree = publish_doctree(file.read())
        xml_buffer = BytesIO(publish_from_doctree(doctree, writer_name='xml'))
        parser = xml_frontend.Parser(CustomElement)
        super().__init__(parser, xml_buffer, backend=pdf)
        self.parse_input()

    def parse_input(self):
##        toc = TableOfContents(style=toc_style, styles=toc_levels)

        self.content_flowables = []

        self.content_flowables.append(rt.Paragraph(self.root.title.text,
                                                   styles['title']))

        for section in self.root.section:
##            toc.register(flowable)
            for flowable in section.parse(self):
                self.content_flowables.append(flowable)
##        try:
##            for flowable in self.root.body.acknowledgement.parse(self):
##                toc.register(flowable)
##                self.content_flowables.append(flowable)
##        except AttributeError:
##            pass

    def setup(self):
        self.page_count = 1
        self.content = rt.Chain(self)
        page = SimplePage(self)
        self.add_page(page, self.page_count)

        for flowable in self.content_flowables:
            self.content.append_flowable(flowable)

##        bib = self.bibliography.bibliography()
##        self.content.append_flowable(bib)

    def new_page(self, chains):
        page = SimplePage(self)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content
