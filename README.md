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



# Code Examples
While NanoConnection and NanoPlotter are primary here, I've also included a couple code examples that interact with the api.

These are likely to be all spun off into a different project that simply requires `K40Nano` as a requirement.

Parsers
---

There are two premade parser classes these take a filename or fileobject and a plotter. 

`parse_png` within the `PngParser` class parses a png file scanline by scanline and plots that information. It does this by reading the PNG directly, and making plotter calls while reading the file. There's very little memory footprint and even a tiny device can process a huge file without delay.

`parse_egv` within the `EgvParser` class reads the egv file and plots that data. The `NanoPlotter` would then turn these commands back into .egv data and send that to the laser. In the parser the .EGV files do not have any special priority. They are simply treated as containing vector data. This allows the `NanoPlotter` to optimize some things. If we wanted to just send the EGV data as is, we would use the a NanoConnection ourselves and feed the EGV data in, and then call `wait()` on the NanoConnection (with the assumption the EGV data has the F command in it already). 

Several other parsers could be added along these same lines. Load a file, interact with the API based on what the file says. But these should not be assumed to be a limit to the utility. If you wanted to, for example, rig up joystick to control the K40, you could do that with a few lines of code and the API, parsers are only a typical uses case example.

CLI (Command Line Interface)
---
I've provided a `Nano` CLI. This is not intended to be exclusive or definitive, but go ahead and ask more to be built on it (raise an issue). It is built on the concept of a stack. Namely you have a list of commands you can list them with (-l), you can load files with a wildcard "-i \*.EGV" and it should load those files.
 
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

Nano uses the PNG parser. Calling the input on a PNG file will perform the raster-engrave commands of the scanlines of the PNG file. As defined in that parser. 

The CLI will also accept units: in, mm, cm, ft. There cannot be a space between the number and the unit. `-m 2in 2in` or `-c 33mm 7mm` 

Usually this would be:
`python2 ./Nano.py <commands>`

Example #1:
If you wanted to run a series of 25 jobs, with 30 seconds between each.

Nano `-m 2in 2in -e -i my_job.egv -w 30 -p 25 -e`

* -m: Add a move to the stack
* -e: execute the stack (move command)
* -i my_job.egv: add my_job.egv to the stack
* -w: add a 30 second wait to the stack.
* -p 25: duplicate the stack (my_job.egv, wait) 25 times.
* (default -e) executes stack.

Example #2:
If you wanted to make 25 copies of a file in a 5x5 grid.

Nano `-r -m 2000 2000 -e -i *.EGV -m 750 0 -p 5 -m -3750 750 -p 5`

* -r: Adds a home position command to the stack.
* -m 2000 2000: moves +2 inches +2 inches
* -e: executes stack (home position, move command)
* -i adds each found file matching wildcard \*.EGV to the stack.
    * In my case this only matched test_engrave.EGV which was about 0.5 x 0.5 inches wide.
* -m 750 0: moves +0.75 inches right.
* -p 5: duplicate stack 5 times (files, move command)
* -m -3750 750: adds move -3.75 inches left, and 0.75 inches down to the stack.
* -p 5: duplicates stack 5 times. (files, move command, files, move command, files, move command, files, move command, files, move command, move to next row position)
* (default -e) executes stack.



# Documentation

Contributions to this project may require a certain amount of understanding of the formatting used. While the goal is to make that understanding not required for the programmer or end user. They should be able to simply add the module, import NanoPlotter and then send it a bunch of commands and have it just work. Contributing to the core of the project or fixing a bug or misunderstanding or improving it or porting it to another language, may require a much more in depth understanding, so I have documented the format to the best of my understanding. 


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
* M: In compact mode, performs a 45° move in the direction of the last set direction flags. (Does nothing in default, R (+Y) gets the magnitude, doing LdistanceTdistanceN in default will do an angle in that mode)
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

