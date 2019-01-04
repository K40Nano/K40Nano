#!/usr/bin/env python

from .PngRaster import PngRaster


def is_on(sample):
    """
    Decides based on the sample from the image if this is on or off.
    If single sample (greyscale, indexed) it is on if not equal to 0
    If multi-sampled (RGB, RGBA) it is on if first value is not equal to 0
    (This will very likely be 0 pixels with 0 for red)
    :param sample:
    :return:
    """
    if isinstance(sample, int):
        return not sample
    if isinstance(sample, list):
        return not sample[0]


def parse_png(png_file, plotter, spread=1):
    if isinstance(png_file, str):
        with open(png_file, "rb") as png_file:
            parse_png(png_file, plotter)
            return
    increment = spread
    step = spread
    on_count = 0
    off_count = 0
    for scanline in PngRaster.png_scanlines(png_file):
        if increment < 0:
            scanline = reversed(scanline)
        for i in scanline:
            if is_on(i):
                if off_count != 0:
                    plotter.up()
                    plotter.move(off_count, 0)
                    off_count = 0
                on_count += increment
            else:
                if on_count != 0:
                    plotter.down()
                    plotter.move(on_count, 0)
                    on_count = 0
                off_count += increment
        if off_count != 0:
            plotter.up()
            plotter.move(off_count, 0)
            off_count = 0
        if on_count != 0:
            plotter.down()
            plotter.move(on_count, 0)
            on_count = 0
        plotter.up()
        plotter.move(0, step)
        increment = -increment
