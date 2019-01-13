#!/usr/bin/env python

from LaserSpeed import LaserSpeed


class LaserB2:
    """
    Values at 9 and below are errored.
    Values at below 6 are tagged with C
    Values below 9 are negative values.

    Has diagonal speedcode.
    """

    def __init__(self):
        self.board_name = "LASER-B2"

    # None Checked.
    @staticmethod
    def get_shift(mm_per_second):
        if 0 <= mm_per_second < 7:
            # return 64752.0, 51308, 0  # 2020
            return 64752.0, 2 * -1010, 0  # 2020
        if 7 <= mm_per_second <= 25.4:
            # return 64752.0, 615699, 1
            return 64752.0, 24 * -1010, 1  # 2020
        if 25.4 < mm_per_second <= 60:
            # return 64752.0, 615699, 2  # 24240
            return 64752.0, 24 * -1010, 2  # 2020
        if 60 < mm_per_second < 127:
            # return 64640.0, 615707, 3
            return 64640.0, 24 * -1010, 3  # 2020
        if 127 <= mm_per_second <= 240:
            # return 64512, 615552, 4  # 24234.33
            return 64512, 24 * -1010, 4
        else:
            return 32432.0, 0, 1

    @staticmethod
    def get_shift_harmonic(mm_per_second):
        if 0 <= mm_per_second < 7:
            return 64752.0, 2 * -1010, 1  # 2020
        if 7 <= mm_per_second <= 25.4:
            # return 64752.0, 50800, 1 #2000
            return 64752, -24240, 1
        if 25.4 < mm_per_second <= 60:
            # return 64752.0, 50800, 2
            return 64752, -24240, 2
        if 60 < mm_per_second < 127:
            # return 64640, 50800, 3
            return 64752, -24240, 2
            # return 64640, -2000, 3
        if 127 <= mm_per_second <= 240:
            return 64640, -24240, 3
        if 240 <= mm_per_second < 321:
            return 64640, -24240, 3
        if 321 <= mm_per_second <= 500:
            # return 59392.0, -248491.0, 4  # should be 307883
            return 64512, -24240, 4
        else:
            return 62086.0, 0, 1

    def make_speed_code(self, mm_per_second, harmonic_step=0, percent=0):
        if harmonic_step != 0:
            shifts = self.get_shift_harmonic(mm_per_second)
        else:
            shifts = self.get_shift(mm_per_second)
        value = LaserSpeed.get_value_from_speed(mm_per_second, shifts)
        encoded_speed_value = LaserSpeed.encode_value(value)
        shift = shifts[3]
        if shift == 0:
            # This is an error code, and we might be better off not sending it.
            return "CV%s1" % encoded_speed_value
        return "CV%s%1d" % (encoded_speed_value, shift)
