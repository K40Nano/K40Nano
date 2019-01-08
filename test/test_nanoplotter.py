import os
import unittest

from k40nano import *


class TestNanoController(unittest.TestCase):

    def test_nano_controller_home(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.home()
        match = "IPP\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_move(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.move(1, 1)
        match = "IBaRaS1P\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_string_move(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_concat_mode()
            plotter.move(1, 0)
            plotter.move(0, 1)
        match = "IBaNRaNS1P\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_compact(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_compact_mode(50)
            plotter.move(1, 0)
            plotter.move(0, 1)
            speed_code = plotter.board.make_speed(50.0, 0)
        match = "I" + speed_code + "NRBS1EBaRaFNSE\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_diagonal(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_compact_mode(50)
            plotter.move(1, 1)
            speed_code = plotter.board.make_speed(50.0, 0)
        match = "I" + speed_code + "NRBS1EMaFNSE\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_reset(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_compact_mode(50)
            plotter.move(1, 0)
            plotter.move(0, 1)
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode()
            plotter.move(1, 1)
            speed_code = plotter.board.make_speed(50.0, 0)
        match = "I" + speed_code + "NRBS1EBaRa@NSE" + speed_code + "NRBS1EMaFNSE\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_speedchange(self):
        filename = "test.egv"

        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_compact_mode(50)
            plotter.move(1, 0)
            plotter.move(0, 1)
            plotter.exit_compact_mode_reset()
            plotter.enter_compact_mode(75)
            plotter.move(1, 1)
            speed_code0 = plotter.board.make_speed(50.0, 0)
            speed_code1 = plotter.board.make_speed(75.0, 0)
        match = "I" + speed_code0 + "NRBS1EBaRa@NSE" + speed_code1 + "NRBS1EMaFNSE\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_sc_rapidmove(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_compact_mode(50)
            plotter.move(1, 0)
            plotter.move(0, 1)
            plotter.exit_compact_mode_reset()
            plotter.move(2, 2)
            plotter.enter_compact_mode(75)
            plotter.move(1, 1)
            speed_code0 = plotter.board.make_speed(50.0, 0)
            speed_code1 = plotter.board.make_speed(75.0, 0)
        match = "I" + speed_code0 + "NRBS1EBaRa@NSEBbRbN" + speed_code1 + "NRBS1EMaFNSE\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_rapidmove(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_compact_mode(50)
            plotter.move(1, 0)
            plotter.move(0, 1)
            plotter.exit_compact_mode_reset()
            plotter.move(2, 2)
            plotter.enter_compact_mode()
            plotter.move(1, 1)
            speed_code0 = plotter.board.make_speed(50.0, 0)
        match = "I" + speed_code0 + "NRBS1EBaRa@NSEBbRbN" + speed_code0 + "NRBS1EMaFNSE\n"
        lines = []
        with open(filename, "r+") as f:
            lines.append(f.readline())
        self.assertEqual(match, lines[0])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_default(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.move(1, 0)
            plotter.move(0, 1)
            plotter.move(2, 2)
            plotter.move(-1, -1)
        lines = []
        with open(filename, "r+") as f:
            while True:
                line = f.readline()
                if line is None or len(line) == 0:
                    break
                lines.append(line)
        self.assertEqual("IBaS1P\n", lines[0])
        self.assertEqual("IRaS1P\n", lines[1])
        self.assertEqual("IBbRbS1P\n", lines[2])
        self.assertEqual("ITaLaS1P\n", lines[3])
        self.addCleanup(os.remove, filename)

    def test_nano_controller_concat(self):
        filename = "test.egv"
        with NanoPlotter(connection=FileWriteConnection(filename)) as plotter:
            plotter.enter_concat_mode()
            plotter.move(1, 0)
            plotter.move(0, 1)
            plotter.move(2, 2)
            plotter.move(-1, -1)
        lines = []
        with open(filename, "r+") as f:
            while True:
                line = f.readline()
                if line is None or len(line) == 0:
                    break
                lines.append(line)
        self.assertEqual("IBaNRaNBbRbNTaLaNS1P\n", lines[0])
        self.addCleanup(os.remove, filename)
