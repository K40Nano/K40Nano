#!/usr/bin/env python

from math import floor


class LaserSpeed:
    """
    MIT License.

    This is the standard library for converting to and from speed code information for LHYMICRO-GL.

    The units in the speed code have particular bands/gears which slightly modifies the equations used
    to convert between values and speeds. The fundamental units within the speed code value are period-ticks.
    All values relate to a value in the counter to count off the number of oscillations within the
    (typically 21.1184) Mhz crystal. The max value here is 65535, potentially with the addition of a diagonal delay.

    The board is ultimately controlling a stepper motor and the speed a stepper motor travels is the result of
    the time between the ticks. Since the crystal oscillator is the same, the delay is controlled by the counted
    oscillations subticks, which gives us the time between stepper motor pulses. Most of the devices we are
    dealing with are 1000 dpi stepper motors, so, for example, to travel at 1 inch a second requires that the
    device tick at 1 kHz. To do this it must delay 1 ms between ticks. This corresponds to a value of 43136 in
    the M2 board. Which has an equation of 65536 - (5120 + 17280T) where T is the period requested in ms. This is
    equal to 25.4 mm/s. If we want a 2 ms delay, which is half the speed (0.5kHz, 0.5 inches/second, 12.7 mm/s)
    we do 65536 - (5120 + 34560) which gives us a value of 25856. This would be encoded as a 16 bit number
    broken up into 2 ascii 3 digit strings between 0-255. 101 for the high bits and 00 for the low bits.
    So CV01010001 where the final character "1" is the gearing equation we used.

    The speed in mm/s is also used for determining which gearing to use and as a factor for the horizontal
    encoded value, for some boards (B2, M2). Slowing down the device down while traveling diagonal to make the
    diagonal and orthogonal take the same amount of time (thereby cutting to the same depth). This is the same
    period-ticks units and is simply summed with the 65535 - (b + mT) value in cases that both stepper motors
    are used.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_speed_from_code(speed_code, board="BOARD-M2"):
        code_value, gear, step_value, diagonal, raster_step = LaserSpeed.parse_speed_code(speed_code)
        b, m, gear = LaserSpeed.get_gearing(board, gear=gear, uses_raster_step=raster_step != 0)
        return LaserSpeed.get_speed_from_value(code_value, b, m)

    @staticmethod
    def get_code_from_speed(mm_per_second, raster_step=0, board="BOARD-M2", d_ratio=0.261199033289, gear=None):
        """
        Get a speedcode from a given speed. The raster step appends the 'G' value and uses speed ranges.
        The d_ratio uses the default/auto ratio. The gearing is optional and forces the speedcode to work
        for that particular gearing. Gear=0 refers to C-suffix notation speeds.

        :param mm_per_second: speed to convert to code.
        :param raster_step: raster step mode to use.
        :param board: Nano Board Model to do the conversion for.
        :param d_ratio: M1, M2, B1, B2 have ratio of optional speed
        :param gear: Optional force gearing rather than default gear for that speed.
        :return: speed code produced.
        """
        if mm_per_second > 240 and raster_step == 0:
            mm_per_second = 19.05  # Arbitrary default speed for out range value.
        b, m, gear = LaserSpeed.get_gearing(board, mm_per_second, raster_step != 0, gear)

        speed_value = LaserSpeed.get_value_from_speed(mm_per_second, b, m)
        encoded_speed = LaserSpeed.encode_value(speed_value)

        if raster_step != 0:
            if gear == 0:  # There is no C suffix notation for gear raster step.
                gear = 1
            return "V%s%1dG%03d" % (
                encoded_speed,
                gear,
                raster_step
            )

        if d_ratio == 0 or board == "A" or board == "B" or board == "M" or board == "BOARD-A" or board =="BOARD-B" or board == "BOARD-M":
            # We do not need the diagonal code.
            if raster_step == 0:
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
            d_value = d_ratio * m * period_in_ms / float(step_value)
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
        is_shortened = False
        normal = False
        if speed_code[0] == "C":
            speed_code = speed_code[1:]
            normal = True
        if speed_code[-1] == "C":
            speed_code = speed_code[:-1]
            is_shortened = True
            # This is an error speed.
        if "V1677" in speed_code or "V1676" in speed_code:
            # The 4th character can only be 0,1,2 except for error speeds.
            code_value = LaserSpeed.decode_value(speed_code[1:12])
            speed_code = speed_code[12:]
            # The value for this speed is so low, it's negative
            # and bit-shifted in 24 bits of a negative number.
        else:
            code_value = LaserSpeed.decode_value(speed_code[1:7])
            speed_code = speed_code[7:]
        code_value = 65536 - code_value
        gear = int(speed_code[0])
        speed_code = speed_code[1:]

        if is_shortened:
            gear = 0  # Flags as step zero during code error.
        raster_step = 0

        if normal:
            step_value = 0
            diagonal = 0
            if len(speed_code) > 1:
                step_value = int(speed_code[:3])
                diagonal = LaserSpeed.decode_value(speed_code[3:])
            return code_value, gear, step_value, diagonal, raster_step
        else:
            if "G" in speed_code:
                raster_step = int(speed_code[-3:])
            return code_value, gear, 1, 1, raster_step

    @staticmethod
    def get_value_from_speed(mm_per_second, b, m):
        """
        Takes in speed in mm per second and returns speed value.
        """
        try:
            frequency_kHz = float(mm_per_second) / 25.4
            period_in_ms = 1.0 / frequency_kHz
            return 65536 - LaserSpeed.get_value_from_period(period_in_ms, b, m)
        except ZeroDivisionError:
            return 65536 - b

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
        if b1 > 0x7FFF:
            b1 = b1 - 0xFFFF
        b2 = int(code[-3:])
        return (b1 << 8) + b2

    @staticmethod
    def encode_value(value):
        value = int(value)
        b0 = value & 255
        b1 = (value >> 8) & 0xFFFFFF  # unsigned shift, to emulate bugged form.
        return "%03d%03d" % (b1, b0)

    @staticmethod
    def get_gear_for_speed(mm_per_second, uses_raster_step=False):
        if mm_per_second <= 25.4:
            return 1
        if 25.4 < mm_per_second <= 60:
            return 2
        if not uses_raster_step:
            if 60 < mm_per_second < 127:
                return 3
            if 127 <= mm_per_second:
                return 4
        else:
            if 60 < mm_per_second < 127:
                return 2
            if 127 <= mm_per_second <= 320:
                return 3
            if 320 <= mm_per_second:
                return 4

    @staticmethod
    def get_gearing(board, mm_per_second=None, uses_raster_step=False, gear=None):
        """The gearing equations are divided into two sets distinct groups.
        The BOARD-[ABM][12]? values and the [ABM][12]? values. If the 'BOARD'
        prefix is specified it will give the correct value to create a given speed.
        Without the prefix, it will give the values the chinese software produced.

        For the M2 board this was physically checked and found to be inaccurate.
        The physical device scaled properly with a different slope value that
        corresponded exactly a factor of 22118400 which is the hz of the crystal used.

        This value has been established for the M2 board. It's guessed at for the B2
        board being twice the M2 board. However it is not known for A or B, B1 or B2
        In this case BOARD-X returns the same value as X.
        """
        if gear is None:
            gear = LaserSpeed.get_gear_for_speed(mm_per_second, uses_raster_step)

        # A, B, B1, B2, BOARD-A, BOARD-B, BOARD-B1 BOARD-B2
        b_values = [2.0 * 8 * 7 * 7, 2.0 * 8 * 7 * 7, 2.0 * 8 * 8 * 7, 2.0 * 8 * 8 * 8]  # 784, 784, 896, 1024
        m = 2.0 * 1000.0
        if board == "BOARD-B2":
            m = 22118400.0 / 640.0  # 22.1184 mhz processor, 34560
        if board == "B2":
            m = 24240.0
        if board == "BOARD-M" or board == "BOARD-M1" or board == "BOARD-M2":  # any BOARD-M series board
            b_values = [2 * 10 * 256, 2 * 10 * 256, 2 * 11 * 256, 2 * 12 * 256]
            m = 22118400.0 / 1280.0  # 22.1184 mhz processor, 17280

        if board == "M" or board == "M1" or board == "M2":  # any M series board
            b_values = [2 * 10 * 256, 2 * 10 * 256, 2 * 11 * 256, 2 * 12 * 256]
            m = 12120.0

        if gear == 0:
            if board == "B2" or board == "BOARD-B2":
                if uses_raster_step:
                    return b_values[0], m / 12, 1
                else:
                    return b_values[0], m / 12, 0
            elif board == "M" or board == "M1" or board == "BOARD-M" or board == "BOARD-M1":
                return b_values[0], m, 0
            elif board == "M2" or board == "BOARD-M2":
                return 2.0 * 4, m / 12, 0
        elif mm_per_second is not None:
            if board == "B2" or board == "BOARD-B2":
                if mm_per_second < 7:
                    if uses_raster_step:
                        return b_values[0], m / 12, 1
                    else:
                        return b_values[0], m / 12, 0
            elif board == "M" or board == "BOARD-M":
                if mm_per_second < 6:
                    return b_values[0], m, 0
            elif board == "M1" or board == "BOARD-M1":
                if mm_per_second < 6 or (not uses_raster_step and mm_per_second < 7):
                    return b_values[0], m, 0
            elif board == "M2" or board == "BOARD-M2":
                if mm_per_second < 7:
                    return 2.0 * 4, m / 12, 0
        return b_values[gear - 1], m, gear

    @staticmethod
    def validate_speed(mm_per_second, board, uses_raster_step=False):
        """
        Validate a speed.
        :param mm_per_second: speed to validate
        :param board: Nano Board Model
        :param uses_raster_step: is this speed for a raster_step
        :return: validated speed.
        """
        if board == "A" or board == "B" or board == "B1" or board == "BOARD-A" or board == "BOARD-B" or board == "BOARD-B1":
            if mm_per_second < 0.785:
                return 0.785
        elif board == "BOARD-B2":
            if mm_per_second < 13.557 and (mm_per_second >= 7 or uses_raster_step):
                return 13.557
            if mm_per_second < 1.131:
                return 1.131
        elif board == "B2":
            if mm_per_second < 9.509 and (mm_per_second >= 7 or uses_raster_step):
                return 9.509
            if mm_per_second < 0.793:
                return 0.793
        elif board == "M" or board == "M1":
            if mm_per_second < 5.096:
                return 5.096
        elif board == "BOARD-M" or board == "BOARD-M1":
            if mm_per_second < 7.266:
                return 7.266
        elif board == "M2":
            if mm_per_second < 5.096 and uses_raster_step:
                return 5.096
            if mm_per_second < 0.392:
                return 0.392
        elif board == "BOARD-M2":
            if mm_per_second < 7.266 and (mm_per_second >= 7 or uses_raster_step):
                return 7.266
            if mm_per_second < 0.559:
                return 0.559
        if uses_raster_step:
            if mm_per_second > 500:
                return 500.0
        else:
            if mm_per_second > 240:
                return 240.0
        return mm_per_second
