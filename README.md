# K40Nano
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40Nano is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it helpful and proper encapsolation and a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.


Goals
---
While the goal is to allow for more extensive CLI support that other can write, or allow people to cook up their own GUIs or use the GUIs already made elsewhere. The NanoController has support for move(x,y), load_egv(), home_position(), and a few other very basic commands. But, that's enough for a working CLI.


CLI
---
The included CLI (which is not intended to be exclusive or definitative, but go ahead and ask more to be built on it) is built on the concept of a stack. Namely you have a list of commands you can list them with (-l), you can load files with a wildcard "-i \*.EGV" and it should load those files. So for example, if you wanted to run a series of 25 jobs, with 30 seconds between each. You would call "Nano.py -m <x> <y> -e -i my_job.egv -w 30 -p 25 -e" which would add a rapid move to the stack, execute that, Add my_job.egv to the stack, add a wait 30 seconds to the stack then duplicate the stack 25 times, allowing you to perform an automated task (or burn the same thing 25 times, with a little bit of cool off time).

* -i [<input>]\*, loads egv files
* -p [n], sets the number of passes
* -m [dx] [dy], move command
* -w [seconds], wait_time
* -e, executes egv stack
* -l, lists egv stack
* -r, resets to home position
* -u, unlock rail
* -q, quiet mode
* -v, verbose mode
* -h, display this message


Example call:

`python2 ./Nano.py -r -m 2000 2000 -e -i *.EGV -m 750 0 -p 5 -m -3750 750 -p 5 -e`

This calls Nano which is the CLI:
* -r: goes to home position
* -m 2000 2000: moves +2 inches +2 inches
* -e: executes those commands requested thus far.
* -i \*.EGV: inputs all the EGV files in the local directory (only test_engrave.EGV)
* -m 750 0: moves +0.75 inches right.
* -p 5: performs 5 passes of the current stack. Namely, the one loaded file, and the move command.
* -m -3750 750: moves -3.75 inches left, and 0.75 inches down.
* -p 5: performs 5 passes of the current stack. Namely, the 5x line, and the move to the next row.
* -e: executes those commands requested thus far.


NanoController
---
The NanoController makes a connection, and builds and sends various compatable calls to the device. Currently this is move(dx,dy), load_egv(file), home_position(), unlock_rail(). More is planned for this, but this is already enough to do most automations. The goal here is to allow the NanoController to control the K40 device, and work as a solid API for dealing with all interactions made between code and machine.

NanoConnection
---
We are connecting to a specific board on a K40 machine, and interacting across the USB cable. The connection class wraps whatever packets it's given and process them in the correct manner. It shouldn't know anything about what's in the packets just packetizes them and does the interaction with the USB. It should internally deal with timeouts, crc error resends, and making and appending the CRC bytes to the packets, etc. These interactions should not need to be known outside of the class.

NanoUsb
---
Encloses the USB classes, keep in mind this code is identical to K40 Whisperer and as such simply requires the same install and if K40 Whisperer works, this will also work. If you are having trouble here, get K40 Whisperer to work and this should also work.


MockUsb
---
Fake USB class for testing purposes.


NanoStream
---
Encloses the NanoConnection class in a python file-like object, at least that's the idea. In theory this might be eventually get used by the NanoController class which would then simply write the data to the stream allowing the stream source to be switched and turning the controller into an egv exporter.


Units
---
The code throughout uses mils (1/1000th of an inch) so the units in the CLI are currently defaulted to mils. So 2000 is 2 inches. And while the CLI still uses this explicitly, it's mostly to use native units in the K40 device.


Coordinate System
---
Currently there's only move, but the coordinate system is that the origin is in the upper left corners and all Y locations are DOWN. Which is to say higher Y values mean lower on the device. This is similar to all modern graphics system, but seemingly different than K40 which strongly implies that all Y values are negative. Internally the commands are relative so this is a choice.
