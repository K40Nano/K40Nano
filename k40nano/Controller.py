class Controller:
    def __init__(self):
        pass

    def move(self, dx, dy, slow=False, laser=False):
        pass

    def move_abs(self, x, y, slow=False, laser=False):
        pass

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
        pass
