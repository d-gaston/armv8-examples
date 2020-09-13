# ARMv8 Examples

+ The examples run on a Raspberry Pi 4 with Ubuntu 20.04.1 64 bit Server. Unfamiliar concepts are explained in source comments as they are introduced.
+ Examples include:
    + **hello.s** start here if you are completely new to ARM assembly and/or linux system calls
	+ **loop.s** same as hello.s, but prints a message mutliple times in order to demonstrate a basic looping construct
	+ **prompt.s** Asks the user for a name then prints out the name with a greeting. Introduces reading input from the command line

# To Compile
`$ as name.s -o name.o && ld name.o -o name`

where "name" is replaced with the example you want to run

# Examining with gdb
It's highly encouraged to step through the programs with a debugger to see what's actually going on. To do this run
`$ gdb name`

Here are some commands you'll want to know:
+ **start** starts the program
+ **layout asm** brings up a TUI environment so you can see what assembly instructions are being executed
+ **stepi** steps one assembly instruction
+ **i r** prints out the contents of the registers
+ **x addr** prints out the contents of the given address
+ **x/s addr** prints out the contents of the given address as a string
+ **q** quit

Pressing enter at a blank prompt causes the previously executed command to run again. This can save a lot of typing.
