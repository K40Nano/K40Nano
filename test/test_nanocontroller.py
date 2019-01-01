import os
import unittest

from k40nano import *


class TestNanoController(unittest.TestCase):

    def test_nano_controller(self):
        controller = NanoController(FileWriteConnection("test"))
        controller.move(1, 1)
        controller.release()
        with open("test.egv", "r+") as f:
            line = f.readline()
            self.assertEqual("BaRa", line)
        self.addCleanup(os.remove, "test.egv")
