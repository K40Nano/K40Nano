# K40Nano
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40Nano is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it a helpful and proper encapsolation and a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.

LHYMICRO-GL Format
---

A fully working version requires some mapping of the permitted states and the commands to get to those states, then the API should be crafted to approximate those states. There are primarily two different modes for the Nano board: default and compact (可压缩). These modes share some of the same commands and states, but work in some fundamentally different ways.

In default, we can set the speed, cut/raster step, laser operation, and direction flags. We cannot unset cut mode. That has to be cleared (unless there's an unknown command to turn it off). All the commands and states trigger at the block end usually an (N) command, and the final flags states is what is executed. The X magnitude and Y magnitude are independent of each other, and combine values, these can be a 3 digit number below 256, |, with z being a slightly special case of being +256 rather than +26 (a=1, b=2, etc). Note that the last flag gets the magnitude so "RzzzzL" in default mode assigns the 1024 mils of distance to the "L" command (Top / -Y direction). Setting the laser in default can leave the laser on without the head moving. Sending "IDS1P" will simply turn the laser on. Sending "IUS1P" will turn the laser off. The default state for the laser is off so "I@S1P" will also reset the states and turn the laser off, and clear the other states, like direction, speed, raster step. The commands in default are executed with N. It is best to execute anything remaining a command state before switching modes or doing something that might object be weird if some left over magnitude is somewhere. These also combine and trigger as a block, so RzzTzzN is a diagonal move. All moves in default-mode are performed at full speed.

Switching to compact mode uses S1E. Switching into and out of this mode will reset the laser position (it will always be turned off) and will always utilize the speed value, cut setting, and step values set with V and C/G. Within compact the permitted commands are D,U,L,R,T,B,M,F,@ anything else will likely cause the mode to stop and often can result in non-understood behaviors. When you exiting S1E we usually end with a mode exit command (F or @) will be relevant only after doing command "SE" in default mode the N command exits the mode and SE sends thing we wanted. If we ended with the F command, then the state will become locked until the commands finish and querying the device returns a TASK_COMPLETE signal. If we send a @ command then we are reset and must set the correct modes again. These changes only apply after calling SE. So usually we end a mode with @NSE or FNSE. Simply exiting compact mode requires an N command. This will allow you to change the value of G or V (step and velocity), but you cannot unset a C (cut-mode) which will override the G and change the behaviors. So it's if we are expecting to use a different speed, we should be sure to reset.

Within compact mode, every command is executed as soon as it's sent. So D turns the laser on. Rzz moves +Y zz (512 mils) immediately. To perform a diagonal the M command is added (in default_mode it does the same as no command, causing the momentum to be assigned to R (+Y) and executed). The diagonal M is the in the last x direction set and last y direction set. So "RRLTB" is LB and goes (+x,-y). It is very often customary to assign these values just before S1E. So usually we see NRBS1E this sets the inital states to RB. And is highly relevant with raster-step harmonic motions. We don't want our mode sets to affect the previous commands, and more pressingly the harmonic motion G triggers on sign change within compact mode. So it matters heavily for M within compact mode, and when G is set.

With G set. The G setting operates only within compact mode and triggers a step between 0-63 mills, set during default mode. It can be set again without harm. But, the C setting causes G to become void and I see no way to unset C without calling reset @. The G parameter takes effect when we switch directional modes. So if we're going B (+X) and and trigger an T command (-X). The step is triggered. If we gave a magnatude for this step, the distance applied to this step is performed diagonally like an M command with that particular distance. If we wish to just transition to the given step given in G to the Y direction we should always transition without a distance. Also during the steps the laser state is always set to off. So often the harmonic motion requires us to go B(somedistance)TD(somedistance)BD(somedistance)... this will cause us to go +X, then the transition to T will cause a step, moving us (let's say the Y direction is R(+Y) and step distance is 10 G010) +Y by 10, turining off the laser. Then we turn the laser back on and go the distance -Y back. Then the transition from T to B will move +Y by 10 again and turn the laser off, we turn it back on and go back. Causing us to have parallel horizontal lines 10 mils apart. The step is in the direction set, so if we do L or R commands to change the vertical we will invoke the step operations (moving in the X, and turning off the laser) if we change the Y-direction currently set. This means that we should have these correctly set before entering the S1E Compact mode as we cannot change them within Compact mode without invoking a step. If C is set, the value of G is ignored and the direction transition tend to click more on the device.

Calling "S1P" triggers instant execution ignores any commands that occur after that. So this is usually used for 1 off commands like move right "IR(distance)S1P" then the rest of commands in the packet don't matter unless 1 of them is another P. Whenever there are two P commands in the same packet the device resets. Unless flushed out with an 'I' command. IPP will reset, but PIP will not. As it only had one P command. If the P commands these are in different packets they won't behave this way. S2P works like S1P but unlocks the rail so it moves more freely.

* I: Deletes the buffer. Any commands currently in the stack are deleted. This includes all commands preceding the I within the same packet. This does not reset any modes. Turning the laser on with IDS1P then sending any additional I commands does not turn the laser off.
* R,L: +Y, -Y direction flags. Set the direction flags for execution of the directional magnitude.
* B,T: +X, -X direction flags. Set the direction flags for execution of the directional magnitude.
* M: In compact mode, performs a 45° move in the direction of the last set direction flags. (Does nothing in default, R (+Y) gets the magnitude, doing LdistanceTdistanceN in default will do a angle in that mode)
* D,U: Laser On and Laser Off. Can be done in default or compact. Leaving or entering compact mode turns the laser off. When a step is invoked within compact, the laser is also disabled.
* C,G: Cut, Raster_Step. Can be set in default mode (in any order at any point in default), by C overrides the G value and prevents any steps from happening.
* V: Speedcode. Differs a bit by controller board, making some EGV files generally less compatible with each other as they are board dependent.
* @: Resets modes. Set all the set modes to the default values. Behaves strangely in default mode. Usually this is invoked while in compact mode, calling @ which resets, then N which exits compact mode, then SE which sends the resets.
* F: Finishes. Behaves strangely in default. In compact, requires we exit (N) then call SE to take effect. Waits until task is complete then signals the TASK_COMPLETE flag.
* N: Executes in default mode, in compact mode, causes the mode to end. We can then issue rapid moves and return to compact mode with S1E. We could override the speed or G value, but cannot unset the C without a reset.
* S1E: Triggers Compact Mode.
* S1P: Executes command, ignores rest of packet. Locks rail.
* S2P: works like S1P but does not lock the rail.
* PP: If within the same packet, causes the device to rehome and all states are defaulted.
* S2E: Goes weird, but sometimes returns the device just to the left (might be rehomed device with an unlocked rail).

![nano-new](https://user-images.githubusercontent.com/3302478/50664116-de28be80-0f60-11e9-8e7d-ca4cf5c5f6ba.png)


API:
---

This is going to be fixed a bit soon, as I only recently figured out that you could fire the laser while stationary or do the various other commands in default. And better understood the boundaries between the states. A good API should reflect the device it's giving the interface for while fixing the routh edges.

While the rest reflects how it current works it's not the final form.

The NanoController class contains the relevant API for controlling the laser. Mostly it is called start() which provides an instance of a NanoTransaction which largely does turns the API calls into EGV data. Since a lot of the interfacing is guess work and incorrect sequences of commands can easily lead to undefined behavior. The NanoTransaction uses these specific states:

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
