#!/usr/bin/env python

from math import floor, ceil


class LaserSpeed:
    """
    MIT License.

    This is the standard library for converting to and from speed code information for LHYMICRO-GL.

    The units in the speed code have particular bands/gears which switches the equations used to convert
    between values and speeds. The fundamental units within the speed code value is period. All values
    are linearly related to the delay between ticks. The device controlled is ultimately a stepper motor
    and the speed a stepper motor travels at is the result of the time between ticks. We are dealing with
    a 1000 dpi stepper motor, so for example to travel at 1 inch a second requires that the device tick
    at 1 kHz. To do this it must delay 1 ms between ticks. This corresponds to a value of 48296 in the M2
    board. Which has an equation of 60416 - (12120 * T) where T is the period requested in ms. This is
    equal to 25.4 mm/s. If we want a 2 ms delay, which is half the speed (0.5kHz, 0.5 inches/second,
    12.7 mm/s) we do 60416 - (12120 * 2) which gives us a value of 36176. This would be encoded a 16 bit
    number broken up into 2 ascii 3 digit strings between 0-255.  141 for the high bits and 80 for the low
    bits. So CV1410801 where the final 1 is the gearing equation we used.

    The speed in mm/s is also used for determining which gearing to use and as a factor for the horizontal
    encoded value. Slow down the device down while traveling diagonal to make the diagonal and orthogonal
    take the same amount of time (thereby cutting to the same depth).
    """

    def __init__(self):
        pass

    @staticmethod
    def make_speed_code(mm_per_second, harmonic_step=0, board="M2", d_ratio=0.261199033289):
        if mm_per_second > 240 and harmonic_step == 0:
            mm_per_second = 19.05
        # if (board == "M2" or board == "M1") and mm_per_second > 240 and not harmonic_step:
        #     mm_per_second = 19.05  # emulate fully.
        # if board == "B2" and mm_per_second > 240 and not harmonic_step:
        #     #mm_per_second = 19.1925187032 # emulate fully
        #     mm_per_second = 19.05
        b, m, gear = LaserSpeed.get_gearing(board, mm_per_second, harmonic_step != 0)

        speed_value = LaserSpeed.get_value_from_speed(mm_per_second, b, m)
        if (speed_value - round(speed_value)) > 0.005:
            speed_value = ceil(speed_value)
        encoded_speed = LaserSpeed.encode_value(speed_value)

        if harmonic_step != 0:
            if gear == 0:  # Nothing flags invalid speeds with steps turned on.
                gear = 1
            return "V%s%1dG%03d" % (
                encoded_speed,
                gear,
                harmonic_step
            )

        if d_ratio == 0 or board == "A" or board == "B" or board == "M":
            # We do not need the diagonal code.
            if harmonic_step == 0:
                if gear == 0:
                    return "CV%s1C" % (
                        encoded_speed
                    )
                else:
                    return "CV%s%1d" % (
                        encoded_speed,
                        gear)
        else:
            step_value = min(int(floor(mm_per_second) + 1), 128)
            frequency_kHz = float(mm_per_second) / 25.4
            try:
                period_in_ms = 1 / frequency_kHz
            except ZeroDivisionError:
                period_in_ms = 0
            d_value = d_ratio * -m * period_in_ms / float(step_value)
            encoded_diagonal = LaserSpeed.encode_value(d_value)
            if gear == 0:
                return "CV%s1%03d%sC" % (
                    encoded_speed,
                    step_value,
                    encoded_diagonal
                )
            else:
                return "CV%s%1d%03d%s" % (
                    encoded_speed,
                    gear,
                    step_value,
                    encoded_diagonal)

    @staticmethod
    def parse_speed_code(speed_code):
        is_invalid_code = False
        normal = False
        if speed_code[0] == "C":
            speed_code = speed_code[1:]
            normal = True
        if speed_code[-1] == "C":
            speed_code = speed_code[:-1]
            is_invalid_code = True
            # This is an error speed.
        if "V1677" in speed_code or "V1676" in speed_code:
            # The 4th character can only be 0,1,2 except for error speeds.
            code_value = LaserSpeed.decode_value(speed_code[1:12])
            speed_code = speed_code[12:]
            is_invalid_code = True
            # This is an error speed.
            # The value for this speed is so low, it turned negative
            # and bit-shifted in 24 bits of a negative number.
        else:
            code_value = LaserSpeed.decode_value(speed_code[1:7])
            speed_code = speed_code[7:]
        gear = int(speed_code[0])
        speed_code = speed_code[1:]
        if is_invalid_code:
            gear = 0  # Flags as step zero during code error.
        if normal:
            step_value = 0
            diagonal = 0
            if len(speed_code) > 1:
                step_value = int(speed_code[:3])
                diagonal = LaserSpeed.decode_value(speed_code[3:])
            return code_value, gear, step_value, diagonal
        else:
            return code_value, gear, 1, 1

    @staticmethod
    def get_value_from_speed(mm_per_second, b, m):
        """
        Takes in speed in mm per second and returns speed value.
        """

        try:
            frequency_kHz = float(mm_per_second) / 25.4
            period_in_ms = 1 / frequency_kHz
            return LaserSpeed.get_value_from_period(period_in_ms, b, m)
        except ZeroDivisionError:
            return b

    @staticmethod
    def get_value_from_period(x, b, m):
        """
        Takes in period in ms and converts it to value.
        This is a simple linear relationship.
        """
        return m * x + b

    @staticmethod
    def get_speed_from_value(value, b, m):
        try:
            period_in_ms = LaserSpeed.get_period_from_value(value, b, m)
            frequency_kHz = 1 / period_in_ms
            return 25.4 * frequency_kHz
        except ZeroDivisionError:
            return 0

    @staticmethod
    def get_period_from_value(y, b, m):
        try:
            return (y - b) / m
        except ZeroDivisionError:
            return float('inf')

    @staticmethod
    def decode_value(code):
        b1 = int(code[0:-3])
        if b1 > 16000000:
            b1 -= 16777216  # decode error negative numbers
        b2 = int(code[-3:])
        return (b1 << 8) + b2

    @staticmethod
    def encode_value(value):
        value = int(value)
        b0 = value & 255
        b1 = (value >> 8) & 0xFFFFFF  # unsigned shift, to emulate bugged form.
        return "%03d%03d" % (b1, b0)

    @staticmethod
    def get_gearing(board, mm_per_second, harmonic=False):
        if board == "A" or board == "B" or board == "B1":
            if not harmonic:
                if 0 <= mm_per_second <= 25.4:
                    return 64752.0, -2000.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 64752.0, -2000.0, 2
                if 60 < mm_per_second < 127:
                    return 64640.0, -2000.0, 3
                if 127 <= mm_per_second:
                    return 64512.0, -2000.0, 4
            else:
                if 0 <= mm_per_second <= 25.4:
                    return 64752.0, -2000.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 64752.0, -2000.0, 2
                if 60 < mm_per_second < 127:
                    return 64752.0, -2000.0, 2
                if 127 <= mm_per_second <= 240:
                    return 64640.0, -2000.0, 3
                if 240 < mm_per_second <= 320:
                    return 64640.0, -2000.0, 3
                if 321 <= mm_per_second:
                    return 64512.0, -2000.0, 4
        if board == "B2":
            if not harmonic:
                if 0 <= mm_per_second < 7:
                    return 64752.0, -2020.0, 0  # -2020 is -24240 / 12
                if 7 <= mm_per_second <= 25.4:
                    return 64752.0, -24240.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 64752.0, -24240.0, 2
                if 60 < mm_per_second < 127:
                    return 64640.0, -24240.0, 3
                if 127 <= mm_per_second:
                    return 64512.0, -24240.0, 4
            else:
                if 0 <= mm_per_second < 7:
                    return 64752.0, -2020.0, 1
                if 7 <= mm_per_second <= 25.4:
                    return 64752.0, -24240.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 64752.0, -24240.0, 2
                if 60 < mm_per_second < 127:
                    return 64752.0, -24240.0, 2
                if 127 <= mm_per_second <= 240:
                    return 64640.0, -24240.0, 3
                if 240 <= mm_per_second < 321:
                    return 64640.0, -24240.0, 3
                if 321 <= mm_per_second:
                    return 64512.0, -24240.0, 4
        if board == "M":
            if not harmonic:
                if 0 <= mm_per_second < 6:
                    return 60416.0, -12120.0, 0
                if 6 <= mm_per_second <= 25.4:
                    return 60416.0, -12120.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 60416.0, -12120.0, 2
                if 60 < mm_per_second < 127:
                    return 59904.0, -12120.0, 3
                if 127 <= mm_per_second:
                    return 59392.0, -12120.0, 4
            else:
                if 0 <= mm_per_second < 6:
                    return 60416.0, -12120.0, 0
                if 6 <= mm_per_second <= 25.4:
                    return 60416.0, -12120.0, 1
                if 25.4 < mm_per_second < 127:
                    return 60416.0, -12120.0, 2
                if 127 <= mm_per_second <= 320:
                    return 59904.0, -12120.0, 3
                if 320 < mm_per_second:
                    return 59392.0, -12120.0, 4
        if board == "M1":
            if not harmonic:
                if 0 <= mm_per_second < 7:
                    return 60416.0, -12120.0, 0
                if 7 <= mm_per_second <= 25.4:
                    return 60416.0, -12120.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 60416.0, -12120.0, 2
                if 60 < mm_per_second < 127:
                    return 59904.0, -12120.0, 3
                if 127 <= mm_per_second:
                    return 59392.0, -12120.0, 4
            else:
                if 0 <= mm_per_second < 6:
                    return 60416.0, -12120.0, 0
                if 6 <= mm_per_second <= 25.4:
                    return 60416.0, -12120.0, 1
                if 25.4 < mm_per_second < 127:
                    return 60416.0, -12120.0, 2
                if 127 <= mm_per_second <= 320:
                    return 59904.0, -12120.0, 3
                if 320 < mm_per_second:
                    return 59392.0, -12120.0, 4
        if board == "M2":
            if not harmonic:
                if 0 <= mm_per_second < 7:
                    return 65528.0, -1010.0, 0  # -1010 is -12120 / 12
                if 7 <= mm_per_second <= 25.4:
                    return 60416.0, -12120.0, 1
                if 25.4 < mm_per_second <= 60:
                    return 60416.0, -12120.0, 2
                if 60 < mm_per_second < 127:
                    return 59904.0, -12120.0, 3
                if 127 <= mm_per_second:
                    return 59392.0, -12120.0, 4
            else:
                if 0 <= mm_per_second < 7:
                    return 65528.0, -1010.0, 0
                if 7 <= mm_per_second <= 25.4:
                    return 60416.0, -12120.0, 1
                if 25.4 < mm_per_second < 127:
                    return 60416.0, -12120.0, 2
                if 127 <= mm_per_second <= 320:
                    return 59904.0, -12120.0, 3
                if 320 < mm_per_second:
                    return 59392.0, -12120.0, 4
