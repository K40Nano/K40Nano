class LaserSpeed:

    def __init__(self):
        pass

    @staticmethod
    def get_value_from_speed(mm_per_second, shifts):
        """
        Takes in speed in mm per second and returns value.
        """
        try:
            freq = float(mm_per_second) / 25.4
            period = 1 / freq
            return LaserSpeed.get_value_from_period(period, shifts)
        except ZeroDivisionError:
            return shifts[0]

    @staticmethod
    def get_value_from_period(period, shifts):
        """
        Takes in period in kHz and converts it to value.
        """
        intercept = shifts[0]
        slope = shifts[1]
        x = period
        try:
            return slope * x + intercept
        except ZeroDivisionError:
            return float("inf")

    @staticmethod
    def get_speed_from_value(value, shifts):
        B = shifts[0]
        M = shifts[1]
        try:
            period = B - value / M
            return 25.4 / (1000.0 * period)
        except ZeroDivisionError:
            return M
        # max_value = shifts[0]
        # unit_position = shifts[0] - shifts[1]
        # try:
        #     return (max_value - unit_position) / (max_value - value)
        # except ZeroDivisionError:
        #     return float("inf")

    @staticmethod
    def decode_value(code):
        b1 = int(code[0:-3])
        if b1 > 16000000:
            b1 -= 16777216
        b2 = int(code[-3:])
        return (b1 << 8) + b2

    @staticmethod
    def encode_value(value):
        b0 = value & 255
        b1 = (value >> 8) & 0xFFFFFFFF  # unsigned shift, to emulate bugged form.
        return "%03d%03d" % (b1, b0)

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
        shift = int(speed_code[0])
        speed_code = speed_code[1:]
        if is_invalid_code:
            shift = 0  # Flags as step zero during code error.
        if normal:
            flow_max = 0
            diagonal = 0
            if len(speed_code) > 1:
                flow_max = int(speed_code[:3])
                diagonal = LaserSpeed.decode_value(speed_code[3:])
            return code_value, shift, flow_max, diagonal
        else:
            return code_value, shift, 1, 1
