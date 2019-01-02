#!/usr/bin/env python

from .NanoConstants import *

MODE_SLOW = 0b00000001  # Slow mode
MODE_SPEED_SET = 0b00000010  # Speed set
MODE_LASER_ON = 0b00000100  # Laser On
MODE_DIRECTION_LEFT = 0b00001000  # Going -X
MODE_DIRECTION_TOP = 0b00010000  # Going -Y
MODE_FINISHING = 0b00100000  # Finishing.
MODE_RESET = 0b01000000  # Reset
MODE_STARTED = 0b10000000


class EgvParser:
    def __init__(self):
        self.command = None
        self.distance = 0
        self.number_value = 0

    @staticmethod
    def skip(file, byte, count):
        pos = file.tell()
        while count > 0:
            char = file.read(1)
            if char == byte:
                count -= 1
            if char is None or len(char) == 0:
                file.seek(pos, 0)
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


def parse_egv(f, transaction):
    parser = EgvParser()
    if isinstance(f, str):
        with open(f, "rb") as f:
            parse_egv(f, transaction)
            return
    parser.skip_header(f)

    speed_code = ""
    raster_step = 0
    is_slow = False
    is_on = False
    is_left = False
    is_top = False
    for commands in parser.parse(f):
        cmd = commands[0]
        distance = commands[1] + commands[2]
        if cmd is None:
            return
        elif cmd == COMMAND_RIGHT:  # move right
            if is_left:
                transaction.move(distance, raster_step, is_on, is_slow)
            else:
                transaction.move(distance, 0, is_on, is_slow)
            is_left = False
        elif cmd == COMMAND_LEFT:  # move left
            if not is_left:
                transaction.move(-distance, raster_step, is_on, is_slow)
            else:
                transaction.move(-distance, 0, is_on, is_slow)
            is_left = True
        elif cmd == COMMAND_TOP:  # move top
            transaction.move(0, -distance, is_on, is_slow)
            is_top = True
        elif cmd == COMMAND_BOTTOM:  # move bottom
            transaction.move(0, distance, is_on, is_slow)
            is_top = False
        elif cmd == COMMAND_ANGLE:
            if is_left:
                distance_x = -distance
            else:
                distance_x = distance
            if is_top:
                distance_y = -distance
            else:
                distance_y = distance
            transaction.move(distance_x, distance_y, is_on, is_slow)
        elif cmd == COMMAND_ON:  # laser on
            is_on = True
        elif cmd == COMMAND_OFF:  # laser off
            is_on = False
        elif cmd == COMMAND_S:  # s command
            pass
        elif cmd == COMMAND_E:  # slow
            is_slow = True
        elif cmd == COMMAND_P:  # pop
            is_slow = False
        elif cmd == COMMAND_INTERRUPT:  # interrupt
            is_slow = False
            is_on = False
        elif cmd == COMMAND_FINISH:  # finish
            transaction.finish()
        elif cmd == COMMAND_CUT:  # cut
            raster_step = 0
            transaction.set_step(raster_step)
            if raster_step == 0:
                code = "CV%s" % str(speed_code)
            else:
                code = "V%sG%03d" % (str(speed_code), raster_step)
            transaction.set_speed(code)
        elif cmd == COMMAND_SPEED:  # velocity
            speed_code = str(commands[2])
            if raster_step == 0:
                code = "CV%s" % str(speed_code)
            else:
                code = "V%sG%03d" % (str(speed_code), raster_step)
            transaction.set_speed(code)
        elif cmd == COMMAND_STEP:  # engrave
            raster_step = commands[2]
            transaction.set_step(raster_step)
            if raster_step == 0:
                code = "CV%s" % str(speed_code)
            else:
                code = "V%sG%03d" % (str(speed_code), raster_step)
            transaction.set_speed(code)
        elif cmd == COMMAND_NEXT:  # next
            is_slow = False
        elif cmd == COMMAND_RESET:  # reset
            is_slow = False
