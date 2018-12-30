from xml.etree.cElementTree import Element, ElementTree, SubElement

import EgvParser

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


def create_svg_dom(values, bounds):
    root = Element(NAME_SVG)
    root.set(ATTR_VERSION, VALUE_SVG_VERSION)
    root.set(ATTR_XMLNS, VALUE_XMLNS)
    root.set(ATTR_XMLNS_LINK, VALUE_XLINK)
    root.set(ATTR_XMLNS_EV, VALUE_XMLNS_EV)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    root.set(ATTR_WIDTH, str(width))
    root.set(ATTR_HEIGHT, str(height))
    viewbox = \
        str(bounds[0]) + " " + \
        str(bounds[1]) + " " + \
        str(width) + " " + \
        str(height)
    root.set(ATTR_VIEWBOX, viewbox)
    group = SubElement(root, NAME_GROUP)
    group.set(ATTR_FILL, VALUE_NONE)
    group.set(ATTR_STROKE, "#000")
    try:
        for segments in values:
            if segments[4] & EgvParser.MODE_D:
                path = SubElement(group, NAME_PATH)
                data = "M%i,%i %i,%i" % (segments[0], segments[1], segments[2], segments[3])
                path.set(ATTR_DATA, data)
    except MemoryError:
        pass
    return ElementTree(root)
