import struct
import zlib
from math import ceil


def get_stride(sample_count, bit_depth, width):
    return int(ceil(bit_depth * sample_count * width / 8.0))


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
            bit_depth = struct.unpack_from("B", data[8])[0]
            color_type = struct.unpack_from("B", data[9])[0]
            sample_count = get_sample_count(color_type)
            stride = get_stride(sample_count, bit_depth, width) + 1
            file.seek(4, 1)  # skip crc
            continue
        if signature == 'IDAT':
            while length > 0:
                read_amount = min(stride, length)
                buf += decompress.decompress(file.read(read_amount))
                length -= read_amount
                while len(buf) >= stride:
                    yield [x for x in as_samples(bit_depth, sample_count, buf[:stride])]
                    buf = buf[stride:]
            file.seek(4, 1)  # skip crc
            continue
        if signature == 'IEND':
            buf += decompress.flush()
            while len(buf) >= stride:
                yield [x for x in as_samples(bit_depth, sample_count, buf[:stride])]
                buf = buf[stride:]
            file.seek(4, 1)
            return
        data = file.read(length)
        crc = file.read(4)


def is_on(sample):
    if isinstance(sample, int):
        return not sample
    if isinstance(sample, list):
        return not sample[0]


def parse_png(f, controller):
    if isinstance(f, str):
        with open(f, "rb") as f:
            parse_png(f, controller)
            return
    increment = 1
    on_count = 0
    off_count = 0
    for scanline in png_scanlines(f):
        if increment == -1:
            scanline = reversed(scanline)
        for i in scanline:
            if is_on(i):
                if off_count != 0:
                    controller.move(off_count, 0, slow=True, laser=False)
                    off_count = 0
                on_count += increment
            else:
                if on_count != 0:
                    controller.move(on_count, 0, slow=True, laser=True)
                    on_count = 0
                off_count += increment
        if off_count != 0:
            controller.move(off_count, 0, slow=True, laser=False)
            off_count = 0
        if on_count != 0:
            controller.move(on_count, 0, slow=True, laser=True)
            on_count = 0
        controller.move(0, 1, slow=True, laser=False)
        increment = -increment
