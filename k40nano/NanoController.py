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

from .LaserM2 import LaserM2
from .NanoConnection import NanoConnection
from .NanoTransaction import NanoTransaction


class NanoController:
    def __init__(self, connect=None, laser_board=None):
        self.connection = connect
        if self.connection is None:
            self.connection = NanoConnection()
        self.connection.connect()
        self.board = laser_board
        if self.board is None:
            self.board = LaserM2()
        self.max_x = 0
        self.max_y = 0
        self.min_x = 0
        self.min_y = 0
        self.current_x = 0
        self.current_y = 0

        self.speedcode = None
        self.speed = None
        self.raster_step = 0

    def start(self):
        transaction = NanoTransaction(self, self.board)
        transaction.current_x = self.current_x
        transaction.current_y = self.current_y
        transaction.speedcode = self.speedcode
        transaction.speed = self.speed
        transaction.raster_step = self.raster_step
        transaction.start()
        return transaction

    def write(self, data):
        self.connection.write_completed_packets(data)

    def close(self, transaction=None):
        if transaction is not None:
            self.current_x = transaction.current_x
            self.current_y = transaction.current_y
            self.speed = transaction.speed
            self.speedcode = transaction.speedcode
            self.raster_step = transaction.raster_step
        self.connection.write_buffer()

    def home(self):
        transaction = self.start()
        transaction.write("P")
        transaction.pop()
        self.current_x = 0
        self.current_y = 0

    def rail(self, lock=False):
        transaction = self.start()
        if not lock:
            transaction.write("S2")
        else:
            transaction.write("S1")
        transaction.pop()

    def wait(self):
        self.connection.wait()

    def halt(self):
        transaction = self.start()
        self.close(transaction)

    def finish(self):
        self.connection.write_buffer()
        self.connection.disconnect()
