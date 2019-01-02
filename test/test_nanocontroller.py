import os
import unittest

from k40nano import *


class TestNanoController(unittest.TestCase):

    def test_nano_controller(self):
        controller = NanoController(FileWriteConnection("test"))
        transaction = controller.start()
        transaction.move(1, 1)
        transaction.finish()
        with open("test.egv", "r+") as f:
            line = f.readline()
            self.assertEqual("IBaRaS1P", line)
        self.addCleanup(os.remove, "test.egv")
