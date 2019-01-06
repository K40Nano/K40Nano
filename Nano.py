#!/usr/bin/env python

from __future__ import print_function

import glob
import sys
import time

from k40nano import *

NANO_VERSION = "0.0.5"


class NanoCommand:
    def __init__(self):
        self.title = None
        self.wait = 0
        self.use_laser = False
        self.absolute = False
        self.positions = None
        self.input_file = None
        self.command = None
        self.speed = None


class Nano:
    def __init__(self, arguments):
        self.plotter = None
        self.log = print
        self.speed = None
        if arguments is None:
            arguments = []
        arguments.append("-e")  # always execute the stack.
        self.elements = list(reversed(arguments))
        if len(arguments) == 2:
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
        if self.plotter is not None:
            self.plotter.close()

    def command_input(self, values):
        v = self.v()
        input_files = glob.glob(v)
        for input_file in input_files:
            m = NanoCommand()
            m.title = "File:" + input_file
            self.log(m.title)
            m.input_file = input_file
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
        m.positions = []
        m.title = "Move Relative: "
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.positions.append([x, y])
            m.title += "(%i,%i) " % (x, y)
        self.log(m.title)
        m.use_laser = False
        m.absolute = False
        values.append(m)
        return values

    def command_move_abs(self, values):
        m = NanoCommand()
        m.positions = []
        m.title = "Move Absolute: "
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.positions.append([x, y])
            m.title += "(%i,%i) " % (x, y)
        self.log(m.title)
        m.use_laser = False
        m.absolute = True
        values.append(m)
        return values

    def command_cut(self, values):
        m = NanoCommand()
        m.positions = []
        m.title = "Cut Relative: "
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.positions.append([x, y])
            m.title += "(%i,%i) " % (x, y)
        self.log(m.title)
        m.use_laser = True
        m.absolute = False
        values.append(m)
        return values

    def command_cut_abs(self, values):
        m = NanoCommand()
        m.positions = []
        m.title = "Cut Absolute: "
        while True:
            x = self.v()
            if x is None:
                break
            y = self.v()
            if y is None:
                break
            x = self.unit_convert(x)
            y = self.unit_convert(y)
            m.positions.append([x, y])
            m.title += "(%i,%i) " % (x, y)
        self.log(m.title)
        m.use_laser = True
        m.absolute = True
        values.append(m)
        return values

    def command_speed(self, values):
        m = NanoCommand()
        speed = self.v()
        if speed.startswith("-"):
            m.absolute = False
            m.title = "Change Speed by: -%f" % float(speed)
        elif speed.startswith("+"):
            m.absolute = False
            m.title = "Change Speed by: +%f" % float(speed)
        else:
            m.absolute = True
            m.title = "Speed: %f" % float(speed)
        m.speed = float(speed)
        self.log(m.title)
        values.append(m)
        return values

    def command_wait(self, values):
        m = NanoCommand()
        m.wait = float(self.v())
        values.append(m)
        m.title = "Pause for: %f seconds" % m.wait
        self.log(m.title)
        values.append(m)
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
        for value in values:
            if value.title is not None:
                print(value.title)
        return values

    def get_plotter(self):
        if self.plotter is None:
            self.plotter = NanoPlotter()
            self.plotter.open()
        return self.plotter

    def command_execute(self, values):
        self.log("Executing:", len(values))
        for value in values:
            if value.positions is not None:
                plotter = self.get_plotter()
                if self.speed is not None:
                    try:
                        plotter.enter_compact_mode(value.speed)
                    except AttributeError:
                        pass
                if value.use_laser:
                    plotter.down()
                for pos in value.positions:
                    if value.absolute:
                        self.plotter.move_abs(pos[0], pos[1])
                    else:
                        self.plotter.move(pos[0], pos[1])
                if value.use_laser:
                    plotter.up()
            if value.wait != 0:
                time.sleep(value.wait)
            if value.speed is not None:
                plotter = self.get_plotter()
                if value.absolute:
                    new_speed = value.speed
                else:
                    new_speed = self.speed + value.speed
                if new_speed != value.speed:
                    try:
                        plotter.exit_compact_mode_reset()
                    except AttributeError:
                        pass
                self.speed = new_speed
            if value.input_file is not None:
                fname = str(value.input_file).lower()
                if fname.endswith("egv"):
                    plotter = self.get_plotter()
                    parse_egv(value.input_file, plotter)
                elif fname.endswith("png"):
                    plotter = self.get_plotter()
                    parse_png(value.input_file, plotter)
            if value.command is not None:
                value.command()
        return []

    def command_home(self, values):
        m = NanoCommand()
        m.title = "Home Position"
        self.log(m.title)
        m.command = self.home_function
        values.append(m)
        return values

    def command_unlock(self, values):
        m = NanoCommand()
        m.title = "Unlock Rail"
        self.log(m.title)
        m.command = self.unlock_function
        values.append(m)
        return values

    def command_lock(self, values):
        m = NanoCommand()
        m.title = "Lock Rail"
        self.log(m.title)
        m.command = self.lock_function
        values.append(m)
        return values

    def home_function(self):
        try:
            plotter = self.get_plotter()
            plotter.home()
        except AttributeError:
            pass

    def unlock_function(self):
        try:
            plotter = self.get_plotter()
            plotter.unlock_rail()
        except AttributeError:
            pass

    def lock_function(self):
        try:
            plotter = self.get_plotter()
            plotter.lock_rail()
        except AttributeError:
            pass

    def command_output(self, values):
        value = self.v()
        if value is None:
            self.plotter = NanoPlotter()
            self.log("NanoController")
        else:
            value = str(value).lower()
            if value.endswith("svg"):
                self.plotter = SvgPlotter(value)
                self.plotter.open()
                self.log("SvgController")
            elif value.endswith("png"):
                self.plotter = PngPlotter(open(value, "wb+"))
                self.plotter.open()
                self.log("PngController")
            elif value.endswith("egv"):
                self.plotter = NanoPlotter()
                self.plotter.open(connect=FileWriteConnection(value))
                self.log("EgvNanoController")
            elif value == "print":
                self.plotter = NanoPlotter()
                self.plotter.open(connect=PrintConnection())
                self.log("PrintNanoController")
            elif value == "mock":
                self.plotter = NanoPlotter()
                self.plotter.open(usb=MockUsb())
                self.log("MockUsb NanoController")
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
