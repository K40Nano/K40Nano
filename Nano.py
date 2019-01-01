#!/usr/bin/env python

from __future__ import print_function

import glob
import sys
import time

from k40nano import *

NANO_VERSION = "0.0.3"


class NanoCommand:
    def __init__(self):
        self.wait = 0
        self.cut = False
        self.abs = False
        self.pos = None
        self.filename = None
        self.command = None
        self.speed = None


class Nano:
    def __init__(self, arguments):
        self.controller = None
        self.log = print
        arguments.append("-e")  # always execute the stack.
        self.elements = list(reversed(arguments))
        if len(arguments) == 1:
            self.elements = ["-h"]
        self.command_lookup = {
            "-i": self.command_input,
            "-o": self.command_output,
            "-p": self.command_passes,
            "-m": self.command_move,
            "-M": self.command_move_abs,
            "-c": self.command_cut,
            "-C": self.command_cut_abs,
            "-s": self.command_speed,
            "-w": self.command_wait,
            "-e": self.command_execute,
            "-l": self.command_list,
            "-r": self.command_home,
            "-u": self.command_unlock,
            "-U": self.command_lock,
            "-q": self.command_quiet,
            "-v": self.command_verbose,
            "-h": self.command_help,
        }

    def command_help(self, values):
        print("Nano v.", NANO_VERSION)
        print("-i [<input>]*, loads egv/png files")
        print("-o [<egv/png/svg>]?, sets output method")
        print("-p [n], sets the number of passes")
        print("-m ([dx] [dy])+, relative move command")
        print("-M ([x] [y])+, absolute move command")
        print("-c ([dx] [dy])+, relative cut command")
        print("-C ([x] [y])+, absolute cut command")
        print("-s [+/-]?<speed> [step]*, sets the speed")
        print("-w [seconds], wait_time")
        print("-e, executes stack")
        print("-l, lists stack")
        print("-r, resets to home position")
        print("-u, unlock rail")
        print("-U, lock rail")
        print("-v, verbose mode (default)")
        print("-q, quiet mode")
        print("-h, display this message")
        print("")
        return values

    def get(self):
        return self.elements.pop()

    def v(self):
        if not self.elements:
            return None
        if self.elements[-1] not in self.command_lookup:
            return self.get()
        else:
            return None

    def execute(self):
        values = []
        while self.elements:
            command = self.get()
            if command not in self.command_lookup:
                continue
            values = self.command_lookup[command](values)
        self.control().release()

    def control(self):
        if self.controller is None:
            self.controller = NanoController()
        return self.controller

    def command_input(self, values):
        v = self.v()
        input_files = glob.glob(v)
        for input_file in input_files:
            m = NanoCommand()
            self.log("File:", input_file)
            m.filename = input_file
            values.append(m)
        return values

    @staticmethod
    def unit_convert(value):
        if value.endswith("in"):
            return int(round(1000 * float(value[:-2])))
        elif value.endswith("mm"):
            return int(round(39.3701 * float(value[:-2])))
        elif value.endswith("cm"):
            return int(round(393.701 * float(value[:-2])))
        elif value.endswith("ft"):
            return int(round(12000 * float(value[:-2])))
        return int(value)

    def command_move(self, values):
        m = NanoCommand()
        m.pos = []
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.pos.append([x, y])
            self.log("Move Relative:", x, y)
        m.cut = False
        m.abs = False
        values.append(m)
        return values

    def command_move_abs(self, values):
        m = NanoCommand()
        m.pos = []
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.pos.append([x, y])
            self.log("Move Absolute:", x, y)
        m.cut = False
        m.abs = True
        values.append(m)
        return values

    def command_cut(self, values):
        m = NanoCommand()
        m.pos = []
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.pos.append([x, y])
            self.log("Cut Relative:", x, y)
        m.cut = True
        m.abs = False
        values.append(m)
        return values

    def command_cut_abs(self, values):
        m = NanoCommand()
        m.pos = []
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.pos.append([x, y])
            self.log("Cut Absolute:", x, y)
        m.cut = True
        m.abs = True
        values.append(m)
        return values

    def command_speed(self, values):
        m = NanoCommand()
        speed = self.v()
        if speed.startswith("-"):
            m.abs = False
        elif speed.startswith("+"):
            m.abs = False
        else:
            m.abs = True
        m.speed = float(speed)
        self.log("Speed:", speed)
        values.append(m)
        return values

    def command_wait(self, values):
        m = NanoCommand()
        m.wait = float(self.v())
        values.append(m)
        self.log("Wait:", m.wait)
        return values

    def command_passes(self, values):
        self.log("Stack:", len(values))
        new_values = []
        count = int(self.v())
        for i in range(0, count):
            for value in values:
                new_values.append(value)
        self.log("Stack Count:", len(values), " -> ", len(new_values))
        return new_values

    def command_list(self, values):
        print("disabled briefly.")
        return values

    def command_execute(self, values):
        self.log("Executing:", len(values))
        for value in values:
            if value.pos is not None:
                for pos in value.pos:
                    if value.cut:
                        if value.abs:
                            self.control().move_abs(pos[0], pos[1], True, True)
                            self.control().wait()
                        else:
                            self.control().move(pos[0], pos[1], True, True)
                            self.control().wait()
                    else:
                        if value.abs:
                            self.control().move_now(pos[0], pos[1], True)
                        else:
                            self.control().move_now(pos[0], pos[1])
            if value.wait != 0:
                time.sleep(value.wait)
            if value.speed is not None:
                if value.abs:
                    self.control().set_speed(value.speed)
                else:
                    self.control().increase_speed(value.speed)
            if value.filename is not None:
                fname = str(value.filename).lower()
                if fname.endswith("egv"):
                    parse_egv(value.filename, self.control())
                elif fname.endswith("png"):
                    parse_png(value.filename, self.control())
            if value.command is not None:
                value.command()
        return []

    def command_home(self, values):
        self.log("Home Position")
        m = NanoCommand()
        m.command = self.home_function
        values.append(m)
        return values

    def home_function(self):
        self.control().home()

    def command_unlock(self, values):
        self.log("Unlock Rail")
        m = NanoCommand()
        m.command = self.unlock_function
        values.append(m)
        return values

    def unlock_function(self):
        self.control().rail(False)

    def command_lock(self, values):
        self.log("Lock Rail")
        m = NanoCommand()
        m.command = self.lock_function
        values.append(m)
        return values

    def lock_function(self):
        self.control().rail(True)

    def command_output(self, values):
        value = self.v()
        if value is None:
            self.controller = NanoController()
            self.log("NanoController")
        else:
            value = str(value).lower()
            if value.endswith("svg"):
                self.controller = SvgController(value)
                self.log("SvgController")
            elif value.endswith("png"):
                self.controller = PngController(value)
                self.log("PngController")
            elif value.endswith("egv"):
                self.controller = NanoController(FileWriteConnection(value))
                self.log("EgvNanoController")
            elif value == "print":
                self.controller = NanoController(PrintConnection())
                self.log("PrintNanoController")
        return values

    def command_quiet(self, values):
        self.log = self.no_operation
        return values

    def command_verbose(self, values):
        self.log = print
        return values

    def no_operation(self, *args):
        pass


argv = sys.argv
nano = Nano(argv)
nano.execute()
