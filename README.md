# K40Nano
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40Nano is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it helpful and proper encapsolation and a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.

API
---
The NanoController class contains the relevant API for controlling the laser. Mostly it is called start() which provides an instance of a NanoTransaction which largely does turns the API calls into EGV data. Since a lot of the interfacing is guess work and incorrect sequences of commands can easily lead to undefined behavior. The NanoTransaction uses these specific states:

![nano](https://user-images.githubusercontent.com/3302478/50603178-7abe6400-0e6e-11e9-9ef5-dee6d053a762.png)

The API transaction calls are:
* start()
    * Initializes the transaction.
* move(dx, dy, laser=False, slow=False, absolute=False):
    * Moves the device, either at full speed or slowed, with or without the laser on. At either relative or absolute positioning.
* set_speed(speed):
    * Sets the speed. This should accept either a speedcode or a feedrate (float).
* set_step(step):
    * Sets the raster-step. The Nano board can go right and left and step-y at the transitions.
* increase_speed(increase):
   * Set the speed relative to the previous speed.
* finish()
     * Finishes the transaction.

The additional commands in NanoController are:
* start():
* write(data):
* close(transaction=None):
* home():
* rail(lock=False):
* wait():
* finish():

The main function of the Transactions are to give you access to the only really important function, move() which controls the device. Some of the other functionalities are useful at points and thus are exposed.

An API should contain all relevant methods to interact with the laser, namely move to a place at a speed, with or without the laser. A few speciality commands like home and unlock rail are also needed. These should be devoid of the information about the state stored within the NanoController (or any controller) so you can perform a rapid move at anytime or a slow move at anytime or cut at any speed and then cut at a different speed while the controller seemlessly switches between the various modes.

This likely needs some more smoothing over and refining. But, it's getting pretty reasonable.

Other Transactions
---
There are several Transactions other than the NanoController's Transactions which properly takes the control the API commands and turns them into something other than EGV data. These are most for debugging purposes, but currently it can export a PNG file with PngTransaction, an SVG with SvgTransaction, and we can dump the EGV data by feeding the NanoController a FileWriteConnection rather than having it open a default NanoConnection.


Parsers
---
There are a few basic parser classes these take a filename or fileobject and a controller. `parse_png` within the `PngParser` class parses a Png file scanline by scanline and feeds that information into a Transaction, it does this directly via by reading the PNG directly, and iterating through the file and returning the relevant commands scanline by scanline, while it's busy reading it (to be nice to memory footprint)

`parse_egv` within the `EgvParser` class reads the egv file and turns sends commands to the API. The `NanoTransaction` would then turn these commands back into .egv data. This might seem a bit odd but, it allows all interations to deal with the API exclusively thereby allowing it to know the exact state of the machine at all times. And allows other parsed elements to work as first order objects. And allow various shortcuts and data consolidations to happen seemlessly. So additional vector classes are merely a parser away.

Several other parsers can be added along these same lines, basically anything that takes in vector-like data. The idea being simply accept a filename or fileobject then parse that applying the relevant core commands to the API and having it handled from there, and all properly encapsolated and isolated.

CLI
---
The included CLI, Nano, (which is not intended to be exclusive or definitative, but go ahead and ask more to be built on it) is built on the concept of a stack. Namely you have a list of commands you can list them with (-l), you can load files with a wildcard "-i \*.EGV" and it should load those files. So for example, if you wanted to run a series of 25 jobs, with 30 seconds between each. You would call "Nano.py -m <x> <y> -e -i my_job.egv -w 30 -p 25 -e" which would add a rapid move to the stack, execute that, add my_job.egv to the stack, add a wait 30 seconds to the stack then duplicate the stack 25 times, allowing you to perform an automated task (or burn the same thing 25 times, with a some amount of switching / cool off time).
* -i [\<input-\*\>]\*, loads egv/png files
* -o [<egv/png/svg>|"print"|"mock"]?, sets output method
* -p [n], sets the number of passes
* -m ([dx] [dy])+, relative move command
* -M ([x] [y])+, absolute move command
* -c ([dx] [dy])+, relative cut command
* -C ([x] [y])+, absolute cut command
* -s [+/-]?<speed> [step]*, sets the speed
* -w [seconds], wait_time
* -e, executes stack
* -l, lists stack
* -r, resets to home position
* -u, unlock rail
* -U, lock rail
* -v, verbose mode (default)
* -q, quiet mode
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
