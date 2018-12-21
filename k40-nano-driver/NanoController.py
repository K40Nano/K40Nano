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

from LaserM2 import *
from NanoConnection import *


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

        # % Yxtart % Xstart % Yend % Xend % I % C VXXXXXXX CUT_TYPE
        #
        # %Ystart_pos %Xstart_pos %Yend_pos %Xend_pos  (start pos is the location of the head before the code is run)
        # I is always I ?
        # C is C for cutting or Marking otherwise it is omitted
        # V is the start of 7 digits indicating the feed rate 255 255 1
        # CUT_TYPE cutting/marking, Engraving=G followed by the raster step in thousandths of an inch

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

    def change_speed(self, feed):
        if feed == self.state_speed:
            return  # speed is not changing.
        self.state_speed = feed
        self.connection.append(b'@NSE')
        speed = self.board.make_speed(feed)
        self.connection.append(bytes(speed))
        self.connection.append(b'NRBS1E')

    def change_laser(self, laser):
        if laser == self.state_laser:
            return  # laser is not changing.
        self.state_laser = laser
        if laser:
            self.connection.append(self.ON)
        else:
            self.connection.append(self.OFF)

    def change_position(self, x, y):
        if x == self.state_x_position and y == self.state_y_position:
            return  # this is current position
        self.connection.append(self.INIT)
        dy = y - self.state_y_position
        dx = x - self.state_x_position
        self.state_x_position = x
        self.state_y_position = y
        if dx != 0 and dy != 0:
            self.connection.append(self.encode_line(dx, dy))
        else:
            if dy != 0:
                if dy > 0:
                    self.state_y_direction = 1
                    self.connection.append(self.DOWN)
                else:
                    self.state_y_direction = -1
                    self.connection.append(self.UP)
                self.connection.append(self.encode_distance(abs(dy)))
            if dx != 0:
                if dx > 0:
                    self.state_x_direction = 1
                    self.connection.append(self.RIGHT)
                else:
                    self.state_y_direction = -1
                    self.connection.append(self.LEFT)
                self.connection.append(self.encode_distance(abs(dx)))
        self.connection.append(self.END)
        self.connection.write_buffer()

    def move_position(self, dx=0, dy=0):
        self.change_position(self.state_x_position + dx, self.state_y_position + dy)

    def encode_line(self, dx, dy):
        # BRESENHAM LINE DRAW ALGORITHM
        code = ""
        x = self.state_x_position
        y = self.state_y_position
        if dy < 0:
            dy = -dy
            step_y = -1
            code_y = self.UP
            code += code_y
        else:
            step_y = 1
            code_y = self.DOWN
            code += code_y
        if dx < 0:
            dx = -dx
            step_x = -1
            code_x = self.LEFT
            code += code_x
        else:
            step_x = 1
            code_x = self.RIGHT
            code += code_x
        if dx > dy:
            dy <<= 1  # dy is now 2*dy
            dx <<= 1
            fraction = dy - (dx >> 1)  # same as 2*dy - dx
            while x != dx:
                if fraction >= 0:
                    y += step_y
                    fraction -= dx  # same as fraction -= 2*dx
                    code += code_y
                    code += self.encode_distance(1)
                code += code_x
                code += self.encode_distance(1)
                x += step_x
                fraction += dy  # same as fraction += 2*dy
        else:
            dy <<= 1  # dy is now 2*dy
            dx <<= 1  # dx is now 2*dx
            fraction = dx - (dy >> 1)
            while y != dy:
                if fraction >= 0:
                    x += step_x
                    fraction -= dy
                    code += code_x
                    code += self.encode_distance(1)
                code += code_y
                code += self.encode_distance(1)
                y += step_y
                fraction += dx
        return code

    def move_down(self, distance):
        self.rapid_move(0,distance)

    def move_up(self, distance=50):
        self.rapid_move(0,-distance)

    def move_right(self, distance=50):
        self.rapid_move(distance, 0)

    def move_left(self, distance=50):
        self.rapid_move(-distance,0)
        
    def rapid_move(self, dx, dy):
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
        
        
    def read_egv(self,filemname):
        value1 = ""
        value2 = ""
        value3 = ""
        value4 = ""
        data=""
        #value1 and value2 are the absolute y and x starting positions
        #value3 and value4 are the absolute y and x end positions
        with open(filemname) as f:
            while True:
                ## Skip header
                c = f.read(1)
                while c!="%" and c:
                    c = f.read(1)
                ## Read 1st Value
                c = f.read(1)
                while c!="%" and c:
                    value1 = value1 + c
                    c = f.read(1)
                y_start_mils = int(value1) 
                ## Read 2nd Value
                c = f.read(1)
                while c!="%" and c:
                    value2 = value2 + c
                    c = f.read(1)
                x_start_mils = int(value2)   
                ## Read 3rd Value
                c = f.read(1)
                while c!="%" and c:
                    value3 = value3 + c
                    c = f.read(1)
                y_end_mils = int(value3)
                ## Read 4th Value
                c = f.read(1)
                while c!="%" and c:
                    value4 = value4 + c
                    c = f.read(1)
                x_end_mils = int(value4)
                break

            ## Read Data
            while True:
                c = f.read(1)
                if not c:
                    break
                if c=='\n' or c==' ' or c=='\r':
                    pass
                else:
                    self.connection.append(c);
        self.connection.write_buffer()
        controller.wait()
        #rapid move back to starting position
        dxmils = -(x_end_mils - x_start_mils)
        dymils =   y_end_mils - y_start_mils
        self.rapid_move(dxmils,dxmils)
    

if __name__ == "__main__":
    controller = NanoController()
    #controller.home_position()
    controller.rapid_move(-500,500)
    controller.read_egv("test_engrave.EGV")
    controller.rapid_move(1000,1000)
    controller.read_egv("test_engrave.EGV")
    controller.release()
