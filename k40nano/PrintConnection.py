#!/usr/bin/env python

from __future__ import print_function

from .Connection import Connection


class PrintConnection(Connection):

    def __init__(self):
        Connection.__init__(self)

    def write(self, data=None):
        """
        Buffers data, sending any complete packets.
        :param data:
        :return:
        """
        print(data)
