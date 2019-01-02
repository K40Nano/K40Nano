#!/usr/bin/env python

from .PngRaster import PngRaster
from .Transaction import Transaction


class PngTransaction(Transaction):
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
        raster = PngRaster(self.max_x - self.min_x, self.max_y - self.min_y, 1, 0)
        raster.fill(1)
        for segments in self.segment_values:
            raster.draw_line(segments[0] - self.min_x,
                             segments[1] - self.min_y,
                             segments[2] - self.min_x,
                             segments[3] - self.min_y,
                             0)
        self.writer.write(raster.get_png_bytes())
        self.writer.close()
        self.writer = None
