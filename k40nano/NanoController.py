#!/usr/bin/env python
"""
This script communicates with the K40 Laser Cutter.

Copyright (C) 2017 Scorch www.scorchworks.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from .Controller import Controller
from .LaserM2 import LaserM2
from .NanoConnection import NanoConnection
from .NanoConstants import *


class NanoController(Controller):
    def __init__(self, connect=None, laser_board=None):
        Controller.__init__(self)
        self.connection = connect
        if self.connection is None:
            self.connection = NanoConnection()
        self.connection.connect()
        self.board = laser_board
        if self.board is None:
            self.board = LaserM2()
        self.current_x = 0
        self.current_y = 0
        self.mode = 0
        self.raster_step = 0
        self.speed = None
        self.speedcode = None

    def move(self, dx, dy, slow=False, laser=False):
        if dx == 0 and dy == 0:
            return
        if slow and not self.is_slow():
            self.slow()
        if not slow and self.is_slow():
            self.rapid()
        if laser and not self.is_on():
            self.laser_on()
        if not laser and self.is_on():
            self.laser_off()
        if dy == 0:
            if dx > 0:  # right
                self.move_right(dx)
            else:
                self.move_left(dx)
            return
        if dx == 0:
            if dy > 0:  # bottom
                self.move_bottom(dy)
            else:
                self.move_top(dy)
            return
        if slow:
            if abs(dx) == abs(dy):
                self.move_angle(dx, dy)
                return
            else:
                self.move_line(dx, dy)
                # Draw a cut line with a bresenham line draw algorithm to the new location using dx and dy.
                return

        else:
            if dx > 0:  # right
                self.move_right(dx)
            else:  # left
                self.move_left(dx)
            if dy > 0:  # bottom
                self.move_bottom(dy)
            else:  # top
                self.move_top(dy)

    def move_abs(self, x, y, slow=False, laser=False):
        self.move(x - self.current_x, y - self.current_y, slow, laser)
    
    def move_now(self, dx, dy, absolute=False):
        self.connection.append(b'I')
        if absolute:
            self.move_x(x - self.current_x)
            self.move_y(y - self.current_y)
        else:
            self.move_x(dx)
            self.move_y(dy)
        self.connection.append(b'S1P')
        self.connection.write_buffer()

    def increase_speed(self, increase=0):
        current_speed = self.speed
        if current_speed is None:
            current_speed = 0
        self.set_speed(current_speed + float(increase))

    def set_step(self, step=0):
        if step == self.raster_step:
            return
        self.raster_step = step
        if self.speed is not None:
            self.speedcode = self.encode_speed(self.speed, self.raster_step)
            if self.is_slow():  # speed is changed, to take effect we must reenter slow_mode
                self.rapid()
                self.slow()

    def set_speed(self, speed=-1.0):
        if isinstance(speed, int):
            self.speed = float(speed)
        if isinstance(speed, float):
            if speed <= 0:  # set speed to default.
                self.speedcode = None
                self.speed = None
            else:
                self.speed = speed
                self.speedcode = self.encode_speed(self.speed, self.raster_step)
        elif isinstance(speed, str):
            self.speedcode = speed
            self.speed = None
        if self.is_slow():  # speed is changed, to take effect we must reenter slow_mode
            self.rapid()
            self.slow()

    def home(self):
        self.connection.send_valid_packet(COMMAND_HOME)
        self.current_x = 0
        self.current_y = 0

    def rail(self, lock=False):
        if not lock:
            self.connection.send_valid_packet(COMMAND_UNLOCK_RAIL)
        else:
            self.connection.send_valid_packet(COMMAND_LOCK_RAIL)

    def wait(self):
        if self.is_finishing():
            return
        # self.connection.write(b'NS1EFNSE')  # This will trigger the wait in any mode.
        if not self.is_slow():
            self.connection.write_completed_packets(b'NS1E')
        self.connection.write(b'FNSE')
        self.set_mode(MODE_SLOW, False)
        self.set_mode(MODE_LASER_ON, False)
        self.set_mode(MODE_FINISHING, True)
        self.connection.wait()
        self.set_mode(MODE_FINISHING, False)

    def halt(self):
        self.connection.write_buffer()
        self.connection.send_valid_packet(COMMAND_INTERRUPT)

    def release(self):
        self.connection.write_buffer()
        self.connection.disconnect()

    def set_mode(self, mask, set_value):
        if set_value:
            self.mode |= mask
        else:
            self.mode &= ~mask

    def is_slow(self):
        return self.mode & MODE_SLOW

    def is_on(self):
        return self.mode & MODE_LASER_ON

    def is_left(self):
        return self.mode & MODE_DIRECTION_LEFT

    def is_top(self):
        return self.mode & MODE_DIRECTION_TOP

    def is_finishing(self):
        return self.mode & MODE_FINISHING

    def is_reset(self):
        return self.mode & MODE_RESET

    def slow(self):
        if self.is_slow():
            return
        if self.is_reset():
            self.connection.write_completed_packets(COMMAND_NEXT + COMMAND_S + COMMAND_E)
            self.set_mode(MODE_RESET, False)
        if self.speedcode is not None:
            self.connection.write_completed_packets(self.speedcode)
        self.connection.write_completed_packets(COMMAND_NEXT)
        if self.is_left():
            self.connection.write_completed_packets(COMMAND_LEFT)
        else:
            self.connection.write_completed_packets(COMMAND_RIGHT)
        if self.is_top():
            self.connection.write_completed_packets(COMMAND_TOP)
        else:
            self.connection.write_completed_packets(COMMAND_BOTTOM)
        self.connection.write_completed_packets(COMMAND_S1E)
        self.set_mode(MODE_SLOW, True)

    def rapid(self):
        if not self.is_slow():
            return
        if self.is_on():
            self.laser_off()
        self.connection.write_completed_packets(COMMAND_RESET)
        self.set_mode(MODE_SLOW, False)
        self.set_mode(MODE_RESET, True)

    def laser_on(self):
        if self.is_on():
            return
        if not self.is_slow():
            self.slow()
        self.set_mode(MODE_LASER_ON, True)
        self.connection.write_completed_packets(COMMAND_ON)

    def laser_off(self):
        if not self.is_on():
            return
        self.set_mode(MODE_LASER_ON, False)
        self.connection.write_completed_packets(COMMAND_OFF)

    def move_x(self, dx):
        if dx > 0:
            self.move_right(dx)
        else:
            self.move_left(dx)

    def move_y(self, dy):
        if dy > 0:
            self.move_bottom(dy)
        else:
            self.move_top(dy)

    def move_angle(self, dx, dy):
        if not self.is_left() and dx < 0:  # left
            self.move_left()
        if self.is_left() and dx > 0:  # right
            self.move_right()
        if not self.is_top() and dy < 0:  # top
            self.move_top()
        if self.is_top() and dy > 0:  # bottom
            self.move_bottom()
        self.current_x += dx
        self.current_y += dy
        self.connection.write_completed_packets(COMMAND_ANGLE)
        self.connection.write_completed_packets(self.encode_distance(abs(dy)))  # dx == dy

    def move_right(self, dx=0):
        self.current_x += dx
        if self.is_left():
            self.current_y += self.raster_step
        self.set_mode(MODE_DIRECTION_LEFT, False)
        self.connection.write_completed_packets(COMMAND_RIGHT)
        if dx != 0:
            self.connection.write_completed_packets(self.encode_distance(abs(dx)))

    def move_left(self, dx=0):
        self.current_x -= abs(dx)
        if not self.is_left():
            self.current_y += self.raster_step
        self.set_mode(MODE_DIRECTION_LEFT, True)
        self.connection.write_completed_packets(COMMAND_LEFT)
        if dx != 0:
            self.connection.write_completed_packets(self.encode_distance(abs(dx)))

    def move_bottom(self, dy=0):
        self.current_y += dy
        self.set_mode(MODE_DIRECTION_TOP, False)
        self.connection.write_completed_packets(COMMAND_BOTTOM)
        if dy != 0:
            self.connection.write_completed_packets(self.encode_distance(abs(dy)))

    def move_top(self, dy=0):
        self.current_y -= abs(dy)
        self.set_mode(MODE_DIRECTION_TOP, True)
        self.connection.write_completed_packets(COMMAND_TOP)
        if dy != 0:
            self.connection.write_completed_packets(self.encode_distance(abs(dy)))

    def move_line(self, dx, dy):
        """
        Implementation of Bresenham's line draw algorithm.
        Checks for the changes between straight and diagonal parts calls the move functions during mode change.
        """
        x0 = self.current_x
        y0 = self.current_y
        x1 = self.current_x + dx
        y1 = self.current_y + dy
        diagonal = 0
        straight = 0
        if dy < 0:
            dy = -dy
            step_y = -1
        else:
            step_y = 1
        if dx < 0:
            dx = -dx
            step_x = -1
        else:
            step_x = 1
        if dx > dy:
            dy <<= 1  # dy is now 2*dy
            dx <<= 1
            fraction = dy - (dx >> 1)  # same as 2*dy - dx

            while x0 != x1:
                if fraction >= 0:
                    y0 += step_y
                    fraction -= dx  # same as fraction -= 2*dx
                    if straight != 0:
                        self.move_x(straight * step_x)
                        straight = 0
                    diagonal += 1
                else:
                    if diagonal != 0:
                        self.move_angle(diagonal * step_x, diagonal * step_y)
                        diagonal = 0
                    straight += 1
                x0 += step_x
                fraction += dy  # same as fraction += 2*dy
        else:
            dy <<= 1  # dy is now 2*dy
            dx <<= 1  # dx is now 2*dx
            fraction = dx - (dy >> 1)

            while y0 != y1:
                if fraction >= 0:
                    x0 += step_x
                    fraction -= dy
                    if straight != 0:
                        self.move_y(straight * step_y)
                        straight = 0
                    diagonal += 1
                else:
                    if diagonal != 0:
                        self.move_angle(diagonal * step_x, diagonal * step_y)
                        diagonal = 0
                    straight += 1
                y0 += step_y
                fraction += dx
        if straight != 0:
            self.move_x(straight * step_x)
        if diagonal != 0:
            self.move_angle(diagonal * step_x, diagonal * step_y)

    def encode_speed(self, feed_rate, step_amount=0):
        return self.board.make_speed(feed_rate, step_amount)

    @staticmethod
    def encode_distance(distance_mils):
        if abs(distance_mils - round(distance_mils, 0)) > 0.000001:
            raise Exception('Distance values should be integer value (inches*1000)')
        distance_mils = int(distance_mils)
        code = b''
        value_z = 255

        while distance_mils >= 255:
            code += b'z'
            distance_mils -= value_z
        if distance_mils == 0:
            return code
        elif distance_mils < 26:  # codes  "a" through  "y"
            character = chr(96 + distance_mils)
            return code + bytes(bytearray(character, 'utf8'))
        elif distance_mils < 52:  # codes "|a" through "|z"
            character = chr(96 + distance_mils - 25)
            return code + b'|' + bytes(bytearray(character, 'utf8'))
        elif distance_mils < 255:
            code += bytes(bytearray("%03d" % distance_mils, 'utf8'))
            return code
        else:
            raise Exception("Could not create distance")  # This really shouldn't happen.

    @staticmethod
    def get_bounds(values):
        min_x = float('inf')
        min_y = float('inf')
        max_x = -float('inf')
        max_y = -float('inf')
        for segments in values:
            x0 = segments[0]
            y0 = segments[1]
            x1 = segments[2]
            y1 = segments[3]
            min_x = min(min_x, x0, x1)
            min_y = min(min_y, y0, y1)
            max_x = max(max_x, x0, x1)
            max_y = max(max_y, y0, y1)
        return min_x, min_y, max_x, max_y
