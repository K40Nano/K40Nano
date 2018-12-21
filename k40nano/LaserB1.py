from math import *

from interpolate import interpolate


class LaserB1:

    def __init__(self):
        self.board_name = "LASER-B1"

    def make_speed(self, feed=None, step=0):
        if feed <= .7:
            M = 198.438
            B = 16777468.940
        else:
            M = 198.437
            B = 252.939
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
        #################################################################

        vals = [
            [0.100, 518083],
            [0.200, 259041],
            [0.300, 172198],
            [0.400, 129148],
            [0.500, 103170],
            [0.600, 86099],
            [0.700, 74012],
            [0.800, 64202],
            [0.900, 57151],
            [1.000, 25234],
            [2.000, 8163],
            [5.000, 1186],
            [10.000, 120],
            [20.000, 31],
            [30.000, 14],
            [40.000, 8],
            [50.000, 5],
            [70.000, 2],
            [90.000, 1],
            [100.000, 1],
            [190.000, 0],
            [199.000, 0],
            [200.000, 0]
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
    board = LaserB1()
    # values  = [.1,.2,.3,.4,.5,.6,.7,.8,.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,70,90,100]
    values = [.01, .05, .1, 10, 400]
    step = 0
    for value_in in values:
        print("% 8.2f" % value_in, ": ",)
        print(board.make_speed(value_in, step=step))
    print("DONE")
