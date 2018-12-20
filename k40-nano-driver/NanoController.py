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
    def __init__(self, connect=None, board=None):
        self.connection = connect
        if self.connection is None:
            self.connection = NanoConnection()
        self.connection.connect()
        self.board = board
        if self.board is None:
            self.board = LaserM2()

        self.Modal_dir = 0
        self.Modal_dist = 0
        self.Modal_on = False
        self.Modal_AX = 0
        self.Modal_AY = 0

        self.INIT = b'I'
        self.END = b'S1P'
        self.RIGHT = b'B'  # ord("B")=66
        self.LEFT = b'T'  # ord("T")=84
        self.UP = b'L'  # ord("L")=76
        self.DOWN = b'R'  # ord("R")=82
        self.ANGLE = b'M'  # ord("M")=77
        self.ON = b'D'  # ord("D")=68
        self.OFF = b'U'  # ord("U")=85

        self.proper_x = 0
        self.proper_y = 0
        self.proper_index = 0

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

    def write_raw(self, data):
        """
        This is just to help work with the utilities helper that has existing code that insists on using raw data writes
        without any context as to what those elements actually do or mean. They should properly be added to here and
        nothing should ever write_raw.

        :param data:
        :return:
        """
        # Properly all the NanoUtility stuff must be turned into proper controller commands.
        pass

    def rapid_move(self, dxmils, dymils):
        if dxmils != 0 or dymils != 0:
            self.make_move_data(dxmils, dymils)

    def move(self, direction, distance, laser_on=False, angle_dirs=None):
        if angle_dirs is None:
            angle_dirs = [self.Modal_AX, self.Modal_AY]

        if direction == self.Modal_dir \
                and laser_on == self.Modal_on \
                and angle_dirs[0] == self.Modal_AX \
                and angle_dirs[1] == self.Modal_AY:
            self.Modal_dist = self.Modal_dist + distance

        else:
            self.update_position_to_modes()
            if laser_on != self.Modal_on:
                if laser_on:
                    self.connection.append(self.ON)
                else:
                    self.connection.append(self.OFF)
                self.Modal_on = laser_on

            if direction == self.ANGLE:
                if angle_dirs[0] != self.Modal_AX:
                    self.connection.append(angle_dirs[0])
                    self.Modal_AX = angle_dirs[0]
                if angle_dirs[1] != self.Modal_AY:
                    self.connection.append(angle_dirs[1])
                    self.Modal_AY = angle_dirs[1]

            self.Modal_dir = direction
            self.Modal_dist = distance

            if direction == self.RIGHT or direction == self.LEFT:
                self.Modal_AX = direction
            if direction == self.UP or direction == self.DOWN:
                self.Modal_AY = direction

    def update_position_to_modes(self, laser_on=None):
        if self.Modal_dist > 0:
            self.connection.append(bytes(bytearray(self.Modal_dir)))
            self.connection.append(bytes(bytearray(self.make_distance_command(self.Modal_dist))))
        if laser_on is not None and laser_on != self.Modal_on:
            if laser_on:
                self.connection.append(self.ON)
            else:
                self.connection.append(self.OFF)
            self.Modal_on = laser_on
        self.Modal_dist = 0

    def make_distance_command(self, dist_mils):
        dist_mils = float(dist_mils)
        if abs(dist_mils - round(dist_mils, 0)) > 0.000001:
            raise Exception('Distance values should be integer value (inches*1000)')
        DIST = 0.0
        code = ""
        v122 = 255
        dist_milsA = int(dist_mils)

        for i in range(0, int(floor(dist_mils / v122))):
            code += chr(122)
            dist_milsA = dist_milsA - v122
            DIST = DIST + v122
        if dist_milsA == 0:
            pass
        elif dist_milsA < 26:  # codes  "a" through  "y"
            code += chr(96 + dist_milsA)
        elif dist_milsA < 52:  # codes "|a" through "|z"
            code += chr(124)
            code += chr(96 + dist_milsA - 25)
        elif dist_milsA < 255:
            code += "%03d" % (int(round(dist_milsA)))
        else:
            raise Exception("Error in EGV make_distance_in(): dist_milsA=", dist_milsA)
        return code

    def make_dir_dist(self, dxmils, dymils, laser_on=False):
        self.proper_x += dxmils
        self.proper_y += dymils
        self.proper_index += 1
        print(self.proper_index, " dir ", dxmils, " ", dymils, " : ", self.proper_x, " ", self.proper_y)
        adx = abs(dxmils)
        ady = abs(dymils)
        if adx > 0 or ady > 0:
            if ady > 0:
                if dymils > 0:
                    self.move(self.UP, ady, laser_on)
                else:
                    self.move(self.DOWN, ady, laser_on)
            if adx > 0:
                if dxmils > 0:
                    self.move(self.RIGHT, adx, laser_on)
                else:
                    self.move(self.LEFT, adx, laser_on)

    def make_cut_line(self, dxmils, dymils, laser_on):
        self.proper_x += dxmils
        self.proper_y += dymils
        self.proper_index += 1
        print(self.proper_index, " cut ", dxmils, " ", dymils, " : ", self.proper_x, " ", self.proper_y)
        XCODE = self.RIGHT
        if dxmils < 0.0:
            XCODE = self.LEFT
        YCODE = self.UP
        if dymils < 0.0:
            YCODE = self.DOWN

        if abs(dxmils - round(dxmils, 0)) > 0.0 or abs(dymils - round(dymils, 0)) > 0.0:
            raise Exception('Distance values should be integer value (inches*1000)')

        adx = abs(dxmils / 1000.0)
        ady = abs(dymils / 1000.0)

        if dxmils == 0:
            self.move(YCODE, abs(dymils), laser_on=laser_on)
        elif dymils == 0:
            self.move(XCODE, abs(dxmils), laser_on=laser_on)
        elif dxmils == dymils:
            self.move(self.ANGLE, abs(dxmils), laser_on=laser_on, angle_dirs=[XCODE, YCODE])
        else:
            h = []
            if adx > ady:
                slope = ady / adx
                n = int(abs(dxmils))
                CODE = XCODE
                CODE1 = YCODE
            else:
                slope = adx / ady
                n = int(abs(dymils))
                CODE = YCODE
                CODE1 = XCODE

            for i in range(1, n + 1):
                h.append(round(i * slope, 0))

            Lh = 0.0
            d1 = 0.0
            d2 = 0.0
            d1cnt = 0.0
            d2cnt = 0.0
            for i in range(len(h)):
                if h[i] == Lh:
                    d1 += 1
                    if d2 > 0.0:
                        self.move(self.ANGLE, d2, laser_on=laser_on, angle_dirs=[XCODE, YCODE])
                        d2cnt = d2cnt + d2
                        d2 = 0.0
                else:
                    d2 += 1
                    if d1 > 0.0:
                        self.move(CODE, d1, laser_on=laser_on)
                        d1cnt = d1cnt + d1
                        d1 = 0.0
                Lh = h[i]

            if d1 > 0.0:
                self.move(CODE, d1, laser_on=laser_on)
                d1cnt = d1cnt + d1
                d1 = 0.0
            if d2 > 0.0:
                self.move(self.ANGLE, d2, laser_on=laser_on, angle_dirs=[XCODE, YCODE])
                d2cnt = d2cnt + d2
                d2 = 0.0

            DX = d2cnt
            DY = (d1cnt + d2cnt)
            if adx < ady:
                error = max(DX - abs(dxmils), DY - abs(dymils))
            else:
                error = max(DY - abs(dxmils), DX - abs(dymils))
            if error > 0:
                raise Exception("egv.py: Error delta =%f" % error)

    def make_move_data(self, dx_mm, dy_mm):
        if (abs(dx_mm) + abs(dy_mm)) > 0:
            self.connection.append(self.INIT)  # I
            self.make_dir_dist(dx_mm, dy_mm)
            self.update_position_to_modes()
            self.connection.append(self.END)  # S, 1, P

    def rapid_move_slow(self, dx, dy):
        self.make_dir_dist(dx, dy)

    def rapid_move_fast(self, dx, dy):
        pad = 3
        if pad == -dx:
            pad += 3
        self.make_dir_dist(-pad, 0)  # add "T" move
        self.make_dir_dist(0, pad)  # add "L" move
        self.update_position_to_modes(laser_on=False)

        if dx + pad < 0.0:
            self.connection.append(b'B')
        else:
            self.connection.append(b'T')
        self.connection.append(b'N')
        self.make_dir_dist(dx + pad, dy - pad)
        self.update_position_to_modes(laser_on=False)
        self.connection.append(b'S')
        self.connection.append(b'E')

    def change_speed(self, feed, board=None, laser_on=False):
        if board is None:
            board = self.board
        cspad = 5
        if laser_on:
            self.connection.append(self.OFF)

        self.make_dir_dist(-cspad, -cspad)
        self.update_position_to_modes(laser_on=False)

        self.connection.append(b'@NSE')
        speed = board.make_speed(feed)
        self.connection.append(bytes(speed, "UTF-8"))
        self.connection.append(b'NRB')
        ## Insert "SIE"
        self.connection.append(b'S1E')

        self.make_dir_dist(cspad, cspad)
        self.update_position_to_modes(laser_on=False)

        if laser_on:
            self.connection.append(self.ON)

    def move_position(self,dx=0, dy=0):
        if dx == 0 and dy == 0:
            return;
        self.connection.append(self.INIT)
        if dy != 0:
            if dy > 0:
                self.connection.append(self.DOWN)
            else:
                self.connection.append(self.UP)
            self.connection.append(self.make_distance_command(abs(dy)))
        if dx != 0:
            if dx > 0:
                self.connection.append(self.RIGHT)
            else:
                self.connection.append(self.LEFT)
            self.connection.append(self.make_distance_command(abs(dx)))
        self.connection.append(self.END)
        self.connection.write_buffer()
        
    def move_down(self, distance=50):
        self.connection.append(self.INIT)
        self.connection.append(self.DOWN)
        self.connection.append(self.make_distance_command(distance))
        self.connection.append(self.END)
        self.connection.write_buffer()
        
    def move_up(self, distance=50):
        self.connection.append(self.INIT)
        self.connection.append(self.UP)
        self.connection.append(self.make_distance_command(distance))
        self.connection.append(self.END)
        self.connection.write_buffer()
    
    def move_right(self, distance=50):
        self.connection.append(self.INIT)
        self.connection.append(self.RIGHT)
        self.connection.append(self.make_distance_command(distance))
        self.connection.append(self.END)
        self.connection.write_buffer()
        
    def move_left(self, distance=50):
        self.connection.append(self.INIT)
        self.connection.append(self.LEFT)
        self.connection.append(self.make_distance_command(distance))
        self.connection.append(self.END)
        self.connection.write_buffer()
        
    def release(self):
        self.connection.disconnect()


if __name__ == "__main__":
    controller = NanoController()
    controller.hello()
    controller.home_position()
    controller.move_position(5000,2000)
    controller.release()
