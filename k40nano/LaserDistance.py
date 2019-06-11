
"""
This script uses a stream to communicate with the K40 Laser Cutter.

Copyright (C) 2017 Scorch www.scorchworks.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""


def encode_distance(distance_mils):
    if abs(distance_mils - round(distance_mils, 0)) > 0.000001:
        raise Exception('Distance values should be integer value (inches*1000)')
    distance_mils = int(distance_mils)
    code = b''
    value_z = 255

    while distance_mils >= 255:
        code += b'z'
        distance_mils -= value_z
    if distance_mils == 0:
        return code
    elif distance_mils < 26:  # codes  "a" through  "y"
        character = chr(96 + distance_mils)
        return code + bytes(bytearray(character, 'utf8'))
    elif distance_mils < 52:  # codes "|a" through "|z"
        character = chr(96 + distance_mils - 25)
        return code + b'|' + bytes(bytearray(character, 'utf8'))
    elif distance_mils < 255:
        code += bytes(bytearray("%03d" % distance_mils, 'utf8'))
        return code
    else:
        raise Exception("Could not create distance")  # This really shouldn't happen.