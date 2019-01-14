from __future__ import print_function

import unittest

from k40nano import *


class TestLaserSpeeds(unittest.TestCase):

    def test_generate_speedcode(self):
        with open("speedcode.txt", "r") as codes:
            line = codes.readline()
            # <SpeedCode> <Board> <mm_per_second> <step_amount>
            values = line.split(" ")
            speed_code = values[0]
            board = values[1]
            mm_per_second = float(values[2])
            step_amount = int(values[3])
            created_speedcode = LaserSpeed.make_speed_code(mm_per_second, step_amount, board)
            self.assertEqual(created_speedcode, speed_code)

    def test_decode_speedcode(self):
        with open("speedcode.txt", "r") as codes:
            while True:
                line = codes.readline()
                if line is None or len(line) == 0:
                    break
                # <SpeedCode> <Board> <mm_per_second> <step_amount>
                values = line.split(" ")
                if len(values) == 0:
                    break
                speed_code = values[0]
                board = values[1]
                mm_per_second = float(values[2])
                step_amount = int(values[3])
                b, m, gear = LaserSpeed.get_gearing(board, mm_per_second, float(step_amount) != 0)
                if m == 0:
                    continue  # Out of range speed codes cannot be decoded.
                parsed = LaserSpeed.parse_speed_code(speed_code)
                determined_speed = LaserSpeed.get_speed_from_value(parsed[0], b, m)

                print("%s %f ~= %f" % (board, mm_per_second, determined_speed))
                self.assertAlmostEqual(determined_speed,mm_per_second, delta=mm_per_second / 100)
