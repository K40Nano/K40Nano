#!/usr/bin/env python

from .Connection import Connection


class FileWriteConnection(Connection):

    def __init__(self, write_object):
        Connection.__init__(self)
        self.writer = write_object

    def open(self):
        if isinstance(self.writer, str):
            self.writer = open(self.writer, "w+")

    def close(self):
        self.writer.flush()
        self.writer.close()

    def write(self, data=None):
        """
        Buffers data, sending any complete packets.
        :param data:
        :return:
        """
        self.writer.write(data.decode("utf-8"))
