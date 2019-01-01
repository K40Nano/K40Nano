#!/usr/bin/env python

from __future__ import print_function


class PrintConnection:

    def write(self, data):
        print(data)

    def write_completed_packets(self, data):
        print(data)

    def write_buffer(self):
        pass

    def append(self, data):
        print(data)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send_valid_packet(self, packet):
        print("Send Packet: ", packet)

    def send_hello(self):
        print("Sending Hello.")

    def wait(self):
        print("Attempting Wait.")

    def read_response(self):
        print("Read Response")
        return 206
