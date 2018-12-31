#!/usr/bin/env python

import struct
import zlib
from math import ceil


# MIT LICENSE

class PngRaster:
    """
    Png Raster is a image reading and writing library that loads and save files into and out of PNG.

    The code permits PNG illegal formats, like bit_depth=1, color_type=2 (1 bit per triplet color) or bit_depth 27,
    color_type=0 (27 bit grayscale), and will properly stack these across multiple bytes as needed. These are not
    generally permitted by PNG and basically nothing will read them. You should stick to the permitted values.

    http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html
    """

    def __init__(self, width=None, height=None, bit_depth=8, color_type=2):
        if height is not None:
            self.width = width
            self.height = height
            self.bit_depth = bit_depth
            self.color_type = color_type
            self.samples_per_pixel = self.get_sample_count(color_type)
            self.stride = self.get_stride(self.samples_per_pixel, self.bit_depth, self.width) + 1
            self.palette = None
            self.buf = []
            for i in range(height):
                self.buf.append(bytearray(b'\x00' * self.stride))

    def index_color(self, index, value=None):
        byte_index_start = index * 3
        byte_index_end = byte_index_start + 3
        if self.palette is None:
            self.palette = bytearray(b'')
        if byte_index_end > len(self.palette):
            self.palette += b'\x00' * (byte_index_end - len(self.palette))
        section = self.palette[byte_index_start: byte_index_end]
        section = (4 - len(section)) * b'\x00' + section
        color = struct.unpack(">I", section)[0]
        if value is not None:
            for pos in range(byte_index_end - 1, byte_index_start - 1, -1):
                self.palette[pos] = value & 0xff
                value >>= 8
        return color

    def pixel(self, x, y, sample=None):
        """
        Reads the current value of the sample, writes the given sample value (if it exists).

        :param x: location of the sample within the scanline
        :param y: index of the scanline
        :param sample: sample value, this should be in the units of the png file.
        :return: the value of the sample in that location.
        """
        scanline = self.buf[y]
        pixel_length_in_bits = self.samples_per_pixel * self.bit_depth
        return self.scanline_sample(scanline, pixel_length_in_bits, x, sample)

    @staticmethod
    def scanline_sample(scanline, pixel_length_in_bits, x, sample=None):
        start_pos_in_bits = x * pixel_length_in_bits
        end_pos_in_bits = start_pos_in_bits + pixel_length_in_bits - 1
        start_pos_in_bytes = int(start_pos_in_bits / 8) + 1  # byte 0 is interlacing
        end_pos_in_bytes = int(end_pos_in_bits / 8) + 1  # byte 0 is interlacing

        section = scanline[start_pos_in_bytes:end_pos_in_bytes + 1]
        section = (4 - len(section)) * b'\x00' + section
        value = struct.unpack(">I", section)[0]
        unused_bits_right_of_sample = (8 - (end_pos_in_bits + 1) % 8) % 8
        mask_sample_bits = (1 << pixel_length_in_bits) - 1
        original = (value >> unused_bits_right_of_sample) & mask_sample_bits
        if sample is not None:
            value &= ~(mask_sample_bits << unused_bits_right_of_sample)
            value |= (sample & mask_sample_bits) << unused_bits_right_of_sample
            for pos in range(end_pos_in_bytes, start_pos_in_bytes - 1, -1):
                try:
                    scanline[pos] = value & 0xff
                    value >>= 8
                except IndexError:
                    print(pos, len(scanline))
        return original

    @staticmethod
    def get_stride(sample_count, bit_depth, width):
        return int(ceil(bit_depth * sample_count * width / 8.0))

    @staticmethod
    def get_sample_count(color_type):
        if color_type == 0:
            return 1
        elif color_type == 2:
            return 3
        elif color_type == 3:
            return 1
        elif color_type == 4:
            return 2
        elif color_type == 6:
            return 4
        else:
            return 1

    def save_png(self, filename):
        with open(filename, "wb+") as f:
            f.write(self.get_png_bytes())

    def get_png_bytes(self):
        buf = self.buf
        width = self.width
        height = self.height
        raw_data = b''.join(bytes(buf[i]) for i in range(0, height))

        def png_pack(png_tag, data):
            chunk_head = png_tag + data
            return struct.pack("!I", len(data)) + chunk_head + struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))

        if self.palette is None:
            plte = b''
        else:
            plte = png_pack(b'PLTE', self.palette)
        return b''.join([
            b'\x89PNG\r\n\x1a\n',
            png_pack(b'IHDR', struct.pack("!2I5B", width, height, self.bit_depth, self.color_type, 0, 0, 0)),
            plte,
            png_pack(b'IDAT', zlib.compress(raw_data, 9)),
            png_pack(b'IEND', b'')])

    @staticmethod
    def read_png_chunks(file):
        while True:
            length_bytes = file.read(4)
            if len(length_bytes) == 0:
                break
            length = struct.unpack(">I", length_bytes)[0]
            byte = file.read(4)
            signature = byte.decode('utf8')
            data = file.read(length)
            crc = file.read(4)
            if len(signature) == 0:
                break
            yield signature, data
            if signature == 'IEND':
                break

    @staticmethod
    def as_samples(bit_depth, sample_count, scanline):
        pixel_length_in_bits = bit_depth * sample_count
        bit_depth_mask = (1 << bit_depth) - 1
        mask_sample_bits = (1 << pixel_length_in_bits) - 1
        for start_pos_in_bits in range(0, len(scanline) * 8, pixel_length_in_bits):
            end_pos_in_bits = start_pos_in_bits + pixel_length_in_bits - 1
            start_pos_in_bytes = int(start_pos_in_bits / 8) + 1
            end_pos_in_bytes = int(end_pos_in_bits / 8) + 1

            section = scanline[start_pos_in_bytes:end_pos_in_bytes + 1]
            section = (4 - len(section)) * b'\x00' + section
            value = struct.unpack(">I", section)[0]
            unused_bits_right_of_sample = (8 - (end_pos_in_bits + 1) % 8) % 8
            sample = (value >> unused_bits_right_of_sample) & mask_sample_bits
            if sample_count == 1:
                yield sample
            else:
                yield [
                    (sample >> bit_move) & bit_depth_mask
                    for bit_move in range((sample_count - 1) * bit_depth, -1, -bit_depth)
                ]

    @staticmethod
    def png_scanlines(file):
        if file.read(8) != b'\x89PNG\r\n\x1a\n':
            return  # Not a png file.
        decompress = zlib.decompressobj()
        buf = b''
        bit_depth = 0
        stride = 1
        sample_count = 1
        while True:
            length_bytes = file.read(4)
            if len(length_bytes) == 0:
                break
            length = struct.unpack(">I", length_bytes)[0]
            byte = file.read(4)
            signature = byte.decode('utf8')
            if len(signature) == 0:
                break
            if signature == 'IHDR':
                data = file.read(length)
                width = struct.unpack(">I", data[0:4])[0]
                # height = struct.unpack(">I", data[4:8])[0]
                bit_depth = data[8]
                color_type = data[9]
                sample_count = PngRaster.get_sample_count(color_type)
                stride = PngRaster.get_stride(sample_count, bit_depth, width) + 1
                file.seek(4, 1)  # skip crc
                continue
            if signature == 'IDAT':
                while length > 0:
                    read_amount = min(stride, length)
                    buf += decompress.decompress(file.read(read_amount))
                    length -= read_amount
                    while len(buf) >= stride:
                        yield [x for x in PngRaster.as_samples(bit_depth, sample_count, buf[:stride])]
                        buf = buf[stride:]
                file.seek(4, 1)  # skip crc
                continue
            if signature == 'IEND':
                buf += decompress.flush()
                while len(buf) >= stride:
                    yield [x for x in PngRaster.as_samples(bit_depth, sample_count, buf[:stride])]
                    buf = buf[stride:]
                file.seek(4, 1)
                return
            data = file.read(length)
            crc = file.read(4)

    def read_png_file(self, file):
        with open(file, "rb") as f:
            self.read_png_stream(f)

    def read_png_stream(self, file):
        if file.read(8) != b'\x89PNG\r\n\x1a\n':
            return  # Not a png file.
        zlib_data = b''
        for chunk in self.read_png_chunks(file):
            signature = chunk[0]
            data = chunk[1]
            if signature == 'IHDR':
                self.width = struct.unpack(">I", data[0:4])[0]
                self.height = struct.unpack(">I", data[4:8])[0]
                self.bit_depth = data[8]
                self.color_type = data[9]
            elif signature == 'PLTE':
                self.palette = bytearray(data)
            elif signature == 'IDAT':
                zlib_data += data
            elif signature == 'IEND':
                break
        png_data = zlib.decompress(zlib_data)
        self.samples_per_pixel = self.get_sample_count(self.color_type)
        self.stride = self.get_stride(self.samples_per_pixel, self.bit_depth, self.width) + 1
        self.buf = [
            bytearray(png_data[line:line + self.stride])
            for line in range(0, len(png_data), self.stride)
        ]

    def draw_line(self, x0, y0, x1, y1, color=0):
        """
        Simple implementation of Bresenham's line draw algorithm to draw lines onto the raster.

        :param x0: x value
        :param y0: y value
        :param x1: second x value
        :param y1: second y value
        :param color: the color we are writing.
        :return:
        """
        dy = y1 - y0  # BRESENHAM LINE DRAW ALGORITHM
        dx = x1 - x0
        if dy < 0:
            dy = -dy
            step_y = -1
        else:
            step_y = 1
        if dx < 0:
            dx = -dx
            step_x = -1
        else:
            step_x = 1
        if dx > dy:
            dy <<= 1  # dy is now 2*dy
            dx <<= 1
            fraction = dy - (dx >> 1)  # same as 2*dy - dx
            self.plot(x0, y0, color)

            while x0 != x1:
                if fraction >= 0:
                    y0 += step_y
                    fraction -= dx  # same as fraction -= 2*dx
                x0 += step_x
                fraction += dy  # same as fraction += 2*dy
                if x0 != x1:
                    self.plot(x0, y0, color)
        else:
            dy <<= 1  # dy is now 2*dy
            dx <<= 1  # dx is now 2*dx
            fraction = dx - (dy >> 1)
            self.plot(x0, y0, color)
            while y0 != y1:
                if fraction >= 0:
                    x0 += step_x
                    fraction -= dy
                y0 += step_y
                fraction += dx
                if y0 != y1:
                    self.plot(x0, y0, color)

    def fill(self, color):
        for y in range(self.height):
            for x in range(self.width):
                self.pixel(x, y, color)

    def plot(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixel(x, y, color)


if __name__ == "__main__":
    raster = PngRaster(100, 100, 1, 3)
    raster.fill(0)
    raster.draw_line(0, 0, 100, 100, 1)
    raster.draw_line(0, 100, 100, 0, 1)
    raster.index_color(0, 0x00FF00)
    raster.index_color(1, 0xFF0000)
    raster.save_png("default.png")
