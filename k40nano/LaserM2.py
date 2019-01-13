#!/usr/bin/env python

from LaserSpeed import LaserSpeed


class LaserM2:
    """
    M2 laser boards require the horizontal codes.

    Codes below 0.391497 mm/s are negative. 1677..
    """

    def __init__(self):
        self.board_name = "LASER-M2"

    @staticmethod
    def get_shift(mm_per_second):
        if 0 <= mm_per_second < 7:
            # return 65528.0, 25654, 0  # 101
            return 65528.0, -1010, 0  # -8
        if 7 <= mm_per_second <= 25.4:
            # return 60417.0, 307860, 1  # 1212 = 101 * 12 # -5120
            return 60416.0, 12 * -1010, 1
        if 25.4 < mm_per_second <= 60:
            # return 60416.0, 307858, 2
            return 60416.0, 12 * -1010, 2
        if 60 < mm_per_second < 127:
            # return 59905.0, 307892, 3
            return 59904.0, 12 * -1010, 3
        if 127 <= mm_per_second <= 240:
            # return 59392.0, 307883, 4
            return 59392.0, 12 * -1010, 4
        else:
            return 44256, 0, 1  # -21280

    @staticmethod
    def get_shift_harmonic(mm_per_second):
        if 0 <= mm_per_second < 7:
            return 65528.0, -1010, 0  # These values are not permitted.
        if 7 <= mm_per_second <= 25.4:
            # return 60416.0, -247442.0, 1  # should be 307858
            return 60416.0, 12 * -1010, 1
        if 25.4 < mm_per_second < 127:
            # return 60416.0, -247442.0, 2  # should be 307858
            return 60416.0, 12 * -1010, 2
        if 127 <= mm_per_second <= 320:  # Check end point of this shift.
            # return 59905.0, -247987, 3  # should be 307892
            return 59904.0, 12 * -1010, 3
        if 320 < mm_per_second <= 500:
            # return 59392.0, -248491.0, 4  # should be 307883
            return 59392.0, 12 * -1010, 4
        else:
            return 59392.0, -248491.0, 4

    def make_speed_code(self, mm_per_second, harmonic_step=0, percent=0):
        if harmonic_step != 0:
            shifts = self.get_shift_harmonic(mm_per_second)
        else:
            shifts = self.get_shift(mm_per_second)
        value = LaserSpeed.get_value_from_speed(mm_per_second, shifts)
        encoded_speed = LaserSpeed.encode_value(value)
        encoded_horizontal = LaserSpeed.encode_value(0)
        # CURRENTLY UNSOLVED TODO: SOLVE
        shift = shifts[3]
        if shift == 0:
            # This is an error code, and we might be better off not sending it.
            return "CV%s1%03d%sC" % (
                encoded_speed,
                int(mm_per_second + 1),
                encoded_horizontal
            )
        return "CV%s%1d%03d%s" % (
            encoded_speed,
            shift,
            int(mm_per_second + 1),
            encoded_horizontal)
