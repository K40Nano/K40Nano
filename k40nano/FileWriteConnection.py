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
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        self.writer.write(data)

    def flush(self):
        self.writer.write('\n')
