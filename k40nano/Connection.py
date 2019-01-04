#!/usr/bin/env python


class Connection:
    def __init__(self):
        pass

    def send(self, data):
        """
        Writes all data immediately.
        :param data:
        :return:
        """
        self.write(data)
        self.flush()

    def write(self, data=None):
        """
        Buffers data, sending any complete packets.
        :param data:
        :return:
        """
        pass

    def flush(self):
        """
        Writes all buffered data immediately.
        :param data:
        :return:
        """
        pass

    def buffer(self, data):
        """
        Appends data to the buffer.
        :param data:
        :return:
        """
        pass

    def open(self):
        """
        Connects.
        """
        pass

    def close(self):
        """
        Disconnects.
        """
        pass

    def wait(self):
        """
        Waits for writes to finish.
        """
        pass
