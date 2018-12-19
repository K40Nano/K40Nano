# K40NanoDriver
Decoupled and extended low level support for K40, derived from K40 Whisperer.

*This almost certainly doesn't work yet, and absolutely certainly hasn't been tested. It's logical inference from modifications and extractions of the original code*

K40NanoDriver is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it helpful and proper encapsolation and a functional low level API.

Need
---

K40 Whisperer performs everything from low level stuff like connecting to the USB and encoding the data sent along the cable to high level stuff like parsing SVG and reading GCode, scanlining images, having a fully fleshed out GUI, all without any intermediate modules.

The goal of this project is to rectify that by providing properly encapsolated low level support from K40 Whisperer in order to better permit things like having a Command Line Interface, or letting people write their own GUI.

As well as allowing us to overcome some short falls of K40 Whisperer.

NanoStream
---
We are connecting to a specific controller on a K40 machine, and interacting across the USB cable. The steam class should simply work like a proper python stream. If you send it data it pass that along to the K40 without any regard of what that information means. It should internally deal with timeouts, crc error resends, and making and appending the CRC bytes to the packets. These interactions should not be known outside of the class.

This should be the lowest level, without any information at all as to how to control the K40 or what's in the packets it is sending. It should simply behind the scenes packetize and error check the stream to the device.

Many elements of the K40 Whisperer class properly equate to a stream like this. When you open the stream it initializes the device, when you flush() the blocking stream it wait_for_laser_to_finish, when you close() it disconnects from the device, and when you write() to the stream it packetizes that data, adds in error control bytes, resends the packets that didn't send etc. So anything using NanoStream doesn't see anything about those aspects.

Stream controls like this also will allow things like a K40 GUI to write the data as it creates that data. So there's no need to preprocess all the data before hand. Since the stream is blocking you can simply run it in real time and have the GUI update itself and deal with user interruptions itself because the stream has sent the stuff it's sent so far and doesn't have a giant block of memory of things it has yet to send. 

NanoController
---
The NanoController takes a stream (very likly going to be a NanoStream, but it doesn't have to be), and writes the Nano Commands to that based on the particularly requested state change to the laser cutter. This is where all the low level commands from K40 Whisperer should end up. So that you can interact with the device without knowing what the interchange language is or how it works.

* Unlock_rail
* e_stop: I don't know what this is.
* home_position
* rapid_move(x,y)
* move(direction, distance, laser on, dirs)
* flush

* make_distance
* make_dir_dist
* make_cut_line
* make_move_data
* rapid_move_slow
* rapid_move_fast
* change_speed

The change speed had some board specific elements so those are pushed into actual classes for the boards. So rather than setting a name and checking everything each time, it simply can be set to a different board which simply changes the calculations there.

NanoUtilities
---
This is largely the make_egv_data functions. This is rather critical functionality for K40 Whisperer, but is tied in with the NanoController really tightly and uses a bunch of raw_writes with unknown meaning rather than be able to delegate to the controller for everything (as one should properly do).

Also, with the code fixes letting the code work as actual stream, it's not really critical to make all the data before sending it. Those can be done at the same time. And do that rather natively.
