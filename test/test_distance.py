import random
import unittest

from k40nano.NanoPlotter import nano_distance


def encode_distance(distance_mils):
    if abs(distance_mils - round(distance_mils, 0)) > 0.000001:
        raise Exception('Distance values should be integer value (inches*1000)')
    distance_mils = int(distance_mils)
    code = b''
    value_z = 255

    while distance_mils >= 255:
        code += b'z'
        distance_mils -= value_z
    if distance_mils == 0:
        return code
    elif distance_mils < 26:  # codes  "a" through  "y"
        character = chr(96 + distance_mils)
        return code + bytes(bytearray(character, 'utf8'))
    elif distance_mils < 52:  # codes "|a" through "|z"
        character = chr(96 + distance_mils - 25)
        return code + b'|' + bytes(bytearray(character, 'utf8'))
    elif distance_mils < 255:
        code += bytes(bytearray("%03d" % distance_mils, 'utf8'))
        return code
    else:
        raise Exception("Could not create distance")  # This really shouldn't happen.


class TestNanoDistance(unittest.TestCase):

    def test_distance(self):
        for q in range(0, 10000):
            d0 = encode_distance(q)
            d1 = nano_distance(q)
            self.assertEqual(d0, d1)
