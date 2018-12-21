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

from .LaserM2 import *
from .NanoConnection import *


class NanoController:
    def __init__(self, connect=None, laser_board=None):
        self.connection = connect
        if self.connection is None:
            self.connection = NanoConnection()
        self.connection.connect()
        self.board = laser_board
        if self.board is None:
            self.board = LaserM2()

        self.state_x_position = 0
        self.state_y_position = 0
        self.state_y_direction = 0
        self.state_x_direction = 0
        self.state_laser = False
        self.state_speed = None

        self.INIT = b'I'
        self.END = b'S1P'
        self.RIGHT = b'B'  # ord("B")=66
        self.LEFT = b'T'  # ord("T")=84
        self.UP = b'L'  # ord("L")=76
        self.DOWN = b'R'  # ord("R")=82
        self.ANGLE = b'M'  # ord("M")=77
        self.ON = b'D'  # ord("D")=68
        self.OFF = b'U'  # ord("U")=85

    def unlock_rail(self):
        self.connection.send_valid_packet(b'IS2P')

    def e_stop(self):
        self.connection.send_valid_packet(b'I')

    def home_position(self):
        self.connection.send_valid_packet(b'IPP')

    def hello(self):
        self.connection.send_hello()

    @staticmethod
    def encode_distance(distance_mils):
        if abs(distance_mils - round(distance_mils, 0)) > 0.000001:
            raise Exception('Distance values should be integer value (inches*1000)')
        distance_mils = int(distance_mils)
        code = ""
        value_z = 255

        while distance_mils >= 255:
            code += 'z'
            distance_mils -= value_z
        if distance_mils == 0:
            return code
        elif distance_mils < 26:  # codes  "a" through  "y"
            return code + chr(96 + distance_mils)
        elif distance_mils < 52:  # codes "|a" through "|z"
            return code + '|' + chr(96 + distance_mils - 25)
        elif distance_mils < 255:
            code += "%03d" % distance_mils
            return code
        else:
            raise Exception("Could not create distance")  # This really shouldn't happen.

    def move_down(self, distance):
        self.move(0, distance)

    def move_up(self, distance=50):
        self.move(0, -distance)

    def move_right(self, distance=50):
        self.move(distance, 0)

    def move_left(self, distance=50):
        self.move(-distance, 0)

    def move(self, dx, dy):
        if dx == 0 and dy == 0:
            return
        self.connection.append(self.INIT)
        if dx > 0:
            self.connection.append(self.RIGHT)
            self.connection.append(self.encode_distance(abs(dx)))
        elif dx < 0:
            self.connection.append(self.LEFT)
            self.connection.append(self.encode_distance(abs(dx)))
        if dy > 0:
            self.connection.append(self.DOWN)
            self.connection.append(self.encode_distance(abs(dy)))
        elif dy < 0:
            self.connection.append(self.UP)
            self.connection.append(self.encode_distance(abs(dy)))
        self.connection.append(self.END)
        self.connection.write_buffer()

    def release(self):
        self.connection.disconnect()

    def wait(self):
        self.connection.wait()

    def read_egv(self, filename):
        value1 = ""
        value2 = ""
        value3 = ""
        value4 = ""
        data = ""
        # value1 and value2 are the absolute y and x starting positions
        # value3 and value4 are the absolute y and x end positions
        with open(filename) as f:
            while True:
                ## Skip header
                c = f.read(1)
                while c != "%" and c:
                    c = f.read(1)
                ## Read 1st Value
                c = f.read(1)
                while c != "%" and c:
                    value1 += c
                    c = f.read(1)
                y_start_mils = int(value1)
                ## Read 2nd Value
                c = f.read(1)
                while c != "%" and c:
                    value2 += c
                    c = f.read(1)
                x_start_mils = int(value2)
                ## Read 3rd Value
                c = f.read(1)
                while c != "%" and c:
                    value3 += c
                    c = f.read(1)
                y_end_mils = int(value3)
                ## Read 4th Value
                c = f.read(1)
                while c != "%" and c:
                    value4 += c
                    c = f.read(1)
                x_end_mils = int(value4)
                break

            ## Read Data
            while True:
                c = f.read(1)
                if not c:
                    break
                if c == '\n' or c == ' ' or c == '\r':
                    pass
                else:
                    self.connection.append(c)
        self.connection.write_buffer()
        self.connection.wait()
        # rapid move back to starting position
        dx_mils = -(x_end_mils - x_start_mils)
        dy_mils = y_end_mils - y_start_mils
        self.move(dx_mils, dy_mils)


if __name__ == "__main__":
    controller = NanoController()
    controller.home_position()
    controller.move(500, 500)
    controller.release()
