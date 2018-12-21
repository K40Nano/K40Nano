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

from .NanoConnection import NanoConnection


class NanoStream:
    """
    I'm not really sure the pythonic ways to do this.
    """

    def __init__(self):
        self.connection = NanoConnection()
        self.connection.connect()
        self.closed = False

    def writable(self):
        return True

    def write(self, data):
        """
        Writes the data to the K40 device, encoding that data internally into packets, validates those packets
        and performs the resends as needed..

        :param data:
        :return:
        """
        self.connection.write_completed_packets(data)

    def flush(self):
        """
        Blocks while waiting for the K40 device to return TASK_COMPLETE to the check status.
        :return:
        """
        if self.closed:
            return
        self.connection.write_buffer()

    def close(self):
        """
        Close the stream.
        :return:
        """
        if self.closed:
            return
        self.connection.disconnect()


if __name__ == "__main__":
    stream = NanoStream()
    stream.write(b'IPP')
    stream.flush()
    # stream.close()
