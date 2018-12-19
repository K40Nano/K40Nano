from math import *


class LaserA:

    def __init__(self):
        self.board_name = "LASER-A"

    def make_speed(self, feed=None, step=0):
        if feed <= .7:
            M = 198.438
            B = 16777468.940
        else:
            M = 198.437
            B = 252.940
        speed_code = self.speed_code(feed, B, M)
        if step == 0:
            speed_text = "C%s" % speed_code
        else:
            speed_text = "%sG%03d" % (speed_code, abs(step))
        return speed_text

    def make_diagonal_speed_interpolator(self):
        # LASER-A and LASER-B do not have this type of speed code.
        return None

    def speed_code(self, feed, B, M):
        V = B - M / float(feed)
        C1 = floor(V)
        C2 = floor((V - C1) * 255.0)
        s_code = "V%03d%03d%d" % (C1, C2, 1)
        # s_code = "V%03d %03d %d" %(C1,C2,1)
        return s_code


if __name__ == "__main__":
    board = LaserA()
    # values  = [.1,.2,.3,.4,.5,.6,.7,.8,.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,70,90,100]
    values = [.01, .05, .1, 10, 400]
    step = 0
    for value_in in values:
        print("% 8.2f" % value_in, ": ", )
        val = board.make_speed(value_in, step=step)
        txt = ""
        for c in val:
            txt += chr(c)
        print(txt)
    print("DONE")
