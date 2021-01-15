# BCR2000-dev

Unofficial Behringer Development Kit - Custom firmware
------------------------------------------------------

Original web site : https://willem.engen.nl/projects/bc2000-dev/

This file should help you get going to developing your own software for the
Behring Control devices. While not everything is known about how the devices
work internally, it is currently possible to put something on the display,
blink the leds, read out keys and send midi by calling out to the bootloader.
But it is useful to tell a little bit about the bootloader first.

Oh, an important PRECAUTION first: make sure you have a way of sending and
receiving midi on your computer that doesn't depend on the Behringer Control
device. When you mess up with the firmware there is a rescue mode but that only
works with the physical midi input and ouput, not with its USB port. Also make
sure to have a .syx file containing the official firmware from Behringer for
your model.


## The boot sequence

At power up, the ARM processor starts executing instructions at address zero.
It then jumps to the pre-bootloader stage that sets up the DRAM timings so that
external memory can be used and subsequently copies the bootloader from flash
memory to DRAM. Then it jumps to the DRAM copy of the bootloader.

The bootloader initializes the timer, uart and probably more. Then it looks at
the operating system image in flash memory (which is encrypted with a
xor-cipher, more about that later) and verifies the length and checksum. If all
is well, the image is deobfuscated, copied to DRAM and executed. If there is a
problem with the operating system image, it goes into bootloader rescue mode
and waits for a new operating system image to be uploaded via midi.


## Interrupt handling

When an interrupt occurs, the processor jumps to address 0x18, which is in
flash memory. Depending on whether the operating system is loaded, it either
jumps to the bootloader's interrupt handler, or the one supplied by the
operating system. This is signified by the highest bit of the 16-bit register
PM0 at address 0x0600620. If this bit is cleared, the bootloader's IRQ handler
is used. This bit is set just before the bootloader hands over control to the
operating system.


## Calling bootloader functions

The bootloader contains code to put something on the display, send and receive
midi, and read out keys. Instead of first having create code that does these
things, one can also just call the bootloader's code. Since the bootloader does
most (all?) hardware interaction in its interrupt routine, the highest bit of
PM0 must be cleared to use its functionality.

The call address to turn a led on or off is 0x021813cd, and this routine
appears to expect the led number register r0 and the desired led status in r1
(the file firmware/shared/include/bootfun.h defines more subroutines). This
will be used in the following example.


## A basic example in assembly

To get an idea of what's needed to create your own firmware image, we'll go
through a basic example that turns on a led on the device. If you just want to
get started with one of the examples as soon as possible, you can safely skip
this for now and continue to the next section.

First get an ARM development toolchain. This project has an Ubuntu repository
containing the packages binutils-arm-eabi, gcc-arm-eabi and gdb-arm-eabi [1].
If you have another operating system, have a look at GNU ARM [2]. You really
need a unix-like environment, so if you're on Windows try Cygwin [3]. Together
with the development kit you're reading the documentation of that's all you
need to start developing.
This example assumes the Ubuntu packages, where all commands have the prefix
arm-eabi-. Please substitute the correct value for your ARM toolchain (GNU ARM
had the prefix arm-elf- last time I checked).

Create an assembly file, save it e.g. in test.S:

         @ let bootloader handle interrupts
         ldr   r0, =0x00600620
         ldr   r1, =0
         strh  r1, [r0]
         @ enable interrupts
         msr   CPSR_c, #0x53
         @ turn on exit led
         ldr   r5, =0x021813cd
         mov   r0, #0x9b
         mov   r1, #1
         mov   lr, pc
         blx   r5
         @ wait forever
         hang: b     hang

If this looks incomprehensible to you, don't worry. You can code C too, but
there's too much happening behind the scenes with that to be instructive.
You'll understand that the '@' symbol here signifies a comment. The first line
loads the address of PM0 (0x00600620) into register r0. Then the value 0 is
loaded into register r1, and the third instruction stores that number into PM0.
This will cause interrupts to be handled by the bootloader. The next
instruction enables interrupts by setting the program status register CPSR.

