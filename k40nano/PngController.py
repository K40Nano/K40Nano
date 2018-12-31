#!/usr/bin/env python

from .Controller import Controller
from .PngRaster import PngRaster


class PngController(Controller):
    def __init__(self, filename="pngcontroller"):
        Controller.__init__(self)
        self.max_x = -float('inf')
        self.max_y = -float('inf')
        self.min_x = float('inf')
        self.min_y = float('inf')
        self.current_x = 0
        self.current_y = 0
        self.segment_values = []
        if not filename.endswith(".png"):
            filename += ".png"
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
        if len(self.segment_values) == 0:
            return
        raster = PngRaster(self.max_x - self.min_x + 1, self.max_y - self.min_y + 1, 1, 0)
        raster.fill(1)
        for segments in self.segment_values:
            raster.draw_line(segments[0] - self.min_x,
                             segments[1] - self.min_y,
                             segments[2] - self.min_x,
                             segments[3] - self.min_y,
                             0)

        raster.save_png(self.filename)
