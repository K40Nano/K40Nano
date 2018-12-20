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

import time

from NanoUsb import NanoUsb

#from MockUsb import MockUsb


def crc_8bit_onewire(line):
    """
    The one wire CRC algorithm is derived from the OneWire.cpp Library
    The latest version of this library may be found at:
    http://www.pjrc.com/teensy/td_libs_OneWire.html
    """
    crc = 0
    for in_byte in line:
        in_byte = ord(in_byte)
        for j in range(8):
            mix = (crc ^ in_byte) & 0x01
            crc >>= 1
            if mix:
                crc ^= 0x8C
            in_byte >>= 1
    return crc


class NanoConnection:
    def __init__(self):
        self.PACKET_SIZE = 30
        self.buffer = []
        self.position = 0

        self.MAX_ERRORS = 10
        self.MAX_TIMEOUTS = 10
        self.TIMEOUT = 500  # Time in milliseconds
        self.WRITE_ADDRESS = 0x2  # Write address
        self.READ_ADDRESS = 0x82  # Read address
        self.READ_LENGTH = 168

        self.HELLO = [160]

        # RESPONSE CODES
        self.RESPONSE_OK = 206
        self.RESPONSE_BUFFER_FULL = 238
        self.RESPONSE_CRC_ERROR = 207
        self.RESPONSE_TASK_COMPLETE = 236
        self.RESPONSE_UNKNOWN_2 = 239  # after failed initialization followed by successful initialization
        self.RESPONSE_ERROR_UNKNOWN = 9999  # Unknown response.
        self.usb = None

    def write(self, data):
        """
        Writes the data to the K40 device, encoding that data internally into packets, validates those packets
        and performs the resends as needed..

        :param data:
        :return:
        """
        if isinstance(data, bytes):
            data = list(data)  # If the data was written properly as a bytes object we convert that to an int list.
        size = self.PACKET_SIZE
        data = self.buffer + data
        chunks = [data[i:i + size] for i in range(0, len(data), size)]
        for chunk in chunks:
            self.send_valid_packet(chunk)

    def write_completed_packets(self, data):
        if isinstance(data, bytes):
            data = list(data)  # If the data was written properly as a bytes object we convert that to an int list.
        size = self.PACKET_SIZE
        data = self.buffer + data
        chunks = [data[i:i + size] for i in range(0, len(data), size)]
        for chunk in chunks[:-1]:
            self.send_valid_packet(chunk)
        self.buffer = chunks[-1]
        if len(self.buffer) == self.PACKET_SIZE:
            self.send_valid_packet(self.buffer)
            self.buffer = []

    def write_buffer(self):
        """
        Blocks while waiting for the K40 device to return TASK_COMPLETE to the check status.
        :return:
        """
        if self.buffer is None or len(self.buffer) == 0:
            return
        self.send_valid_packet(self.buffer)  # Send non-completed packet.
        self.buffer = []

    def append_buffer(self, data):
        self.buffer += data

    def connect(self):
        self.usb = NanoUsb()
        # self.usb = MockUsb()
        self.usb.initialize()

    def disconnect(self):
        self.usb.release_usb()

    def make_valid_packet(self, packet):
        """
        :param packet: list of integers.
        :return:
        """
        while len(packet) < self.PACKET_SIZE:
            packet += b'F'
        crc = crc_8bit_onewire(packet)
        for i in range(0, len(packet)):
            packet[i] = ord(packet[i])
        return [166, 0] + packet + [166, crc]

    def send_valid_packet(self, packet):
        if isinstance(packet, str):
            packet = list(packet)
        valid_packet = self.make_valid_packet(packet)
        self.send_packet(bytes(valid_packet))

    def send_packet(self, packet):
        """
        Creates a valid packet and attempts to send it, resending on timeout and CRC error.

        This should not be called directly.

        :param packet: 0-30 bytes as int list.
        :return:
        """
        timeout_count = 0
        error_count = 0
        buffer_count = 0
        while True:
            try:
                self.usb.write(packet)
                break
            except Exception:
                timeout_count += 1
                if timeout_count >= self.MAX_TIMEOUTS:
                    print("Timed Out ", timeout_count)
                    raise Exception
            response = self.read_response()
            if response == self.RESPONSE_OK:
                break  # break to move on to next packet
            elif response == self.RESPONSE_BUFFER_FULL:
                buffer_count += 1
                time.sleep(0.01)  # Wait 0.01 seconds and try again.
                continue
            elif response == self.RESPONSE_CRC_ERROR:
                error_count += 1
                if error_count < self.MAX_ERRORS:
                    raise IOError
                continue
            elif response is None:
                # The controller board is not reporting status. but we will
                # assume things are going OK. until we cannot transmit to the controller.
                break  # break to move on to next packet
            break  # Unknown/Unhandled response.

    def send_hello(self):
        """
        Checks the status response after sending a HELLO, retrying as necessary.
        :return: status response.
        """
        self.send_packet(self.HELLO)
        return self.read_response()

    def read_response(self):
        """
        Reads the status response from the device, retrying as necessary.
        :return: status response.
        """
        read_count = 0
        while True:
            try:
                response = self.usb.read()
                if response == self.RESPONSE_OK:
                    return response
                elif response == self.RESPONSE_BUFFER_FULL:
                    return response
                elif response == self.RESPONSE_TASK_COMPLETE:
                    return response
                elif response == self.RESPONSE_UNKNOWN_2:
                    return response
                return self.RESPONSE_ERROR_UNKNOWN
            except:
                read_count += 1
                if read_count >= self.MAX_TIMEOUTS:
                    return None


if __name__ == "__main__":
    connection = NanoConnection()
    connection.connect()
    print(connection.send_hello())
    connection.write(b'IPP')
    connection.disconnect()
