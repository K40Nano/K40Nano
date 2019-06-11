#!/usr/bin/env python

# MIT License.

from xml.etree.cElementTree import Element, ElementTree, SubElement

from .Plotter import Plotter

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


class SvgPlotter(Plotter):
    def __init__(self, writer=None):
        Plotter.__init__(self)
        self.write_object = writer
        self.segment_values = []

    def close(self):
        if len(self.segment_values) == 0:
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
        tree.write(self.write_object)
        self.segment_values = []

    def move(self, dx, dy):
        if self.pen_down:
            self.segment_values.append(
                [
                    self.current_x,
                    self.current_y,
                    self.current_x + dx,
                    self.current_y + dy,
                ])
        Plotter.move(self, dx, dy)
