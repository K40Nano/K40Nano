# K40Nano
API support for K40 Laser Cutter with Nano Boards.
(Derived from K40 Whisperer, by Scorch)

K40Nano is intended to pull out the low level functionality from K40Whisperer, improve, document, and ecapsulate it and present a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.

Install
---
To install via PyPI

`pip install k40nano`

Include `k40nano` as part your project requirements.

Compatibility
---
K40Nano should be compatible with both Python 2.7 and 3.6.


Examples
---
See the companion K40Tools project for examples and useful tools built for the API.
https://github.com/K40Nano/K40Tools


API
---

This API encapsulates the two major advances of K40 Whisperer, writing into `LHYMICRO-GL` format and transmitting data directly to the K40 device. Writing the `LHYMICRO-GL` encoded commands is done with `NanoPlotter` and it transmits this data to the device with `NanoConnection`.

The primary method of controlling the device is with a `Plotter` which is just like a pen plotter interface. This should be very simple and easy to use, and yet able to encapsulate everything we are doing.

NanoPlotter / Plotter interface
---

The M, A, B series boards use `LHYMICRO-GL` encoding which is derived from pen-plotters. As such, plotter interface is the best, simplest, and most natural way to interact with the K40.

For debugging purposes, there are also specialty plotters which write to file types rather than to a NanoConnection. These are `PngPlotter` and `SvgPlotter` which plot to PNG files and an SVG files respectively.

 
Plotters have:
* open()
* move(dx, dy)
* down()
* up()
* close()

* enter_concat_mode()
* enter_compact_mode(speed, harmonic_step)
* exit_compact_mode_finish()
* exit_compact_mode_reset()
* exit_compact_mode_break()

When writing to `LHYMICRO-GL` format, there are a few non-plotter based judgment calls to be made here as to how we should encode the data. As such, `NanoPlotter` uses a few mode altering commands outside the scope of typical plotter. Mostly this controls the compact mode for the device and how we would like our data packaged.

In default mode, the device will simply execute the command immediately and pop the stack. This sends everything as rapid commands, even turning the laser on and off without moving it.

In concat mode, commands are all strung together. They may be delayed until the current packet is full. But these are all rapid commands, where the users has chosen not flush out the packet after each command. These commands will be written to the buffer but may not be sent until the (30 byte) packet is full and as sending prematurely may introduce undesirable commands to the stack. When the NanoPlotter is closed, the packets are flushed by popping the stack.

Internally there a mode called "unfinished" which is basically the same as concat, except that when we close a connection in unfinished it must enter compact_mode() and then exit_compact_mode_finish(), this is because the device was previously was in compact mode and we cannot be sure the current task was actually finished, so we cannot safely pop the stack.

If we do not manually invoke `enter_concat_mode()` and we only exit compact mode with `exit_compact_mode_finish()`, the "unfinished" mode will not occur.

The device itself has a compact mode. These are compacted instruction sets, executed quickly, at a particular head-movement speed. You must call `enter_compact_mode()` at a specific speed and the plotter commands are executed in compact_mode on the device. This is typical for vector-cuts, vector-engraves and raster line engraves, anything where you need to go slower to cut deeper, it also reduces the amount of data to be sent.

There are three ways to exit this mode.
* Finish. This sends a finished command, and blocks our code operations until the device itself says the task is complete. Returning us to default mode.
* Reset. This sends a reset command, allowing additional code to be sent without delay, and returns us to unfinished mode.
* Break. Doesn't reset the speed commands within the device. It returns us to unfinished mode. We can still reenter compact mode at whatever speed, but if the speed has changed, NanoPlotter has to (enter_compact, reset, exit_compact) to permit the speed change or to close the plotter. But, if your intention is to run more compact commands at at the same speed after some rapid moves, break should permit that without resetting the speed internally.

In addition to theses we have a couple helpful device specific commands:
* `home()` : Homes the device back to 0,0 (upper left corner)
* `unlock_rail()` : Allows you to manually drag the rail into position.
* `lock_rail()` : Locks the rail again (this will be done automatically for most things).
* `abort()` : Kills the current job, restores us to default mode.

These should be done in default mode. If we aren't in default mode, the `NanoPlotter` will attempt get to default mode by exiting whatever modes the device is in. `abort()`, however, won't do anything other than kill whatever the device is currently doing and doesn't need to be called in any particular mode.

NOTE: In default mode, down() and up() commands are single-packet commands. This will cause the K40 to turn on the laser and just sit there firing the laser. If this is not desirable, do not use these commands in default mode.

Connections
---
The `NanoPlotter` sends its data via a connection. In addition to the `NanoConnection`, there are a couple other debug connection classes `FileWriteConnection` and `PrintConnection` that can be requested when we open the `NanoConnection`, if these are used by the NanoPlotter the data will be redirected to them and written to a file or printed to the screen accordingly.

Connections try to mimic a file-like object:

* open() - Opens the connection
* send(data) - Sends data immediately.
* write(data) - Writes data to the buffer and sends as packets complete.
* flush() - Sends the buffer immediately.
* buffer(data) - Buffers the data, and makes no attempt to transmit it.
* close() - Closes the connection
* wait() - Waits for the device to report task complete.

You can also, use the python `with` statement for connections and plotters to ensure we open and close our connections correctly.

NanoConnection
---
The `NanoConnection` class is based on almost exclusively a highly-streamlined version of K40 Whisperer code and performs the interface, packetizations, and handling the usb connection to the device. The USB connection is done by the `NanoUsb` class. For testing purposes, the `MockUsb` class can be exchanged for the `NanoUsb` class. The MockUsb class will also be used if there is no valid `pyusb` install.

If you wish to send data via the `NanoConnection` direcly, for example you want to feed it pre-made EGV data, you would only need to open the connection, write() the data, flush() the buffer, and close() the connection.  And the connection will deal with all the packetization and crc errors and resends for you.

```python
with NanoConnection(board="B1") as stream:
    stream.write("IPP")
```


Units
---
The code throughout uses mils (1/1000th of an inch). So 2000 is 2 inches, etc. The lasers have a dpi of 1000. In the speed code there we sometimes use period, as the speed codes are linear with regard to the period. Stepper motors like those within the K40 are speed controlled by the delay between ticks sent to the motor to step one. This tends to be used internally and you can use mm per second.


Coordinate System
---
The coordinate system is that the origin is in the upper left corners and all Y locations are DOWN. Which is to say higher Y values mean lower on the device. This is similar to all modern graphics system. Internally the commands are all relative with a positive magnitude.


Documentation
---
See Wiki for documentation of the LHYMICRO-GL format.

https://github.com/K40Nano/K40Nano/wiki
