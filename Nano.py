#!/usr/bin/env python

from __future__ import print_function

import glob
import sys
import time

from k40nano import *

NANO_VERSION = "0.0.2"


class NanoCommand:
    def __init__(self):
        self.wait = 0
        self.dx = 0
        self.dy = 0
        self.filename = None
        self.command = None


class Nano:
    def __init__(self, arguments):
        self.controller = NanoController()
        self.log = self.no_operation
        self.elements = list(reversed(arguments))
        if len(arguments) == 1:
            self.elements = ["-h"]
        self.elements.append("-e")  # always execute the stack.
        self.command_lookup = {
            "-i": self.command_input,
            "-o": self.command_output,
            "-p": self.command_passes,
            "-m": self.command_move,
            "-w": self.command_wait,
            "-e": self.command_execute,
            "-l": self.command_list,
            "-r": self.command_home,
            "-u": self.command_unlock,
            "-q": self.command_quiet,
            "-v": self.command_verbose,
            "-h": self.command_help,
        }

    def command_help(self, values):
        print("Nano v.", NANO_VERSION)
        print("-i [<input>]*, loads egv/png files")
        print("-o [<output>]?, sets output method")
        print("-p [n], sets the number of passes")
        print("-m [dx] [dy], move command")
        print("-w [seconds], wait_time")
        print("-e, executes egv stack")
        print("-l, lists egv stack")
        print("-r, resets to home position")
        print("-u, unlock rail")
        print("-q, quiet mode")
        print("-v, verbose mode")
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
        self.controller.release()

    def command_input(self, values):
        v = self.v()
        input_files = glob.glob(v)
        for input_file in input_files:
            m = NanoCommand()
            self.log("File:", input_file)
            m.filename = input_file
            values.append(m)
        return values

    def command_move(self, values):
        m = NanoCommand()
        m.dx = int(self.v())
        m.dy = int(self.v())
        values.append(m)
        self.log("Move:", m.dx, m.dy)
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
        for value in values:
            if value.dx != 0 or value.dy != 0:
                print("move:", value.dx, ",", value.dy)
            if value.wait != 0:
                print("wait:", value.wait)
            if value.filename is not None:
                print("burn:", value.filename)
            if value.command is not None:
                print(value.command)
        return values

    def command_execute(self, values):
        self.log("Executing:", len(values))
        for value in values:
            if value.dx != 0 or value.dy != 0:
                self.controller.move(value.dx, value.dy)
            if value.wait != 0:
                time.sleep(value.wait)
            if value.filename is not None:
                fname = str(value.filename).lower()
                if fname.endswith("egv"):
                    parse_egv(value.filename, self.controller)
                elif fname.endswith("png"):
                    self.controller.set_speed(52.1) #230
                    parse_png(value.filename, self.controller)
            if value.command is not None:
                value.command()
        return []

    def command_home(self, values):
        self.log("Home Position")
        m = NanoCommand()
        m.command = self.controller.home()
        values.append(m)
        return values

    def command_unlock(self, values):
        self.log("Unlock Rail")
        m = NanoCommand()
        m.command = self.controller.rail(False)
        values.append(m)
        return values

    def command_output(self, values):
        value = self.v()
        if value is None:
            self.controller = NanoController()
            self.log("NanoController")
        else:
            value = str(value)
            if value.endswith("svg"):
                self.controller = SvgController(value)
                self.log("SvgController")
            elif value.endswith("png"):
                self.controller = PngController(value)
                self.log("PngController")
            elif value.endswith("egv"):
                self.controller = NanoController(FileWriteConnection(value))
                self.log("EgvController")
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
# argv = ["-o", "svg", "-i", "outfile1.EGV", "-e"]
# argv = ["-o", "egv", "-i", "outfile2.EGV", "-e"]
# argv = ["-o", "png", "-i", "outfile2.EGV", "-e"]
nano = Nano(argv)
nano.execute()
