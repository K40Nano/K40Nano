#!/usr/bin/env python

# MIT License.

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
        if self.device is None:
            print("Device already released.")
        else:
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
