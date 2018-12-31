#!/usr/bin/env python


class FileWriteConnection:
    def __init__(self, filename):
        if not filename.endswith(".egv"):
            filename += ".egv"
        self.filename = filename
        self.f = None

    def write(self, data):
        self.write_completed_packets(data)
        self.write_buffer()

    def write_completed_packets(self, data):
        if self.f is not None:
            self.f.write(data.decode("utf-8"))

    def write_buffer(self):
        pass

    def append(self, data):
        if self.f is not None:
            self.f.write(data)

    def connect(self):
        self.f = open(self.filename, "w+")

    def disconnect(self):
        self.f.flush()
        self.f.close()

    def send_valid_packet(self, packet):
        pass

    def send_hello(self):
        pass

    def wait(self):
        pass

    def read_response(self):
        pass


if __name__ == "__main__":
    connection = FileWriteConnection("text.txt")
    connection.connect()
    connection.write(b'IPP')
    connection.disconnect()
