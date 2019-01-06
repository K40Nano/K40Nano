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

import usb.core
import usb.util


class NanoUsb:
    def __init__(self):
        self.PACKET_SIZE = 30
        self.TIMEOUT = 300  # Time in milliseconds
        self.WRITE_ADDRESS = 0x2  # Write address
        self.READ_ADDRESS = 0x82  # Read address
        self.READ_LENGTH = 168
        self.device = None

    def initialize(self):
        """
        Attempts to initializes the K40 device.

        :param
        :return:
        """
        try:
            self.release_usb()
        except:
            pass
        try:
            self.device = usb.core.find(idVendor=0x1a86, idProduct=0x5512)
        except ValueError:
            raise IOError("USB backend could not be found by pyusb.")
        if self.device is None:
            raise IOError("Laser USB Device not found.")
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        try:
            self.device.set_configuration()
        except:
            raise IOError("Unable to set USB Device configuration.")
        # get an endpoint instance
        configuration = self.device.get_active_configuration()
        intf = configuration[(0, 0)]
        descriptor = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        if descriptor is None:
            raise IOError("Unable to match the USB 'OUT' endpoint.")
        self.device.ctrl_transfer(0x40, 177, 0x0102, 0, 0, 2000)

    def reset_usb(self):
        self.device.reset()

    def release_usb(self):
        usb.util.dispose_resources(self.device)
        self.device = None

    def read(self):
        return self.device.read(self.READ_ADDRESS, self.READ_LENGTH, self.TIMEOUT)[1]

    def write(self, packet):
        self.device.write(self.WRITE_ADDRESS, packet, self.TIMEOUT)


if __name__ == "__main__":
    connection = NanoUsb()
    connection.initialize()
    connection.write([160])
    connection.write([166, 0, 73, 80, 80, 70, 70, 70,
                      70, 70, 70, 70, 70, 70, 70, 70,
                      70, 70, 70, 70, 70, 70, 70, 70,
                      70, 70, 70, 70, 70, 70, 70, 70,
                      166, 228])
