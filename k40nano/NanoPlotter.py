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
from .LaserSpeed import LaserSpeed
from .NanoConnection import NanoConnection
from .Plotter import Plotter

DEFAULT_SPEED = 75.0
COMMAND_RIGHT = b'B'
COMMAND_LEFT = b'T'
COMMAND_TOP = b'L'
COMMAND_BOTTOM = b'R'
COMMAND_ANGLE = b'M'
COMMAND_ON = b'D'
COMMAND_OFF = b'U'

STATE_DEFAULT = 0
STATE_CONCAT = 1
STATE_UNFINISHED = 2
STATE_COMPACT = 3


class NanoPlotter(Plotter):

    def __init__(self, laser_board=None, connection=None, usb=None):
        Plotter.__init__(self)
        self.board = laser_board
        if self.board is None:
            self.board = "M2"
        self.connection = connection
        self.usb = usb
        self.state = STATE_DEFAULT
        self.is_on = False
        self.is_left = False
        self.is_top = False
        self.is_speed = False
        self.is_cut = False
        self.is_harmonic = False

        self.set_step = None
        self.set_speed_code = None
        self.set_speed_value = None

        self.previous_set_step = None
        self.previous_set_speed_code = None
        self.previous_set_speed = None

    def open(self):
        if self.connection is None:
            self.connection = NanoConnection(usb=self.usb)
        self.connection.open()
        self.reset_modes()
        self.state = STATE_DEFAULT

    def close(self):
        if self.state == STATE_CONCAT:
            self.connection.write(b'S1P')
        if self.state == STATE_UNFINISHED:
            self.enter_compact_mode()
            self.exit_compact_mode_finish()
        elif self.state == STATE_COMPACT:
            self.exit_compact_mode_finish()
        self.connection.flush()
        self.connection.close()

    def move(self, dx, dy):
        if dx == 0 and dy == 0:
            return
        if self.state == STATE_DEFAULT:
            self.connection.write(b'I')
            if dy == 0:
                self.move_x(dx)
            elif dx == 0:
                self.move_y(dy)
            else:
                self.move_x(dx)
                self.move_y(dy)
            self.connection.send(b'S1P')
        elif self.state == STATE_COMPACT:
            if dy == 0:
                self.move_x(dx)
            elif dx == 0:
                self.move_y(dy)
            elif abs(dx) == abs(dy):
                self.move_angle(dx, dy)
            else:
                self.move_line(dx, dy)
        elif self.state == STATE_CONCAT or self.state == STATE_UNFINISHED:
            if dy == 0:
                self.move_x(dx)
            elif dx == 0:
                self.move_y(dy)
            else:
                self.move_x(dx)
                self.move_y(dy)
            self.connection.write(b'N')
        self.check_bounds()

    def laser_on(self):
        self.down()

    def laser_off(self):
        self.up()

    def down(self):
        if self.is_on:
            return False
        if self.state == STATE_DEFAULT:
            self.connection.write(b'I')
            self.connection.write(COMMAND_ON)
            self.connection.send(b'S1P')
        elif self.state == STATE_COMPACT:
            self.connection.write(COMMAND_ON)
        elif self.state == STATE_CONCAT or self.state == STATE_UNFINISHED:
            self.connection.write(COMMAND_ON)
            self.connection.write(b'N')
        self.is_on = True
        return True

    def up(self):
        if not self.is_on:
            return False
        if self.state == STATE_DEFAULT:
            self.connection.write(b'I')
            self.connection.write(COMMAND_OFF)
            self.connection.send(b'S1P')
        elif self.state == STATE_COMPACT:
            self.connection.write(COMMAND_OFF)
        elif self.state == STATE_CONCAT or self.state == STATE_UNFINISHED:
            self.connection.write(COMMAND_OFF)
            self.connection.write(b'N')
        self.is_on = False
        return True

    def enter_compact_mode(self, speed=None, harmonic_step=None):
        if self.state == STATE_COMPACT:
            return
        if self.state == STATE_DEFAULT:
            self.connection.write(b"I")
        changing = (
                           self.is_speed and
                           speed is not None and
                           (
                                   (
                                           isinstance(speed, str) and
                                           self.set_speed_code != speed
                                   ) or (
                                           isinstance(speed, (float, int)) and
                                           self.set_speed_value != float(speed)
                                   )
                           )
                   ) or (
                           self.is_harmonic and
                           harmonic_step is not None and
                           self.set_step != harmonic_step
                   ) or (
                           self.is_cut and
                           (
                                   harmonic_step is not None and
                                   harmonic_step != 0
                           )
                   )

        if speed is None and harmonic_step is None and self.previous_set_speed_code is not None:
            speed_code = self.previous_set_speed_code
        else:
            if harmonic_step is None:
                if self.previous_set_step is not None:
                    harmonic_step = self.previous_set_step
                else:
                    harmonic_step = 0
            if speed is None:
                if self.previous_set_speed is not None:
                    speed = self.previous_set_speed
                else:
                    speed = DEFAULT_SPEED
                speed_code = LaserSpeed.make_speed_code(speed, harmonic_step, self.board)
            elif isinstance(speed, str):
                speed_code = speed
            else:
                speed_code = LaserSpeed.make_speed_code(speed, harmonic_step, self.board)
        if changing:
            # We can't perform this operation within concat. We must reset.
            self.connection.write(b'S1E@NSE')  # Jump into compact mode and reset.
            self.reset_modes()
        if not self.is_speed:
            self.connection.write(speed_code)
            self.connection.write(b'N')
        self.set_speed_code = speed_code
        self.previous_set_speed_code = speed_code
        if speed is not None and isinstance(speed, (float, int)):
            self.set_speed_value = speed
            self.previous_set_speed = speed
        if harmonic_step is not None:
            self.set_step = harmonic_step
            self.previous_set_step = harmonic_step
        self.is_speed = True
        self.is_harmonic = 'G' in speed_code
        self.is_cut = 'C' in speed_code

        self.declare_directions()
        self.connection.write(b'S1E')
        self.state = STATE_COMPACT

    def exit_compact_mode_finish(self):
        if self.state == STATE_COMPACT:
            self.connection.write(b'FNSE')
            self.connection.flush()
            self.connection.wait()
            self.reset_modes()
            self.state = STATE_DEFAULT
            return True
        return False

    def exit_compact_mode_reset(self):
        if self.state == STATE_COMPACT:
            self.connection.write(b'@NSE')
            self.reset_modes()
            self.state = STATE_UNFINISHED
            return True
        return False

    def exit_compact_mode_break(self):
        if self.state == STATE_COMPACT:
            self.connection.write(b'N')
            self.state = STATE_UNFINISHED
            return True
        return False

    def enter_concat_mode(self):
        if self.state == STATE_DEFAULT:
            self.connection.write(b"I")
            self.state = STATE_CONCAT
            return True
        return False

    def h_switch(self):
        if self.is_left:
            self.connection.write(COMMAND_RIGHT)
        else:
            self.connection.write(COMMAND_LEFT)
        self.is_left = not self.is_left
        return True

    def v_switch(self):
        if self.is_top:
            self.connection.write(COMMAND_BOTTOM)
        else:
            self.connection.write(COMMAND_TOP)
        self.is_top = not self.is_top
        return True

    def home(self, abort=False):
        if not abort:
            self.exit_compact_mode_finish()
        self.connection.send(b'IPP')
        self.current_x = 0
        self.current_y = 0
        self.reset_modes()
        self.state = STATE_DEFAULT

    def lock_rail(self, abort=False):
        if not abort:
            self.exit_compact_mode_finish()
        self.connection.send(b'IS1P')

    def unlock_rail(self, abort=False):
        if not abort:
            self.exit_compact_mode_finish()
        self.connection.send(b'IS2P')

    def abort(self):
        self.connection.send(b'I')

    # Do not call anything below this point directly.
    # These assume machine states that may not be verified.

    def reset_modes(self):
        self.is_on = False
        self.is_left = False
        self.is_top = False
        self.is_speed = False
        self.set_step = None
        self.set_speed_value = None
        self.set_speed_code = None
        self.is_cut = False
        self.is_harmonic = False

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
        if dx < 0 and not self.is_left:  # left
            self.move_left()
        if dx > 0 and self.is_left:  # right
            self.move_right()
        if dy < 0 and not self.is_top:  # top
            self.move_top()
        if dy > 0 and self.is_top:  # bottom
            self.move_bottom()
        self.current_x += dx
        self.current_y += dy
        self.check_bounds()
        self.connection.write(COMMAND_ANGLE)
        self.connection.write(self.encode_distance(abs(dy)))  # dx == dy

    def declare_directions(self):
        if self.is_top:
            self.connection.write(COMMAND_TOP)
        else:
            self.connection.write(COMMAND_BOTTOM)
        if self.is_left:
            self.connection.write(COMMAND_LEFT)
        else:
            self.connection.write(COMMAND_RIGHT)

    def move_right(self, dx=0):
        self.current_x += dx
        if self.is_harmonic and self.is_left:
            # TODO: Properly account for the distance of diagonal
            if self.is_top:
                self.current_y -= self.set_step
            else:
                self.current_y += self.set_step
            self.is_on = False
        self.is_left = False
        self.connection.write(COMMAND_RIGHT)
        if dx != 0:
            self.connection.write(self.encode_distance(abs(dx)))
            self.check_bounds()

    def move_left(self, dx=0):
        self.current_x -= abs(dx)
        if self.is_harmonic and not self.is_left:
            # TODO: Properly account for the distance of diagonal
            if self.is_top:
                self.current_y -= self.set_step
            else:
                self.current_y += self.set_step
            self.is_on = False
        self.is_left = True
        self.connection.write(COMMAND_LEFT)
        if dx != 0:
            self.connection.write(self.encode_distance(abs(dx)))
            self.check_bounds()

    def move_bottom(self, dy=0):
        self.current_y += dy
        if self.is_harmonic and self.is_top:
            # TODO: Properly account for the distance of diagonal, and difference with Top/Bottom transitions
            if self.is_left:
                self.current_x -= self.set_step
            else:
                self.current_x += self.set_step
            self.is_on = False
        self.is_top = False
        self.connection.write(COMMAND_BOTTOM)
        if dy != 0:
            self.connection.write(self.encode_distance(abs(dy)))
            self.check_bounds()

    def move_top(self, dy=0):
        self.current_y -= abs(dy)
        self.is_top = True
        if self.is_harmonic and not self.is_top:
            # TODO: Properly account for the distance of diagonal, and difference with Top/Bottom transitions
            if self.is_left:
                self.current_x -= self.set_step
            else:
                self.current_x += self.set_step
            self.is_on = False
        self.connection.write(COMMAND_TOP)
        if dy != 0:
            self.connection.write(self.encode_distance(abs(dy)))
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
