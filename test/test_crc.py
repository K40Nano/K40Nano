import unittest
import random

from k40nano.NanoConnection import onewire_crc_lookup


def crc_8bit_onewire(line):
    """
    The one wire CRC algorithm is derived from the OneWire.cpp Library
    The latest version of this library may be found at:
    http://www.pjrc.com/teensy/td_libs_OneWire.html
    """
    crc = 0
    for i in range(2, 32):
        in_byte = line[i]
        for j in range(8):
            mix = (crc ^ in_byte) & 0x01
            crc >>= 1
            if mix:
                crc ^= 0x8C
            in_byte >>= 1
    return crc


class TestNanoCrc(unittest.TestCase):

    def test_crc(self):
        """
        Test to prove the code change here is correct. New code is about 7 times faster.
        1,000,000 packets in 8 seconds rather than 60
        """
        for q in range(0,10000):
            line = [random.randint(0,255) for m in range(0,32)]
            self.assertEqual(onewire_crc_lookup(line), crc_8bit_onewire(line))
