#!/usr/bin/env python

from .NanoConstants import *


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


class EgvInterpreter:
    def __init__(self, controller):
        self.controller = controller
        self.distance_x = 0
        self.distance_y = 0
        self.mode = 0

    def commit_moves(self):
        d_laser = self.mode & MODE_LASER_ON
        d_slow = self.mode & MODE_SLOW
        if self.mode & MODE_DIRECTION_LEFT:
            dx = -self.distance_x
        else:
            dx = self.distance_x
        if self.mode & MODE_DIRECTION_TOP:
            dy = -self.distance_y
        else:
            dy = self.distance_y
        if dx != 0 or dy != 0:
            self.controller.move(dx, dy, d_slow, d_laser)
        self.distance_x = 0
        self.distance_y = 0

    def get_slow(self):
        return self.mode & MODE_SLOW

    def get_laser(self):
        return self.mode & MODE_LASER_ON

    def set_mode(self, mask, set_value):
        if set_value:
            self.mode |= mask
        else:
            self.mode &= ~mask


def parse_egv(f, controller):
    parser = EgvParser()
    if isinstance(f, str):
        with open(f, "rb") as f:
            parse_egv(f, controller)
            return
    parser.skip_header(f)
    egv = EgvInterpreter(controller)

    for commands in parser.parse(f):
        cmd = commands[0]
        if cmd is None:
            return
        elif cmd == COMMAND_RIGHT:  # move right
            slow = egv.get_slow()
            laser = egv.get_laser()
            egv.distance_x += commands[1] + commands[2]
            egv.set_mode(MODE_DIRECTION_LEFT, False)
            if slow or laser:
                egv.commit_moves()
        elif cmd == COMMAND_LEFT:  # move left
            slow = egv.get_slow()
            laser = egv.get_laser()
            egv.distance_x += commands[1] + commands[2]
            egv.set_mode(MODE_DIRECTION_LEFT, True)
            if slow or laser:
                egv.commit_moves()
        elif cmd == COMMAND_TOP:  # move top
            slow = egv.get_slow()
            laser = egv.get_laser()
            egv.distance_y += commands[1] + commands[2]
            egv.set_mode(MODE_DIRECTION_TOP, True)
            if slow or laser:
                egv.commit_moves()
        elif cmd == COMMAND_BOTTOM:  # move bottom
            slow = egv.get_slow()
            laser = egv.get_laser()
            egv.distance_y += commands[1] + commands[2]
            egv.set_mode(MODE_DIRECTION_TOP, False)
            if slow or laser:
                egv.commit_moves()
        elif cmd == COMMAND_ANGLE:
            slow = egv.get_slow()
            laser = egv.get_laser()
            distance = commands[1] + commands[2]
            egv.distance_y += distance
            egv.distance_x += distance
            if slow or laser:
                egv.commit_moves()
        elif cmd == COMMAND_ON:  # laser on
            egv.set_mode(MODE_LASER_ON, True)
        elif cmd == COMMAND_OFF:  # laser off
            egv.set_mode(MODE_LASER_ON, False)
        elif cmd == COMMAND_S:  # s command
            pass
        elif cmd == COMMAND_E:  # slow
            egv.commit_moves()
            egv.set_mode(MODE_SLOW, True)
        elif cmd == COMMAND_P:  # pop
            egv.set_mode(MODE_SLOW, False)
            egv.commit_moves()
        elif cmd == COMMAND_INTERRUPT:  # interrupt
            controller.halt()
        elif cmd == COMMAND_FINISH:  # finish
            egv.commit_moves()
            controller.wait()
        elif cmd == COMMAND_CUT:  # cut
            controller.set_speed(None, 0)
        elif cmd == COMMAND_SPEED:  # velocity
            controller.set_speed(commands[2])
        elif cmd == COMMAND_STEP:  # engrave
            controller.set_speed(None, commands[2])
        elif cmd == COMMAND_NEXT:  # next
            egv.commit_moves()
            egv.set_mode(MODE_SLOW, False)
            egv.set_mode(MODE_LASER_ON, False)
        elif cmd == COMMAND_RESET:  # reset
            egv.commit_moves()
            egv.set_mode(MODE_SLOW, False)
