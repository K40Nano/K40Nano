#!/usr/bin/env python

from __future__ import print_function

from .Connection import Connection


class PrintConnection(Connection):

    def __init__(self):
        Connection.__init__(self)

    def write(self, data=None):
        print(data)
