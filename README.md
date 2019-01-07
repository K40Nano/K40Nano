# K40Nano
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40Nano is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it a helpful and proper encapsulation and a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.


Compatibility
---
K40Nano should be compatible with both Python 2.7 and 3.6.


Project Status
---

Seems to work. Wrote Keyburn to access the device via keystrokes and it went off without a hitch, including turning on a particular speed and running direction. The export code looked good and it ran fine on the machine.

API:
---

The API encapsulates the two major advances of K40 Whisperer, writing into `LHYMICRO-GL` format and transmitting data directly to the K40 device. Writing the `LHYMICRO-GL` encoded commands is done with NanoPlotter and it transmits this data to the device with NanoConnection.

The primary method of controlling the device is with a `Plotter` which is just like a pen plotter interface. This should be very simple and easy to use, and yet able to encapsulate everything we are doing.

Plotters
---

The M, A, B series boards use `LHYMICRO-GL` encoding which is derived from pen-plotters. As such, plotter interface is the best, simplest, and most natural way to interact with the K40.
 
Plotters have:
* open()
* move(dx, dy)
* down()
* up()
* close()

This captures almost everything a laser cutter can do.

For debugging purposes, there are also specialty plotters which write to file types rather than to a NanoConnection. These are `PngPlotter` and `SvgPlotter` which plot to PNG files and an SVG files respectively.


NanoPlotter
---

When writing to `LHYMICRO-GL` format, there are a few non-plotter based judgment calls to be made here as to how we should encode the data. As such, `NanoPlotter` has a few commands outside the scope of typical plotter to change modes. Mostly this control the compact mode for the device and how we would like our data packaged. These are:

* enter_concat_mode()
* enter_compact_mode(speed, harmonic_step)
* exit_compact_mode_finish()
* exit_compact_mode_reset()
* exit_compact_mode_break()

In default mode, the device will simply execute the command immediately and pop the stack. This sends everything as rapid commands, even turning the laser on and off without moving it.

In concat mode, commands are all strung together. They may be delayed until the current packet is full. But these are all rapid commands, where the users has either chosen to not flush out the packet after each command. These commands will be written to the buffer but may not be sent until the (30 byte) packet is full and as sending prematurely may introduce undesirable commands to the stack. When the NanoPlotter is closed, the packets are flushed by popping the stack.

Internally there a mode called which is basically the same as concat, except that when we close a connection in unfinished it must enter compact_mode() and then exit_compact_mode_finish(), this is because it previously was in compact mode and we cannot be sure the current task is actually finished, so we cannot pop the stack.

If we do not manually invoke `enter_concat_mode()` and we only exit compact with `exit_compact_mode_finish()`, this mode will not occur.

The device itself has a compact mode. These are compacted instruction sets, executed quickly, at a particular head-movement speed. You `enter_compact_mode()` at a specific speed and the plotter commands are executed in compact_mode on the device. This is for your typical vector-cuts, vector-engraves and raster line engraves, anything where you need to go slower to cut deeper, it also reduces the amount of data to be sent.

There are three ways to exit this mode.
* Finish. This sends a finished command, and blocks our code operations until the device itself says the task is complete. Returning us to default mode.
* Reset. This sends a reset command, allowing additional code to be sent without delay. It returns us to unfinished mode.
* Break. Doesn't reset the speed commands within the device. It returns us to unfinished mode. We can still reenter compact mode at whatever speed, but in that case NanoPlotter has to (enter_compact, reset, exit_compact) to permit the speed change or to close the plotter. But, if your intention is to want to run more compact commands at at the same speed after some rapid moves, break will allow that without resetting the speed internally.

In addition to those we have a couple helpful device specific commands:
* `home()` : Homes the device back to 0,0 (upper left corner)
* `unlock_rail()` : Allows you to manually drag the rail into position.
* `lock_rail()` : Locks the rail again. (this will be done automatically for most things)
* `abort()` : Kills the current job, restores us to default mode.

These should be done in default mode. If we aren't in default mode, it will attempt to get there by exiting whatever modes we are in. Except for `abort()` which won't do anything other than kill whatever the device is currently doing.

NOTE: down() and up() commands are, in default mode, single-packet commands. This will cause the K40 to turn on the laser and just sit there firing the laser. If this is not desirable, do not use these commands in default mode.

Connections
---
The NanoPlotter sends its data via a connection. In addition to the NanoConnection, there are a couple other debug connection classes `FileWriteConnection` and `PrintConnection` that can be requested when we open the NanoConnection, if these are used by the NanoPlotter the data will be redirected to them and written to a file or printed accordingly.

Connections try to mimic a file-like object, and they have:

* open() - Opens the connection
* send(data) - Sends data immediately.
* write(data) - Writes data to the buffer and sends as packets complete.
* flush() - Sends the buffer immediately.
* buffer(data) - Buffers the data, and makes no attempt to transmit it.
* close() - Closes the connection
* wait() - Waits for the device to report task complete.


NanoConnection
---
The NanoConnection class is based on almost exclusively a highly-streamlined version of K40 Whisperer code and performs the interface, packetizations, and handling the usb connection to the device. The USB connection is done by the NanoUsb class. For testing purposes, the NanoUsb class can be switched, with the MockUsb class. The MockUsb class will also be used if there is no valid `pyusb` install.

If you wish to send data via the NanoConnection direcly, for example you want to feed it pre-made data from an EGV file, you would only need to open the connection, write() the data, flush() the buffer, and close() the connection.  And the connection will deal with all the packetization and crc errors and resends for you.


Units
---
The code throughout uses mils (1/1000th of an inch). So 2000 is 2 inches. 


Coordinate System
---
The coordinate system is that the origin is in the upper left corners and all Y locations are DOWN. Which is to say higher Y values mean lower on the device. This is similar to all modern graphics system, but seemingly different than `K40 Whisperer` which seemed to strongly imply that all Y values are negative. Internally the commands are all relative with a positive magnitude.

