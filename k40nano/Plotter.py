#!/usr/bin/env python


class Plotter:
    def __init__(self, current_x=0, current_y=0):
        self.current_x = current_x
        self.current_y = current_y
        self.max_x = current_x
        self.max_y = current_y
        self.min_x = current_x
        self.min_y = current_y
        self.start_x = current_x
        self.start_y = current_y
        self.pen_down = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        pass

    def close(self):
        pass

    def move_abs(self, x, y):
        self.move(x - self.current_x, y - self.current_y)

    def move(self, dx, dy):
        self.current_x += dx
        self.current_y += dy
        self.check_bounds()

    def down(self):
        self.pen_down = True

    def up(self):
        self.pen_down = False

    def check_bounds(self):
        self.min_x = min(self.min_x, self.current_x)
        self.min_y = min(self.min_y, self.current_y)
        self.max_x = max(self.max_x, self.current_x)
        self.max_y = max(self.max_y, self.current_y)
