# K40Nano
Decoupled and extended low level support for K40, derived from K40 Whisperer.

K40Nano is intended to pull out the low level support from K40Whisperer ( https://github.com/jkramarz/K40-Whisperer (not the author's github, there isn't an author's github)) and give it a helpful and proper encapsulation and a functional low level API. Making this functionality more direct, understandable, and extendable for everybody.

Project Status
---
Almost there. The API should be mostly stable, so how interactions are done should not change. There are likely a number of bugs still. And while some version of the code has been working here or there other errors may have cropped up. I'm hoping to test things and debug them in the next few days. Running the code with a mock output `-o mock` seems to produce quite reasonable egv data that a machine would have no trouble executing. Equally some commands like `Nano -o baby.svg -i baby.png` has no trouble converting a black and white image of a baby into an svg file of lines that looks like the given image.

Some other elements like the Parsers and CLI seem to generally work but might still need some tweaks and adjustments these are somewhat less important. These could be removed from the project. So could the additional debug connections (PrintConnection, and FileWriteConnection) and debug plotters (SvgPlotter, PngPlotter). The actual essential files are NanoUsb, NanoConnection, and NanoPlotter.

Compatibility
---
K40Nano should be compatible with both Python 2.7 and 3.6.


API:
---

The API is broken down into three main types, connections output streams. Connections, Plotters, and Parsers.

Connections are what we are connecting to and sending data to, Plotters is how tell the device to move and fire lasers beams, and Parser read a file and apply the instructions it contains to the Plotter.

Connections
---
The main one is NanoConnection which uses a usb connection to communicate with the K40. For testing purposes there is a MockUsb, but the main element is NanoUsb which does all the device specific connections etc. In addition to this there are a couple other connection classes `FileWriteConnection` and `PrintConnection` if these are assigned to a plotter then the plotter operations are sent to a file specified or to `print` accordingly.
Connections try to mimic a file-like object, and they have:

* send(data) - Sends data immediately.
* write(data) - Writes data to the buffer and sends as packets complete.
* flush() - Sends the buffer immediately.
* buffer(data) - Buffers the data, and makes no attempt to transmit it.
* open() - Opens the connection
* close() - Closes the connection
* wait() - Waits for the device to report itself done.

Plotters
---

The primary way to interact with with the API though is through the plotters. This is modelled after old pen plotters from which the `LHYMICRO-GL` encoding is derived. As such it is the best, simplest, and most natural way to interact with the K40.
 
Plotters have:
* open()
* close()
* move(dx, dy)
* down()
* up()

Effectively capturing almost everything a laser cutter can do. Like with Connectors there's couple helpful debugger plotters. These are `PngPlotter` and `SvgPlotter` which plots to a Png file and an Svg file respectively. 

The main plotter however is `NanoPlotter` and it has a few commands outside the scope of typical plotter. Mostly this is to control the compact mode within the language. These are:

* enter_compact_mode(speed, harmonic_step)
* exit_compact_mode_finish()
* exit_compact_mode_reset()
* exit_compact_mode_break()
* enter_concat_mode()

There are two modes, one for the device itself and a second because sometimes we don't know the correct state. There are three different methods to perform a move, all of these are supported. We can perform a rapid move. These are the positioning adjustments for the device. They consist of a single packet flagged with S1P at the end. These are fast and the initial state to use. Secondly we have compact mode. These are compacted instruction sets, at a particular speed. You enter_compact_mode() at a specific speed and the actions in compact_mode are done at that speed. This is for your typical vector-cuts or vector-engraves. Anything where you need to go slower to cut deeper.

The final mode is concat mode. If we didn't exit_compact_mode to a finished state, we cannot know whether or not device has finished. For technical reasons we can't start calling rapid moves as these trigger a "S1P" suffix which is not acceptable if we're currently cutting something. We can, however, concatenate these commands divided by N commands. These will be written to the buffer but may not be sent until the packet is full and sending prematurely may introduce undesirable command to the stack. So it will eventually perform that action, but we could not safely demand it happen instantly. If we exited compact with finish() though it would have returned to the default method of sending rapid-move packets.


In addition to those we have a couple helpful device specific commands:
* home()
* lock_rail()
* unlock_rail()

These cause the device to home, lock the rail, and unlock the rail. By default it will try to leave the compact mode if it has that option. But, this can be overwritten by sending abort=True. 


Also, keep in mind that the down() and up() commands are, in rapid-mode, rapid-commands. This will cause the K40 to turn on the laser and just sit there firing the laser. Generally we should enter_compact_mode() for most things we are doing. Usually this will be read a vector file of some type and write it to the laser, via the NanoPlotter's API.


Parsers
---
In a real sense the parsers are an end product rather than something that is properly an API but these are given as solid examples of how things should work.

There are a couple basic parser classes these take a filename or fileobject and a controller. `parse_png` within the `PngParser` class parses a png file scanline by scanline and feeds that information to the Plotter, it does this directly via by reading the PNG directly, and iterating through the file and returning the relevant commands as it reads the file. There's very little memory footprint and even a tiny device can write a massive file.

`parse_egv` within the `EgvParser` class reads the egv file and applies that to the Plotter. The `NanoPlotter` would then turn these commands back into .egv data and send it to the laser. Since the only way we interact is through the API, the .EGV files do not have any special priority. They are simply files containing vector data, and are treated as such. This is required because NanoPlotter needs to know the current state, so it cannot have something else altering that state without it knowing.

Several other parsers could be added along these same lines, basically anything that takes in vector-like data. The idea being simply accept a filename or fileobject then parse that applying the relevant commands to the API and having it the API handle it. It's all properly encapsulated and isolated.

CLI (Command Line Interface)
---
The API is nice, but we will likely just want the functionality. I've provided a Nano CLI. This is not intended to be exclusive or definitative, but go ahead and ask more to be built on it (raise an issue). It is built on the concept of a stack. Namely you have a list of commands you can list them with (-l), you can load files with a wildcard "-i \*.EGV" and it should load those files. So for example, if you wanted to run a series of 25 jobs, with 30 seconds between each. You would call "Nano.py -m <x> <y> -e -i my_job.egv -w 30 -p 25 -e" which would add a move to the stack, execute that, add my_job.egv to the stack, add a wait of 30 seconds to the stack then duplicate the stack 25 times, allowing you to perform an automated task (or burn the same thing 25 times, with a some amount of switching / cool off time).
 
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
* -i \test_engrave.EGV: inputs that file
* -m 750 0: moves +0.75 inches right.
* -p 5: performs 5 passes of the current stack. Namely, the one loaded file, and the move command.
* -m -3750 750: moves -3.75 inches left, and 0.75 inches down.
* -p 5: performs 5 passes of the current stack. Namely, the 5x line, and the move to the next row.
* -e: executes those commands requested thus far.

Calling the input on a PNG file will perform the raster-engrave commands of the scanlines of the PNG file. The program calls the PngParser.

The CLI will also accept some units like `-m 2in 2in` or `-c 33mm 7mm` (in, mm, cm, ft (there cannot be a space between the number and the unit))


NanoConnection
---
We are connecting to a specific board on a K40 machine, and interacting across the USB cable. The connection class wraps whatever data it's given and process that data. No class using NanoConnection needs to know anything more, it seamlessly packetizes the data them and does the interaction with the USB. It deals with timeouts, CRC error resends, and making and appending the CRC bytes to the packets, etc. These interactions should not need to be known outside of the class.

NanoUsb
---
Encloses the USB classes, keep in mind this code is identical to K40 Whisperer and as such simply requires the same install and if K40 Whisperer works, this will also work. If you are having trouble here, get K40 Whisperer to work and this should also work.


MockUsb
---
Fake USB class for testing purposes. If `pyusb` is not properly setup the NanoUsb should fail and replace with the MockUsb largely for testing purposes. It can also be specified in the the open of NanoConnection to use the MockUsb instead.


Units
---
The code throughout uses mils (1/1000th of an inch) so the units in the CLI are currently defaulted to mils. So 2000 is 2 inches. And while the CLI still uses this explicitly, it's mostly to use native units in the K40 device.


Coordinate System
---
The coordinate system is that the origin is in the upper left corners and all Y locations are DOWN. Which is to say higher Y values mean lower on the device. This is similar to all modern graphics system, but seemingly different than `K40 Whisperer` which seemed to strongly imply that all Y values are negative. Internally the commands are all relative with a positive magnitude so this is a choice.


Documentation
---

Contributions to this project may require a certain amount of understanding of the formatting used. While the goal is to make that understand not required for the end user. They should be able to simply add the module, import NanoPlotter and then send it a bunch of commands and have it just work. Contributing to the core of the project or fixing a bug or misunderstanding or improving it or porting it to another language, may require a much more in depth understanding, so I have documented the format to the best of my understanding. 


LHYMICRO-GL Format
---

A fully working version requires some mapping of the permitted states and the commands to get to those states, then the API should be crafted to approximate those states. There are primarily two different modes for the Nano board: default and compact (可压缩). These modes share some of the same commands and states, but work in some fundamentally different ways.

In default, we can set the speed, cut/raster step, laser operation, and direction flags. We cannot unset cut mode. That has to be cleared (unless there's an unknown command to turn it off). All the commands and states trigger at the block end usually an (N) command, and the final flags states is what is executed. The X magnitude and Y magnitude are independent of each other, and combine values, these can be a 3 digit number below 256, |, with z being a slightly special case of being +256 rather than +26 (a=1, b=2, etc). Note that the last flag gets the magnitude so "RzzzzL" in default mode assigns the 1024 mils of distance to the "L" command (Top / -Y direction). Setting the laser in default can leave the laser on without the head moving. Sending "IDS1P" will simply turn the laser on. Sending "IUS1P" will turn the laser off. The default state for the laser is off so "I@S1P" will also reset the states and turn the laser off, and clear the other states, like direction, speed, raster step. The commands in default are executed with N. It is best to execute anything remaining a command state before switching modes or doing something that might object be weird if some left over magnitude is somewhere. These also combine and trigger as a block, so RzzTzzN is a diagonal move. All moves in default-mode are performed at full speed.

Switching to compact mode uses S1E. Switching into and out of this mode will reset the laser position (it will always be turned off) and will always utilize the speed value, cut setting, and step values set with V and C/G. Within compact the permitted commands are D,U,L,R,T,B,M,F,@ anything else will likely cause the mode to stop and often can result in non-understood behaviors. When you exiting S1E we usually end with a mode exit command (F or @) will be relevant only after doing command "SE" in default mode the N command exits the mode and SE sends thing we wanted. If we ended with the F command, then the state will become locked until the commands finish and querying the device returns a TASK_COMPLETE signal. If we send a @ command then we are reset and must set the correct modes again. These changes only apply after calling SE. So usually we end a mode with @NSE or FNSE. Simply exiting compact mode requires an N command. This will allow you to change the value of G or V (step and velocity), but you cannot unset a C (cut-mode) which will override the G and change the behaviors. So it's if we are expecting to use a different speed, we should be sure to reset.

Within compact mode, every command is executed as soon as it's sent. So D turns the laser on. Rzz moves +Y zz (512 mils) immediately. To perform a diagonal the M command is added (in default_mode it does the same as no command, causing the momentum to be assigned to R (+Y) and executed). The diagonal M is the in the last x direction set and last y direction set. So "RRLTB" is LB and goes (+x,-y). It is very often customary to assign these values just before S1E. So usually we see NRBS1E this sets the initial states to RB. And is highly relevant with raster-step harmonic motions. We don't want our mode sets to affect the previous commands, and more pressingly the harmonic motion G triggers on sign change within compact mode. So it matters heavily for M within compact mode, and when G is set.

With G set. The G setting operates only within compact mode and triggers a step between 0-63 mills, set during default mode. It can be set again without harm. But, the C setting causes G to become void and I see no way to unset C without calling reset @. The G parameter takes effect when we switch directional modes. So if we're going B (+X) and and trigger an T command (-X). The step is triggered. If we gave a magnitude for this step, the distance applied to this step is performed diagonally like an M command with that particular distance. If we wish to just transition to the given step given in G to the Y direction we should always transition without a distance. Also during the steps the laser state is always set to off. So often the harmonic motion requires us to go B(somedistance)TD(somedistance)BD(somedistance)... this will cause us to go +X, then the transition to T will cause a step, moving us (let's say the Y direction is R(+Y) and step distance is 10 G010) +Y by 10, turning off the laser. Then we turn the laser back on and go the distance -Y back. Then the transition from T to B will move +Y by 10 again and turn the laser off, we turn it back on and go back. Causing us to have parallel horizontal lines 10 mils apart. The step is in the direction set, so if we do L or R commands to change the vertical we will invoke the step operations (moving in the X, and turning off the laser) if we change the Y-direction currently set. This means that we should have these correctly set before entering the S1E Compact mode as we cannot change them within Compact mode without invoking a step. If C is set, the value of G is ignored and the direction transition tend to click more on the device.

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

