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

from .NanoConstants import *
from .Transaction import Transaction

STATE_EMPTY = 0
STATE_INIT = 1
STATE_SPEED = 2
STATE_R1 = 3
STATE_SLOW = 4
STATE_R2 = 5
STATE_FINISH = 6


class NanoTransaction(Transaction):
    def __init__(self, writer, board):
        Transaction.__init__(self, writer)
        self.board = board
        self.state = STATE_EMPTY
        self.is_on = False
        self.is_left = False
        self.is_top = False
        self.needs_speed = True
        self.was_ever_slowed = False
        self.was_ever_moved = False
        self.was_last_rapid = False

    def state_to_init(self):
        if self.state == STATE_INIT:
            return
        if self.state == STATE_EMPTY:
            self.writer.write(b'I')
        else:
            self.state_to_r2()
            self.writer.write(b'NSE')
        self.state = STATE_INIT

    def state_to_speed(self):
        if self.state == STATE_SPEED:
            return
        self.state_to_init()
        if self.speedcode is not None:
            self.writer.write(self.speedcode)
        self.needs_speed = False
        self.state = STATE_SPEED
    
    def state_to_r1(self):
        if self.state == STATE_R1:
            return
        self.state_to_speed()
        self.state = STATE_R1

    def state_to_slow(self):
        if self.state == STATE_SLOW:
            return
        self.state_to_r1()
        self.writer.write(b'NS1E')
        self.state = STATE_SLOW
        self.was_ever_slowed = True
    
    
    def state_to_r2(self):
        if self.state == STATE_R2:
            return
        self.state_to_slow()
        self.writer.write(b'@')
        self.state = STATE_R2
    

    def state_to_finish(self):
        if self.state == STATE_FINISH:
            return
        self.state_to_slow()
        self.writer.write(b'FNSE')
        self.state = STATE_FINISH

    def move(self, dx, dy, laser=False, slow=False, absolute=False):
        if absolute:
            self.move(dx - self.current_x, dy - self.current_y, laser, slow, absolute=False)
            return
        if dx == 0 and dy == 0:
            return
        
        if not laser:
            self.laser_off()

        if slow:
            # We are performing a slow move.
            self.was_last_rapid = False
            self.state_to_slow()
            if laser and not self.is_on:
                self.laser_on()
            elif not laser and self.is_on:
                self.laser_off()
            if dy == 0:
                self.move_x(dx)
            elif dx == 0:
                self.move_y(dy)
            elif abs(dx) == abs(dy):
                self.move_angle(dx, dy)
            else:
                self.move_line(dx, dy)
                # Draw a cut line with a bresenham line draw algorithm to the new location using dx and dy.
        else:
            # We are performing a rapid move.
            if self.was_last_rapid:
                self.writer.write(b'N')
            if self.was_ever_slowed:
                self.state_to_r2()
            else:
                self.state_to_r1()
            if dy == 0:
                self.move_x(dx)
            elif dx == 0:
                self.move_y(dy)
            else:
                self.move_x(dx)
                self.move_y(dy)
            self.was_last_rapid = True
        self.was_ever_moved = True

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
        self.needs_speed = True

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
        elif isinstance(speed, str):  # We only have the text code
            self.speedcode = speed
            self.speed = None
        self.needs_speed = True

    def write(self, data):
        if self.state == STATE_EMPTY:
            self.state_to_init()
        self.writer.write(data)

    def finish(self):
        writer = self.writer
        if self.state == STATE_EMPTY:
            writer.close(self)
            return
        if not self.was_ever_moved:
            writer.close(self)
            return
        if not self.was_ever_slowed:
            writer.write(b'S1P')
            writer.close(self)
            return
        self.laser_off()
        self.state_to_finish()
        writer.close(self)
        writer.wait()

    def laser_on(self):
        if self.is_on:
            return
        self.is_on = True
        self.writer.write(COMMAND_ON)

    def laser_off(self):
        if not self.is_on:
            return
        self.is_on = False
        self.writer.write(COMMAND_OFF)

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
        if dx < 0:  # left
            self.move_left()
        if dx > 0:  # right
            self.move_right()
        if dy < 0:  # top
            self.move_top()
        if dy > 0:  # bottom
            self.move_bottom()
        self.current_x += dx
        self.current_y += dy
        self.check_bounds()
        self.writer.write(COMMAND_ANGLE)
        self.writer.write(self.encode_distance(abs(dy)))  # dx == dy

    def move_right(self, dx=0):
        self.current_x += dx
        if self.is_left:
            self.current_y += self.raster_step
        self.is_left = False
        self.writer.write(COMMAND_RIGHT)
        if dx != 0:
            self.writer.write(self.encode_distance(abs(dx)))
            self.check_bounds()

    def move_left(self, dx=0):
        self.current_x -= abs(dx)
        if not self.is_left:
            self.current_y += self.raster_step
        self.is_left = True
        self.writer.write(COMMAND_LEFT)
        if dx != 0:
            self.writer.write(self.encode_distance(abs(dx)))
            self.check_bounds()

    def move_bottom(self, dy=0):
        self.current_y += dy
        self.is_top = False
        self.writer.write(COMMAND_BOTTOM)
        if dy != 0:
            self.writer.write(self.encode_distance(abs(dy)))
            self.check_bounds()

    def move_top(self, dy=0):
        self.current_y -= abs(dy)
        self.is_top = True
        self.writer.write(COMMAND_TOP)
        if dy != 0:
            self.writer.write(self.encode_distance(abs(dy)))
            self.check_bounds()

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
