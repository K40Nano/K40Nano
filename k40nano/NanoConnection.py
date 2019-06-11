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

try:
    from .NanoUsb import NanoUsb as Usb
except:
    from .MockUsb import MockUsb as Usb

from .Connection import Connection

crc_table = [
    0x00, 0x5E, 0xBC, 0xE2, 0x61, 0x3F, 0xDD, 0x83,
    0xC2, 0x9C, 0x7E, 0x20, 0xA3, 0xFD, 0x1F, 0x41,
    0x00, 0x9D, 0x23, 0xBE, 0x46, 0xDB, 0x65, 0xF8,
    0x8C, 0x11, 0xAF, 0x32, 0xCA, 0x57, 0xE9, 0x74]


def onewire_crc_lookup(line):
    """
    License: 2-clause "simplified" BSD license
    Copyright (C) 1992-2017 Arjen Lentz
    https://lentz.com.au/blog/calculating-crc-with-a-tiny-32-entry-lookup-table

    :param line: line to be CRC'd
    :return: 8 bit crc of line.
    """
    crc = 0
    for i in range(2, 32):
        crc = line[i] ^ crc
        crc = crc_table[crc & 0x0f] ^ crc_table[16 + ((crc >> 4) & 0x0f)]
    return crc


class NanoConnection(Connection):
    def __init__(self, usb=None):
        Connection.__init__(self)
        self.usb = usb
        self.PACKET_SIZE = 30
        self.buffer = b''
        self.position = 0

        self.MAX_ERRORS = 10
        self.MAX_TIMEOUTS = 10

        self.HELLO = [160]

        # RESPONSE CODES
        self.RESPONSE_OK = 206
        self.RESPONSE_BUSY = 238
        self.RESPONSE_CRC_ERROR = 207
        self.RESPONSE_TASK_COMPLETE = 236
        self.RESPONSE_POWER = 239
        self.RESPONSE_ERROR_UNKNOWN = 9999  # Unknown response.

    def send(self, data):
        """
        Writes all data immediately to the K40 device.
        :param data:
        :return:
        """
        self.write(data)
        self.flush()

    def write(self, data=None):
        """
        Buffers data, sending any complete packets to the device immediately to the K40 device.
        :param data:
        :return:
        """
        size = self.PACKET_SIZE
        if data is None:
            data = self.buffer
        else:
            if isinstance(data, str):
                data = data.encode("utf-8")
            data = self.buffer + data
        chunks = [data[i:i + size] for i in range(0, len(data), size)]
        for chunk in chunks[:-1]:
            self.send_valid_packet(chunk)
        self.buffer = chunks[-1]
        if len(self.buffer) == self.PACKET_SIZE:
            self.send_valid_packet(self.buffer)
            self.buffer = b''

    def flush(self):
        """
        Writes all buffered data immediately.
        :param data:
        :return:
        """
        if len(self.buffer) == 0:
            return
        data = self.buffer
        size = self.PACKET_SIZE
        chunks = [data[i:i + size] for i in range(0, len(data), size)]
        for chunk in chunks:
            self.send_valid_packet(chunk)
        self.buffer = b''

    def buffer(self, data):
        """
        Appends data to the buffer.
        :param data:
        :return:
        """
        self.buffer += data

    def open(self):
        """
        Connects to the USB device.
        """
        if self.usb is None:
            self.usb = Usb()
        self.usb.initialize()

    def close(self):
        """
        Disconnects from USB device.
        """
        self.flush()
        self.usb.release_usb()

    def make_valid_packet(self, packet):
        p = [166] + [0] + ([ord('F')] * self.PACKET_SIZE) + [166] + [0]
        for i in range(0, len(packet)):
            v = packet[i]
            if isinstance(v, str):  # if python_2
                v = ord(v)
            p[i + 2] = v
        crc = onewire_crc_lookup(p)
        p[33] = crc
        return p

    def send_valid_packet(self, packet):
        """
        Sends the validated version of packet to the USB immediately
        :param packet: packet to be validated and sent.
        :return:
        """
        if isinstance(packet, str):
            packet = list(packet)
        valid_packet = self.make_valid_packet(packet)
        self.send_packet(valid_packet)

    def send_raw_packet(self, packet):
        """
        Sends the packet to the USB immediately. No attempt to validate or resend is made.

        :param packet: 0-30 bytes as int list.
        :return:
        """
        self.usb.write(packet)

    def send_packet(self, packet):
        """
        Attempts to send packet, resending on timeout and CRC error.

        :param packet: 0-30 bytes as int list.
        :return:
        """
        timeout_count = 0
        error_count = 0
        buffer_count = 0
        while True:
            response = self.send_hello()
            if response == self.RESPONSE_OK or response == self.RESPONSE_CRC_ERROR:
                pass  # Ready to send packet.
            elif response == self.RESPONSE_BUSY or response == self.RESPONSE_POWER:
                buffer_count += 1
                time.sleep(0.1)  # Wait 0.1 seconds and try again.
                continue  # Cannot send packet.
            try:
                self.usb.write(packet)
            except IOError:
                timeout_count += 1
                if timeout_count >= self.MAX_TIMEOUTS:
                    raise Exception

            response = self.send_hello()
            if response == self.RESPONSE_CRC_ERROR:
                error_count += 1
                if error_count < self.MAX_ERRORS:
                    raise IOError
                continue  # must resend.
            break

    def wait(self):
        """
        Waits for task complete.
        """
        timeout_count = 0
        while True:
            response = self.send_hello()
            if response == self.RESPONSE_TASK_COMPLETE:
                break
            timeout_count += 1
            time.sleep(0.1)

    def send_hello(self):
        """
        Checks the status response after sending a HELLO, retrying as necessary.
        :return: status response.
        """
        timeout_count = 0
        while True:
            try:
                self.usb.write(self.HELLO)
            except IOError:
                timeout_count += 1
                if timeout_count >= self.MAX_TIMEOUTS:
                    return None
            return self.read_response()

    def read_response(self):
        """
        Reads the status response from the device.
        :return: status response.
        """
        while True:
            try:
                response = self.usb.read()
                if response == self.RESPONSE_OK:
                    return response
                elif response == self.RESPONSE_BUSY:
                    return response
                elif response == self.RESPONSE_TASK_COMPLETE:
                    return response
                elif response == self.RESPONSE_POWER:
                    return response
                return response
            except IOError:
                return None
