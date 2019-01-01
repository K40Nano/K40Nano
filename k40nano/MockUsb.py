#!/usr/bin/env python

"""
This script uses a stream to communicate with the K40 Laser Cutter.

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
from __future__ import print_function


class MockUsb:
    def __init__(self):
        self.device = None
        self.finish = 0

    def initialize(self):
        """
        Attempts to initializes the K40 device.

        :param
        :return:
        """
        print("Mock Device Initialized")
        print("----")
        print("The pyusb module didn't load, so MockUsb has been loaded.")
        print("This is merely for testing purposes. There is no connection.")
        print("Connection requires pyusb and a working backend driver.")
        print("----")
        self.device = self

    def reset_usb(self):
        print("Device Reset")

    def release_usb(self):
        self.device = None
        print("Device Released")

    def read(self):
        return self.device.get_mock_read_value()

    def write(self, packet):
        self.device.do_mock_write(packet)

    def get_mock_read_value(self):
        self.finish -= 1
        if self.finish == 0:
            return 236
        return 206

    def do_mock_write(self, packet):
        ps = ""
        for p in packet:
            ps += chr(p)
        if "F" in ps:
            self.finish = 10
        print(ps, " ", packet)


if __name__ == "__main__":
    connection = MockUsb()
    connection.initialize()
    connection.write([160])
    connection.write([166, 0, 73, 80, 80, 70, 70, 70,
                      70, 70, 70, 70, 70, 70, 70, 70,
                      70, 70, 70, 70, 70, 70, 70, 70,
                      70, 70, 70, 70, 70, 70, 70, 70,
                      166, 228])
