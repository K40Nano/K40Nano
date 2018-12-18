#!/usr/bin/env python

'''
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
'''
from __future__ import print_function

import io
import time

try:
    import usb.core
    import usb.util
except ImportError:
    print("Unable to load pyusb/USB library. (Sending data to Laser will not work.)")


#######################################################################
#  The one wire CRC algorithm is derived from the OneWire.cpp Library
#  The latest version of this library may be found at:
#  http://www.pjrc.com/teensy/td_libs_OneWire.html
#######################################################################
def crc_8bit_onewire(line):
    crc = 0
    for in_byte in line:
        for j in range(8):
            mix = (crc ^ in_byte) & 0x01
            crc >>= 1
            if mix:
                crc ^= 0x8C
            in_byte >>= 1
    return crc


class NanoStream(io.RawIOBase):

    def __init__(self):
        io.RawIOBase.__init__(self)

        self.PACKET_SIZE = 32
        self.EMPTY_PACKET = [166, 0, 70, 70, 70, 70, 70, 70,
                             70, 70, 70, 70, 70, 70, 70, 70,
                             70, 70, 70, 70, 70, 70, 70, 70,
                             70, 70, 70, 70, 70, 70, 70, 70,
                             166, 0]
        self.MAX_ERRORS = 10
        self.MAX_TIMEOUTS = 10
        self.TIMEOUT = 200  # Time in milliseconds
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
        self.RESPONSE_ERROR_CLOSED = 9998  # State is uninitialized.

        self.device = None
        self.initialize_device()

    def writable(self):
        return True

    def write(self, data):
        if self.closed:
            raise ValueError("Stream is closed.")
        if isinstance(data, bytes):
            data = list(data)
        size = self.PACKET_SIZE
        for chunk in [data[i:i + size] for i in range(0, len(data), size)]:
            self.send_valid_packet(chunk)

    def flush(self):
        io.RawIOBase.flush(self)
        if self.closed:
            return
        while True:
            response = self.check_status()
            if response == self.RESPONSE_OK:
                time.sleep(0.01)
                continue
            elif response == self.RESPONSE_TASK_COMPLETE:
                return
            elif response is None:
                raise IOError()

    def close(self):
        try:
            self.release_usb()
        except:
            pass
        io.RawIOBase.close(self)

    def valid_packet(self, packet):
        if isinstance(packet, list):
            if len(packet) == self.PACKET_SIZE:
                packet.append(166)
                packet.append(crc_8bit_onewire(packet))
            if len(packet) == self.PACKET_SIZE + 2:
                packet[32] = 166
                packet[33] = crc_8bit_onewire(packet)
        return packet

    def send_valid_packet(self, packet):
        size = self.PACKET_SIZE
        if len(packet) < size:
            packet = list(packet) + self.EMPTY_PACKET[len(packet):size]
        crc_packet = self.valid_packet(packet)
        timeout_count = 0
        error_count = 0
        buffer_count = 0
        while True:
            try:
                self.send_raw_packet(crc_packet)
            except:
                timeout_count += 1
                if timeout_count > self.MAX_TIMEOUTS:
                    raise TimeoutError()
                continue

            response = self.check_status()
            if response == self.RESPONSE_OK:
                break  # break to move on to next packet
            elif response == self.RESPONSE_BUFFER_FULL:
                buffer_count += 1
                time.sleep(0.01)  # Wait 0.01 seconds and try again.
                continue
            elif response == self.RESPONSE_CRC_ERROR:
                error_count += 1
                if error_count < self.MAX_ERRORS:
                    raise ConnectionError
                continue
            elif response is None:
                # The controller board is not reporting status. but we will
                # assume things are going OK. until we cannot transmit to the controller.
                break  # break to move on to next packet
            break  # Unknown/Unhandled response.

    def check_status(self):
        timeout_count = 0
        while True:
            try:
                self.send_raw_packet(self.HELLO)
                break
            except:
                timeout_count += 1
                if timeout_count >= self.MAX_TIMEOUTS:
                    raise IOError()
        return self.read_response()

    def read_response(self):
        read_count = 0
        while True:
            try:
                response = self.read_raw()
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
                    raise IOError()

    def reset_usb(self):
        self.device.reset()

    def release_usb(self):
        usb.util.dispose_resources(self.device)
        self.device = None

    def read_raw(self):
        return self.device.read(self.READ_ADDRESS, self.READ_LENGTH, self.TIMEOUT)[1]

    def send_raw_packet(self, packet):
        self.device.write(self.WRITE_ADDRESS, packet, self.TIMEOUT)

    def initialize_device(self, verbose=False):
        try:
            self.release_usb()
        except:
            pass
        # find the device
        try:
            self.device = usb.core.find(idVendor=0x1a86, idProduct=0x5512)
        except ValueError:
            raise IOError("USB backend could not be found by pyusb.")

        if self.device is None:
            raise IOError("Laser USB Device not found.")
            # return "Laser USB Device not found."

        if verbose:
            print("-------------- dev --------------")
            print(self.device)
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        try:
            self.device.set_configuration()
        except:
            # return "Unable to set USB Device configuration."
            raise IOError("Unable to set USB Device configuration.")

        # get an endpoint instance
        configuration = self.device.get_active_configuration()
        if verbose:
            print("-------------- configuration --------------")
            print(configuration)
        intf = configuration[(0, 0)]
        if verbose:
            print("-------------- intf --------------")
            print(intf)
        descriptor = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        if descriptor is None:
            raise IOError("Unable to match the USB 'OUT' endpoint.")
        if verbose:
            print("-------------- descriptor --------------")
            print(descriptor)

        ctrl_transfer = self.device.ctrl_transfer(0x40, 177, 0x0102, 0, 0, 2000)
        if verbose:
            print("---------- ctrl_transfer ------------")
            print(ctrl_transfer)


if __name__ == "__main__":
    k40 = NanoStream()
    k40.initialize_device(True)
    k40.check_status()
