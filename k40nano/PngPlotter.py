#!/usr/bin/env python

# MIT License.

from .Plotter import Plotter
from .PngRaster import PngRaster


class PngPlotter(Plotter):
    def __init__(self, writer=None):
        Plotter.__init__(self)
        self.write_object = writer
        self.segment_values = []

    def close(self):
        if len(self.segment_values) == 0:
            return
        raster = PngRaster(self.max_x - self.min_x,
                           self.max_y - self.min_y,
                           1,
                           0)  # 1 bit-sample, type 0 (greyscale)
        raster.fill(1)
        for segments in self.segment_values:
            raster.draw_line(segments[0] - self.min_x,
                             segments[1] - self.min_y,
                             segments[2] - self.min_x,
                             segments[3] - self.min_y,
                             0)
        if isinstance(self.write_object, str):
            with open(self.write_object, "w+") as writer:
                writer.write(raster.get_png_bytes())
        else:
            self.write_object.write(raster.get_png_bytes())
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
