#!/usr/bin/env python

from math import *

from interpolate import interpolate


class LaserM2:

    def __init__(self):
        self.board_name = "LASER-M2"

    def make_speed(self, feed=None, step=0):
        board_name = self.board_name
        append_code = ""
        if feed < .4:
            B = 16777471.974
            M = 100.211
            append_code = "C"
        elif feed < 7:
            B = 255.97
            M = 100.21
            append_code = "C"
        else:
            B = 236
            M = 1202.5
        speed_code = self.speed_code(feed, B, M)
        if step == 0:
            diag_linterp = self.make_diagonal_speed_interpolator(board_name)
            if feed <= 240.0:
                C4 = "%03d" % (floor(min(feed / 2.0 + 1, 128)))
                C5 = "%06d" % (int(round(diag_linterp[feed / 2.0], 0)))
            else:
                C4 = "000"
                C5 = "000000"
            # speed_text = "C%s000000000" %(speed_code)
            speed_text = "C%s%s%s" % (speed_code, C4, C5)
            # speed_text = "C%s %s %s" %(speed_code,C4,C5)
        else:
            speed_text = "%sG%03d" % (speed_code, abs(step))
        speed_text += append_code
        return speed_text

    def make_diagonal_speed_interpolator(self, board_name):
        # I have not been able to figure out the relationship between the speeds
        # in the first column and the codes in the second columns below.
        # these codes somehow ensure the speeds on the diagonal are the same horizontal
        # and vertical moves.  For now we will just use tables and interpolate as needed.
        vals = [
            [0.010, 2617140],
            [0.050, 523130],
            [0.100, 261193],
            [0.150, 174129],
            [0.200, 130224],
            [0.300, 87064],
            [0.400, 65112],
            [0.500, 52089],
            [0.600, 43160],
            [0.700, 37101],
            [0.800, 32184],
            [0.900, 29021],
            [0.990, 26112],
            [1.000, 13022],
            [1.500, 8185],
            [2.000, 4092],
            [3.000, 2046],
            [3.500, 1222],
            [4.000, 1079],
            [4.500, 1041],
            [4.990, 1012],
            [5.000, 223],
            [6.000, 159],
            [6.990, 136],
            [7.000, 5155],
            [8.000, 4092],
            [9.000, 3125],
            [10.000, 2219],
            [12.000, 2003],
            [12.080, 2000],
            [12.090, 1255],
            [12.500, 1238],
            [13.000, 1185],
            [15.000, 1079],
            [17.000, 1006],
            [17.450, 1000],
            [17.460, 255],
            [18.000, 235],
            [19.000, 211],
            [20.000, 191],
            [25.000, 123],
            [30.000, 86],
            [40.000, 49],
            [50.000, 31],
            [60.000, 21],
            [70.000, 16],
            [80.000, 12],
            [90.000, 9],
            [100.000, 7],
            [120.000, 5],
            [150.000, 4],
            [200.000, 3],
            [220.000, 2],
            [230.000, 2],
            [240.000, 2],
            [241.000, 0]
        ]
        xvals = []
        yvals = []
        for i in range(len(vals)):
            xvals.append(vals[i][0])
            yvals.append(vals[i][1])
        return interpolate(xvals, yvals)

    def speed_code(self, feed, B, M):
        V = B - M / float(feed)
        C1 = floor(V)
        C2 = floor((V - C1) * 255.0)
        s_code = "V%03d%03d%d" % (C1, C2, 1)
        # s_code = "V%03d %03d %d" %(C1,C2,1)
        return s_code


if __name__ == "__main__":
    board = LaserM2()
    # values  = [.1,.2,.3,.4,.5,.6,.7,.8,.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,70,90,100]
    values = [.01, .05, .1, 10, 400]
    step = 0
    for value_in in values:
        print("% 8.2f" % value_in, ": ",)
        print(board.make_speed(value_in, step=step))
    print("DONE")
