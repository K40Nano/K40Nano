#!/usr/bin/env python


class Controller:
    def __init__(self):
        pass

    def move(self, dx, dy, slow=False, laser=False):
        pass

    def move_abs(self, x, y, slow=False, laser=False):
        pass

    def move_now(self, dx, dy, absolute=False):
        pass
    
    def set_speed(self, speed=-1.0):
        pass

    def set_step(self, step=0):
        pass

    def increase_speed(self, increase=0):
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
        pass
