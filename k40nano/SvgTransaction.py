from xml.etree.cElementTree import Element, ElementTree, SubElement

from .Transaction import Transaction

NAME_SVG = "svg"
NAME_GROUP = "g"
ATTR_VERSION = "version"
VALUE_SVG_VERSION = "1.1"
ATTR_XMLNS = "xmlns"
VALUE_XMLNS = "http://www.w3.org/2000/svg"
ATTR_XMLNS_LINK = "xmlns:xlink"
VALUE_XLINK = "http://www.w3.org/1999/xlink"
ATTR_XMLNS_EV = "xmlns:ev"
VALUE_XMLNS_EV = "http://www.w3.org/2001/xml-events"
ATTR_WIDTH = "width"
ATTR_HEIGHT = "height"
ATTR_VIEWBOX = "viewBox"
NAME_PATH = "path"
ATTR_DATA = "d"
ATTR_FILL = "fill"
ATTR_STROKE = "stroke"
ATTR_STROKE_WIDTH = "stroke-width"
VALUE_NONE = "none"


class SvgTransaction(Transaction):
    def __init__(self, filename=None):
        Transaction.__init__(self, filename)
        self.segment_values = []

    def move(self, dx, dy, laser=False, slow=False, absolute=False):
        if absolute:
            self.move(dx - self.current_x, dy - self.current_y, laser, slow, absolute=False)
            return
        next_x = self.current_x + dx
        next_y = self.current_y + dy
        if laser:
            self.check_bounds()
            self.segment_values.append([self.current_x, self.current_y, next_x, next_y])
        self.current_x = next_x
        self.current_y = next_y
        self.check_bounds()

    def finish(self):
        self.pop()

    def pop(self):
        if len(self.segment_values) == 0:
            return
        if self.writer is None:
            return
        root = Element(NAME_SVG)
        root.set(ATTR_VERSION, VALUE_SVG_VERSION)
        root.set(ATTR_XMLNS, VALUE_XMLNS)
        root.set(ATTR_XMLNS_LINK, VALUE_XLINK)
        root.set(ATTR_XMLNS_EV, VALUE_XMLNS_EV)
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        root.set(ATTR_WIDTH, str(width))
        root.set(ATTR_HEIGHT, str(height))
        viewbox = \
            str(self.min_x) + " " + \
            str(self.min_y) + " " + \
            str(width) + " " + \
            str(height)
        root.set(ATTR_VIEWBOX, viewbox)
        group = SubElement(root, NAME_GROUP)
        group.set(ATTR_FILL, VALUE_NONE)
        group.set(ATTR_STROKE, "#000")
        try:
            for segments in self.segment_values:
                path = SubElement(group, NAME_PATH)
                data = "M%i,%i %i,%i" % (segments[0], segments[1], segments[2], segments[3])
                path.set(ATTR_DATA, data)
        except MemoryError:
            pass
        tree = ElementTree(root)
        tree.write(self.writer)
        self.writer.close()
        self.writer = None