Then the address of the function that turns on leds is loaded into r5. The led
we want to turn on is the led of the exit button, which has number 0x9b, and
that is the first argument in r0. We want to turn it on, so r1 is set to one.
The next two instructions store the current program counter pc into lr, and
then branch (jump) to the led function (the instruction mov lr,pc shouldn't
actually be necessary, but somehow I couldn't get it to work without). Upon
return execution proceeds a branch to itself, so it hangs.

Now you can assemble ("compile") this file by the command:

        arm-eabi-as -o test.o test.S

which creates the object file test.o, which contains machine code and symbol
information. To extract the raw binary firmware image, this command is used

        arm-eabi-objcopy -O binary test.o test.bin

When test.bin is loaded into the device's memory at 0x02000000 and executed, it
would do just what we wanted. Now to get there, it must first be converted to a
series of midi messages that the device understands. That's were bcfwconvert.py
comes in that's provided in this package. Assuming you're in the directory
where that program is, you can run

       ./bcfwconvert.py -i test.bin -I os -o test.syx -O syx

and there's test.syx to be sent to the device. Then you can use bcfwflash.py to
upload the file to the device (though on Windows and Mac OS this probably
doesn't work and you'll need an external SysEx utility). It is strongly
recommended to use the external midi input/output on the Behringer Control
device, so that you can restore the original firmware back. The device's USB
connection doesn't work in rescue mode!  So if you dare proceed, you can flash
it using:

       ./bcfwflash.py -i test.syx

It is assumed that you have setup your device correctly so that you can
communicate between the device and your computer.

Now turn off the device, wait a couple of seconds (it takes some time before it
really turns off), and turn it back on. You should see the led of the exit
button turn on!


## The bootloader's rescue mode

When you want to upload new firmware to the device (or possibly the original
firmware in case you want to start actually using it again), you can always use
the bootloader's built-in rescue mode. Make sure the device is really off (if
you just turned it off, wait for some seconds to make sure it really is powered
down), keep down the buttons named "store" and "learn" and turn on the device.
The display will show "load" and you can send it new firmware via the midi
input connector (though not via USB). See also [4] for a description of the
bootloader mode.

Note that it is theoretically possible to overwrite the bootloader by sending a
series of firmware midi upload packets that programs the first 4k of flash.
This software should refuse to create a file that does so, but please be
careful when experimenting with custom addresses. In any case, the developers
can not be held responsible for bricked devices. That's the small risk in
playing with this.


## Supplied examples

Some example firmware codes in C can be found in the firmware/ directory,
including the beginnings of a code library for this device in firmware/shared.
The other subdirectories contain the files needed for each example, which is
usually a Makefile and one or more .c files. Just type 'make' to create the
.syx file, and 'make upload' to upload it to your device (on Linux; use a SysEx
utility on other systems).

hello:    simple (h)ello(-world) application
keycode:  display keycode of the last key pressed
ledcode:  turn on leds by their index
hello-os: hello-world application with existing os (see below)

The last example, hello-os, is a special one. It is built on top of the
official Behringer operating system image. Before running the normal operating
system, a custom function is called that shows a message on screen. After a
little delay then control is passed back to the original operating system and
the device continues as if nothing happened. Building this example requires an
official firmware .syx file to be present, which you can download from the
Behringer website (just type 'make' in that directory and it'll show where).
This makes it possible to use functions from the existing operating system
instead of the bootloader, such as USB, without having to code that all
ourselves. The only downside is less available memory and the longer time
needed to program the device.


## Coding in C

While assembly keeps one close to the hardware, it is a little cumbersome for
creating larger programs. And while you may not be fluent in assembly, chances
are that you've programmed C before. And that's where the development focus of
this package is.

The examples show well enough how to use C to program the device. As more
details of the hardware are discovered, the header files will expand and
functionality in firmware/shared/lib.c will be added.

One thing does not yet appear in the examples: the use of interrupts. By
default interrupts return immediately (unless they're diverted back to the
bootloader, see previous section on interrupts). When a function irq() is
defined though, that will be used instead (this is taken care of by the linker
script).


## Bring it on!

I hope you've enjoyed this rather long explanation. If something's unclear,
feel free to mail. And if you make something cool or useful, please think of
contributing it back so people can build on the shoulders of others, which
might possibly include you. Happy hacking.



[1] https://launchpad.net/~bc2000-dev/+archive/ppa

[2] http://www.gnuarm.com/

[3] http://www.cygwin.com/

[4] "B-Control MIDI Implementation", http://mntn-utils.110mb.com/

