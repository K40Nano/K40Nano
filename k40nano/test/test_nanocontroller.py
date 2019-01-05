import os
import unittest

from k40nano import *


class TestNanoController(unittest.TestCase):

    def test_nano_controller(self):
        filename = "test.egv"
        plotter = NanoPlotter()
        plotter.open(connect=FileWriteConnection(filename))
        plotter.move(1, 1)
        plotter.close()
        with open("test.egv", "r+") as f:
            line = f.readline()
            self.assertEqual("IBaRaS1P\n", line)
        self.addCleanup(os.remove, filename)
