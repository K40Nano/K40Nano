import unittest

from k40nano import *


class TestLaserSpeeds(unittest.TestCase):

    def test_generate_speed_M2(self):
        b = LaserM2()
        results = [
            "CV167674502221001000482C",
            "CV1677546719210011831886C",
            "CV167764692201001523130C",
            "CV1151911006000223",
            "CV2322531000000000"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

    def test_generate_speed_M1(self):
        b = LaserM1()
        results = [
            "CV166571982301000000000",
            "CV167534010971000000000",
            "CV167654261761000000000",
            "CV1151911000000000",
            "CV2330001000000000"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

    def test_generate_speedM(self):
        b = LaserM()
        results = [
            "CV166571982301",
            "CV167534010971",
            "CV167654261761",
            "CV1151911",
            "CV2322541"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

    def test_generate_speedA(self):
        b = LaserA()
        results = [
            "CV167576250351",
            "CV167735000451",
            "CV167754841421",
            "CV2330241",
            "CV2521131"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

    def test_generate_speedB2(self):
        b = LaserB2()
        results = [
            "CV167574261881000000000C",
            "CV167734601271000000000C",
            "CV167754641831000000000C",
            "CV0121131000000000",
            "CV2462371000000000"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

    def test_generate_speedB1(self):
        b = LaserB1()
        results = [
            "CV167576250351000000000",
            "CV167735000451000000000",
            "CV167754841421000000000",
            "CV2330241000000000",
            "CV2521121000000000"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

    def test_generate_speedB(self):
        b = LaserB()
        results = [
            "CV167576250351",
            "CV167735000451",
            "CV167754841421",
            "CV2330241",
            "CV2521131"
        ]
        feed_values = [.01, .05, .1, 10, 400]
        for i in range(len(feed_values)):
            self.assertEqual(results[i], b.make_speed(feed_values[i]))

