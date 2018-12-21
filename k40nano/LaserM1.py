from math import *

from interpolate import interpolate


class LaserM1:

    def __init__(self):
        self.board_name = "LASER-M1"

    def make_speed(self, feed=None, step=0):
        if feed <= 5:
            M = 1202.531
            B = 16777452.003
        else:
            M = 1202.562
            B = 236.007
        speed_code = self.speed_code(feed, B, M)
        if step == 0:
            speed_text = "C%s000000000" % (speed_code)
        else:
            speed_text = "%sG%03d" % (speed_code, abs(step))
        return speed_text

    def make_diagonal_speed_interpolator(self, board_name):
        # I have not been able to figure out the relationship between the speeds
        # in the first column and the codes in the second columns below.
        # these codes somehow ensure the speeds on the diagonal are the same horizontal
        # and vertical moves.  For now we will just use tables and interpolate as needed.

        vals = [
            [0.100, 3141014],
            [0.200, 1570135],
            [0.300, 1047004],
            [0.400, 785067],
            [0.500, 628054],
            [0.600, 523130],
            [0.700, 448185],
            [0.800, 392161],
            [0.900, 349001],
            [1.000, 157013],
            [2.000, 52089],
            [3.000, 26044],
            [4.000, 15180],
            [5.000, 10120],
            [6.000, 7122],
            [7.000, 5155],
            [8.000, 4092],
            [9.000, 3125],
            [10.000, 2219],
            [20.000, 191],
            [50.000, 31],
            [70.000, 16],
            [100.000, 7],
            [150.000, 4],
            [200.000, 3]
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
    board = LaserM1()
    # values  = [.1,.2,.3,.4,.5,.6,.7,.8,.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,70,90,100]
    values = [.01, .05, .1, 10, 400]
    step = 0
    for value_in in values:
        print("% 8.2f" % value_in, ": ",)
        print(board.make_speed(value_in, step=step))
    print("DONE")
