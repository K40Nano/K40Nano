from xml.etree.cElementTree import Element, ElementTree, SubElement

from Controller import Controller

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


class SvgController(Controller):
    def __init__(self, filename="svgcontroller"):
        Controller.__init__(self)
        self.max_x = -float('inf')
        self.max_y = -float('inf')
        self.min_x = float('inf')
        self.min_y = float('inf')
        self.current_x = 0
        self.current_y = 0
        self.segment_values = []
        if not filename.endswith(".svg"):
            filename += ".svg"
        self.filename = filename

    def move(self, dx, dy, slow=False, laser=False):
        next_x = self.current_x + dx
        next_y = self.current_y + dy
        if laser and slow:
            self.max_x = max(next_x, self.max_x)
            self.max_y = max(next_y, self.max_y)
            self.min_x = min(next_x, self.min_x)
            self.min_y = min(next_y, self.min_y)
            self.segment_values.append([self.current_x, self.current_y, next_x, next_y])
        self.current_x = next_x
        self.current_y = next_y

    def move_abs(self, x, y, slow=False, laser=False):
        self.move(x - self.current_x, y - self.current_y, slow, laser)

    def set_speed(self, speed=None, raster_step=None):
        pass

    def home(self):
        pass

    def rail(self, lock=False):
        pass

    def wait(self):
        pass

    def halt(self):
        pass

    def release(self):
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
        tree.write(self.filename)
