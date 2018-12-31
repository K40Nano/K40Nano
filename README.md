# K40Nano
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40Nano is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it helpful and proper encapsolation and a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.


* Not fully tested. Recent upgrade and early version of the fully API'd version, not yet fully tested.

API
---
The Controller.py class contains the relevant API for controlling the laser. The NanoController has the NanoConnection and various relevant .EGV writing information.

The core commands are:
* move(dx, dy, slow=False, laser=False):
    * Moves to new relative location either at the set speed or rapidly with or without the laser engaged.
* move_abs(x, y, slow=False, laser=False):
    * Moves to new absolute location either at the set speed or rapidly with or without the laser engaged.
* set_speed(speed=None, raster_step=None):
    * Sets the speed
* home():
    * Homes the device.
* rail(lock=False):
    * Locks or unlikes the rail
* wait():
    * Waits until all operations are done.
* halt():
    * Aborts current operations.
* release():
    * terminates the controller.
    
The API should contain all relevant methods to interact with the laser, namely move to a place at a speed, with or without the laser. A few speciality commands like home and unlock rail are also needed. These should be devoid of the information about the state stored within the NanoController (or any controller) so you can perform a rapid move at anytime or a slow move at anytime or cut at any speed and then cut at a different speed while the controller seemlessly switches between the various modes.

    controller = NanoController()
    controller.home() # resets the machine to home.
    controller.move(500, 500) # moves head down and right by 0.5 inches.
    controller.move(100,100,True,True) # performs a diagonal 0.1 inches cut with the laser.
    controller.release()

And that should work for basically everything. It should give a proper programatic interface for the laser interactions.

Controllers
---

There are several controllers other than the NanoController which properly takes the control commands and turns them into EGV commands. Mostly these are for debugging purposes, but currently we can export a PNG file with PngController, an SVG with SvgController, and we can dump the EGV data by feeding the NanoController a FileWriteConnection rather than having it open a default NanoConnection.


Parsers
---
There are a few basic parser classes these take a filename or fileobject and a controller. `parse_png` within the `PngParser` class parses a Png file scanline by scanline and feeds that information into the controller, it does this directly via by reading the PNG directly, and iterating through the file and returning the relevant commands scanline by scanline.

`parse_egv` within the `EgvParser` class reads the egv file and turns the EGV file into controller commands sent to the API. The `NanoController` would then turns these commands back into .egv data. This might seem a bit odd but, it allows all interations to deal with the API exclusively thereby allowing it to know the exact state of the machine at all times. And allows other parsed elements to work as first order objects.

Several other parsers can be added along these same lines, basically anything that takes in vector-like data. The idea being simply accept a filename or fileobject then parse that applying the relevant core commands to the API and having it handled from there, and all properly encapsolated and isolated.

CLI
---
* Latest version doesn't have the CLI fully tested. It's a pretty major revision.
* The input png files don't have a speed commands yet.

The included CLI, Nano, (which is not intended to be exclusive or definitative, but go ahead and ask more to be built on it) is built on the concept of a stack. Namely you have a list of commands you can list them with (-l), you can load files with a wildcard "-i \*.EGV" and it should load those files. So for example, if you wanted to run a series of 25 jobs, with 30 seconds between each. You would call "Nano.py -m <x> <y> -e -i my_job.egv -w 30 -p 25 -e" which would add a rapid move to the stack, execute that, add my_job.egv to the stack, add a wait 30 seconds to the stack then duplicate the stack 25 times, allowing you to perform an automated task (or burn the same thing 25 times, with a little bit of cool off time).

* -i [\<file-name-\*\>]\*, loads egv/png files
* -o [\<file-name-\*\>]\*, export file type
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

Calling the input on a PNG file will perform the raster-engrave commands of the scanlines of the PNG file. The program calls the PngParser which parses the scanlines line-by-line and converts the scanlines into controller commands. 

NanoController
---
The NanoController makes a connection, and builds and sends various compatable calls to the device. It complies with the API interfacing and doesn't include any additional add commands as such.

NanoConnection
---
We are connecting to a specific board on a K40 machine, and interacting across the USB cable. The connection class wraps whatever packets it's given and process them in the correct manner. It shouldn't know anything about what's in the packets just packetizes them and does the interaction with the USB. It should internally deal with timeouts, CRC error resends, and making and appending the CRC bytes to the packets, etc. These interactions should not need to be known outside of the class.

NanoUsb
---
Encloses the USB classes, keep in mind this code is identical to K40 Whisperer and as such simply requires the same install and if K40 Whisperer works, this will also work. If you are having trouble here, get K40 Whisperer to work and this should also work.


MockUsb
---
Fake USB class for testing purposes. If `pyusb` is not properly setup the NanoUsb should fail and replace with the MockUsb largely for testing purposes.


Units
---
The code throughout uses mils (1/1000th of an inch) so the units in the CLI are currently defaulted to mils. So 2000 is 2 inches. And while the CLI still uses this explicitly, it's mostly to use native units in the K40 device.


Coordinate System
---
The coordinate system is that the origin is in the upper left corners and all Y locations are DOWN. Which is to say higher Y values mean lower on the device. This is similar to all modern graphics system, but seemingly different than `K40 Whisperer` which strongly implies that all Y values are negative. Internally the commands are all relative with a positive magnatude so this is a choice.
