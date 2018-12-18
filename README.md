# K40NanoDriver
Decoupled and extended low level support for K40, derived from K40 Whisperer.

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

