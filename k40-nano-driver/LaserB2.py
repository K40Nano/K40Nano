from math import *

from interpolate import interpolate


class LaserB2:
    def __init__(self):
        self.board_name = "LASER-B2"

    def make_speed(self, feed=None, step=0):
        append_code = ""
        if feed <= .7:
            M = 200.422
            B = 16777468.941
            append_code = "C"
        elif feed <= 6:
            M = 200.423
            B = 252.942
            append_code = "C"
        elif feed <= 9:
            M = 2405.109
            B = 16777468.947
        else:
            M = 2405.008
            B = 252.944
        speed_code = self.speed_code(feed, B, M)
        if step == 0:
            speed_text = "C%s000000000" % (speed_code)
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
            [0.100, 523],
            [0.200, 261],
            [0.300, 174],
            [0.400, 130],
            [0.500, 104],
            [0.600, 87],
            [0.700, 74],
            [0.800, 65112],
            [0.900, 58043],
            [1.000, 26044],
            [2.000, 8185],
            [3.000, 4092],
            [4.000, 2158],
            [5.000, 1190],
            [6.000, 1063],
            [7.000, 11055],
            [8.000, 8185],
            [9.000, 6250],
            [10.000, 5182],
            [15.000, 2158],
            [20.000, 1126],
            [30.000, 172],
            [50.000, 63],
            [100.000, 15],
            [150.000, 8],
            [200.000, 6]
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
    board = LaserB2()
    # values  = [.1,.2,.3,.4,.5,.6,.7,.8,.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,70,90,100]
    values = [.01, .05, .1, 10, 400]
    step = 0
    for value_in in values:
        print("% 8.2f" % value_in, ": ",)
        val = board.make_speed(value_in, step=step)
        txt = ""
        for c in val:
            txt += chr(c)
        print(txt)
    print("DONE")
