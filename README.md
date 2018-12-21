# K40NanoDriver
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40NanoDriver is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it helpful and proper encapsolation and a functional low level API. Making this functionality more direct, understandable, and extendable.

Need
---

The goal of this project is to rectify that by providing properly encapsolated low level support from K40 Whisperer in order to better permit things like having a Command Line Interface, or letting people write their own GUI.

CLI
---

So far NanoController has move(x,y), load_egv(), home_position(), and a few other very basic commands. But, that's enough for a working CLI.

`python2 ./Nano.py -r -m 2000 2000 -e -i *.EGV -m 750 0 -p 5 -m -3750 750 -p 5 -e`

This calls Nano which is the CLI:
-r: goes to home position
-m 2000 2000: moves +2 inches +2 inches
-e: executes those commands requested thus far.
-i \*.EGV: inputs all the EGV files in the local directory (only test_engrave.EGV)
-m 750 0: moves +0.75 inches right.
-p 5: performs 5 passes of the current stack. Namely, the one loaded file, and the move command.
-m -3750 750: moves -3.75 inches left, and 0.75 inches down.
-p 5: performs 5 passes of the current stack. Namely, the 5x line, and the move to the next row.
-e: executes those commands requested thus far.


NanoController
---
The NanoController makes a connection, and relates the various calls to the output of the device. Currently this is move(dx,dy), load_egv(file), home_position(), unlock_rail(). More is planned for this, but this is enough to do most automations. The goal here is to allow the NanoController to control the K40 device work as a solid API for dealing with all interactions.

NanoConnection
---
We are connecting to a specific board on a K40 machine, and interacting across the USB cable. The connection class should wrap whatever packets it's given and process them in the correct manner. It shouldn't know anything about what's in the packets just divides them and does the interaction with the USB. It should internally deal with timeouts, crc error resends, and making and appending the CRC bytes to the packets. These interactions should not be known outside of the class.

NanoUsb
---
Encloses the USB classes, keep in mind this code is identical to K40 Whisperer and as such simply requires the same install and if K40 Whisperer works, this will also work.

MockUsb
---
Fake USB class for testing purposes.

NanoStream
---
Ties up the NanoConnection class in a python stream like class.

