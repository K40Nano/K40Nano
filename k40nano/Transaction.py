class Transaction:
    def __init__(self, write_object):
        self.writer = write_object
        self.current_x = 0
        self.current_y = 0
        self.max_x = 0
        self.max_y = 0
        self.min_x = 0
        self.min_y = 0

        self.raster_step = 0
        self.speed = None
        self.speedcode = None

    def start(self):
        self.max_x = self.current_x
        self.min_x = self.current_x
        self.max_y = self.current_y
        self.min_y = self.current_y
        return self

    def move(self, dx, dy, laser=False, slow=False, absolute=False):
        pass

    def set_speed(self, speed):
        pass

    def set_step(self, step):
        pass

    def increase_speed(self, increase):
        pass

    def finish(self):
        pass

    def pop(self):
        pass

    def check_bounds(self):
        self.min_x = min(self.min_x, self.current_x)
        self.min_y = min(self.min_y, self.current_y)
        self.max_x = max(self.max_x, self.current_x)
        self.max_y = max(self.max_y, self.current_y)
