#!/usr/bin/env python

COMMAND_RIGHT = b'B'
COMMAND_LEFT = b'T'
COMMAND_TOP = b'L'
COMMAND_BOTTOM = b'R'

COMMAND_ON = b'D'
COMMAND_OFF = b'U'
COMMAND_P = b'P'


class EgvParser:
    def __init__(self):
        self.command = None
        self.distance = 0
        self.number_value = 0

    @staticmethod
    def skip(read, byte, count):
        """Skips forward in the file until we find <count> instances of <byte>"""
        pos = read.tell()
        while count > 0:
            char = read.read(1)
            if char == byte:
                count -= 1
            if char is None or len(char) == 0:
                read.seek(pos, 0)
                # If we didn't skip the right stuff, reset the position.
                break

    def skip_header(self, file):
        self.skip(file, b'\n', 3)
        self.skip(file, b'%', 5)

    def parse(self, f):
        while True:
            byte = f.read(1)
            if byte is None or len(byte) == 0:
                break
            value = ord(byte)
            if ord('0') <= value <= ord('9'):
                self.append_digit(value - ord('0'))  # '0' = 0
                continue
            if ord('a') <= value <= ord('y'):
                self.append_distance(value - ord('a') + 1)  # 'a' = 1, not zero.
                continue
            if ord('A') <= value <= ord('Z') or value == ord('@'):
                if self.command is not None:
                    yield [self.command, self.distance, self.number_value]
                self.distance = 0
                self.number_value = 0
                self.command = byte
                continue
            if value == ord('z'):
                self.append_distance(255)
            if value == ord('|'):
                byte = f.read(1)
                if byte is None or len(byte) == 0:
                    break
                value = ord(byte)
                self.append_distance(25 + value - ord('a') + 1)  # '|a' = 27, not 26
        if self.command is not None:
            yield [self.command, self.distance, self.number_value]

    def append_digit(self, value):
        self.number_value *= 10
        self.number_value += value

    def append_distance(self, amount):
        self.distance += amount


def parse_egv(f, plotter):
    egv_parser = EgvParser()
    if isinstance(f, str):
        with open(f, "rb") as f:
            parse_egv(f, plotter)
            return
    egv_parser.skip_header(f)

    speed_code = None
    value_g = 0
    is_compact = False
    is_on = False
    is_left = False
    is_top = False
    is_speed = False
    is_cut = False
    is_harmonic = False
    is_finishing = False
    is_resetting = False
    value_s = -1

    for commands in egv_parser.parse(f):
        cmd = commands[0]
        distance = commands[1] + commands[2]
        if cmd is None:
            return
        elif cmd == COMMAND_RIGHT:  # move right
            if is_compact and is_harmonic and is_left:
                if is_top:
                    dy = -value_g
                else:
                    dy = value_g
                plotter.up()
                is_on = False
                plotter.move(distance, dy)
            else:
                plotter.move(distance, 0)
            is_left = False
        elif cmd == COMMAND_LEFT:  # move left
            if is_compact and is_harmonic and not is_left:
                if is_top:
                    dy = -value_g
                else:
                    dy = value_g
                plotter.up()
                is_on = False
                plotter.move(-distance, dy)
            else:
                plotter.move(-distance, 0)
            is_left = True
        elif cmd == COMMAND_BOTTOM:  # move bottom
            if is_compact and is_harmonic and is_top:
                if is_left:
                    dx = -value_g
                else:
                    dx = value_g
                plotter.up()
                is_on = False
                plotter.move(dx, distance)
            else:
                plotter.move(0, distance)
            is_top = False
        elif cmd == COMMAND_TOP:  # move top
            if is_compact and is_harmonic and not is_top:
                if is_left:
                    dx = -value_g
                else:
                    dx = value_g
                plotter.up()
                is_on = False
                plotter.move(dx, -distance)
            else:
                plotter.move(0, -distance)
            is_top = True
        elif cmd == b'M':
            if is_left:
                distance_x = -distance
            else:
                distance_x = distance
            if is_top:
                distance_y = -distance
            else:
                distance_y = distance
            plotter.move(distance_x, distance_y)
        elif cmd == COMMAND_ON:  # laser on
            is_on = True
            plotter.down()
        elif cmd == COMMAND_OFF:  # laser off
            is_on = False
            plotter.up()
        elif cmd == b'S':  # s command
            value_s = commands[2]  # needed to know which E we are performing.
        elif cmd == b'E':  # slow
            is_compact = True
            if is_finishing or is_resetting:
                is_resetting = False
                is_compact = False
                is_on = False
                is_left = False
                is_top = False
                is_speed = False
                speed_code = None
                is_cut = False
                is_harmonic = False
            if is_finishing:
                is_finishing = False
                break
            try:  # compact_mode command is only for NanoPlotter.
                plotter.enter_compact_mode(speed=speed_code, harmonic_step=value_g)
            except AttributeError:
                pass
        elif cmd == b'F':  # finish
            is_compact = True
            try:  # compact_mode command is only for NanoPlotter.
                plotter.enter_compact_mode(speed=speed_code, harmonic_step=value_g)
            except AttributeError:
                pass
        elif cmd == b'P':  # pop
            is_compact = False
        elif cmd == b'I':  # interrupt
            pass
        elif cmd == b'C':  # cut
            is_harmonic = False
            is_cut = True
            value_g = 0
            if speed_code is None:
                speed_code = ""
            speed_code += 'C'
        elif cmd == b'V':  # velocity
            is_speed = True
            if speed_code is None:
                speed_code = ""
            speed_code += 'V%d' % commands[2]
        elif cmd == b'G':  # engrave
            is_harmonic = True
            value_g = commands[2]
            if speed_code is None:
                speed_code = ""
            speed_code += "G%03d" % value_g
        elif cmd == b'N':  # next
            is_compact = False
            try:
                plotter.exit_compact_mode_break()
            except AttributeError:
                pass
        elif cmd == b'@':  # reset
            is_resetting = True
