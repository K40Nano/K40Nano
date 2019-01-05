#!/usr/bin/env python

COMMAND_RIGHT = b'B'
COMMAND_LEFT = b'T'
COMMAND_TOP = b'L'
COMMAND_BOTTOM = b'R'

COMMAND_ANGLE = b'M'
COMMAND_ON = b'D'
COMMAND_OFF = b'U'
COMMAND_NEXT = b'N'
COMMAND_S = b'S'
COMMAND_P = b'P'
COMMAND_E = b'E'
COMMAND_INTERRUPT = b'I'
COMMAND_SPEED = b'V'
COMMAND_CUT = b'C'
COMMAND_FINISH = b'F'
COMMAND_STEP = b'G'
COMMAND_RESET = b'@'


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

    speed_code = ""
    value_g = 0
    is_compact = False
    is_on = False
    is_left = False
    is_top = False
    is_speed = False
    is_cut = False
    is_harmonic = False
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
        elif cmd == COMMAND_ANGLE:
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
        elif cmd == COMMAND_S:  # s command
            value_s = commands[2]  # needed to know which E we are performing.
        elif cmd == COMMAND_E:  # slow
            if value_s == 1:  # is S1E not SE
                try:  # compact_mode command is only for NanoPlotter.
                    plotter.enter_compact_mode(speed=speed_code, harmonic_step=value_g)
                except AttributeError:
                    pass
                is_compact = True
        elif cmd == COMMAND_P:  # pop
            is_compact = True
        elif cmd == COMMAND_INTERRUPT:  # interrupt
            pass
        elif cmd == COMMAND_FINISH:  # finish
            try:  # compact_mode command is only for NanoPlotter.
                    plotter.enter_compact_mode(speed=speed_code, harmonic_step=value_g)
            except AttributeError:
                    pass
            is_compact = True
        elif cmd == COMMAND_CUT:  # cut
            is_harmonic = False
            is_cut = True
            value_g = 0
            speed_code += str(COMMAND_CUT)
        elif cmd == COMMAND_SPEED:  # velocity
            is_speed = True
            speed_code += str(commands[2])
        elif cmd == COMMAND_STEP:  # engrave
            value_g = commands[2]
            speed_code += "G%03d" % value_g
        elif cmd == COMMAND_NEXT:  # next
            try:
                plotter.exit_compact_mode_break()
            except AttributeError:
                pass
            is_compact = False
        elif cmd == COMMAND_RESET:  # reset
            is_compact = False
            is_on = False
            is_left = False
            is_top = False
            is_speed = False
            is_cut = False
            is_harmonic = False
