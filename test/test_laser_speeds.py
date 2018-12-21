from __future__ import print_function

import unittest

from k40nano import *


class TestLaserSpeeds(unittest.TestCase):

    def test_generate_speed_M2(self):
        b = LaserM2()
        self.assertEqual(b.make_speed(.5), "CV0551401001108644C")

    def test_generate_speed_M1(self):
        b = LaserM1()
        self.assertEqual(b.make_speed(.5), "CV167750462391000000000")
