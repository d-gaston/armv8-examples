# armsim Guide
--------------------
The goal of this program is to simulate an arm64 processor executing a compiled .s file. It attempts to be compatible with the format of gnu assembler files and supports a subset of the instructions and directives. The basic operation of the simulator is that it first reads in a .s file line by line and separates the input into code and symbol declarations.The data in static memory is simulated with a python list, where each element represents one byte as an int. It attempts to execute each line of code by matching against regular expressions that encode the instruction format, and updating global variables appropriately based on that execution. All text is converted to lower case, meaning that identifiers are not case sensitive (so variable = VARIABLE).
Run a program with `python armsim.py <program>.s`
## Currently supported:
### System Calls:
    read       0x3f  (63) --stdin only
    write      0x40  (64) --stdout only
    brk        0xd6  (214)
    getrandom  0x116 (278)
    exit       0x5d  (93)
### Labels:
Can start with zero or more periods followed by any number of numbers, letters, or underscores (regex: [.]*[a-z0-9_]+). The same label cannot be declared twice. Since text is converted to lowercase, LABEL: and label: would count as the same. Labels must be declared on their ***OWN*** line.
### Directives:
Directives are information for an assembler. These aren't needed for writing simple programs to test out instructions
* .data    (declare a region of initialized data)
    * .asciz   (declare a string in the .data section)
    * .8byte   (declare an array of 8 bytes words in the .data section)
    * =        (assignment of a variable to a constant value within the .data section)
    * = . -      (find the length of the previously declared item within the .data section)
* .bss     (declare a region of uninitialized data)
    * .space   (declare an empty buffer in the .bss section)
### Registers
Registers x0-28 can be used. The special registers fp, lr, sp, and xzr must be explicitly named (i.e. you can't use x30 as an alias for lr, you must use lr)
### Instructions:
These are the current supported instructions. The instruction formats comes from the official ARM documentation \
**{s} means that 's' can be optionally added to the end of an instruction to make the result affect the flags** \
*rd     = destination register* \
*rt/rt2 = target register* \
*rn     = first register operand* \
*rm     = second register operand* \
*imm    = immediate value (aka a number)* 
   
    ldp     rt, rt2, [rn]
    ldp     rt, rt2, [rn, imm]
    ldp     rt, rt2, [rn, imm]! //pre index
    ldp     rt, rt2, [rn], imm  //post index
    stp     rt, rt2, [rn]
    stp     rt, rt2, [rn, imm]
    stp     rt, rt2, [rn, imm]! //pre index
    stp     rt, rt2, [rn], imm  //post index
    ldr     rd, =<var>
    ldr     rt, [rn]
    ldr     rt, [rn, imm]
    ldr     rt, [rn, rm]
    ldr     rt, [rn, imm]! //pre index
    ldr     rt, [rn], imm  //post index
    str     rt, [rn]
    str     rt, [rn, imm]
    str     rt, [rn, rm]
    str     rt, [rn, imm]! //pre index
    str     rt, [rn], imm  //post index
    mov     rd, imm
    mov     rd, rn
    sub{s}  rd, rn, imm
    sub{s}  rd, rn, rm
    add{s}  rd, rn, imm
    add{s}  rd, rn, rm
    asr     rd, rn, imm
    lsl     rd, rn, imm
    udiv    rd, rn, rm
    sdiv    rd, rn, rm
    mul     rd, rn, rm
    msub    rd, rn, rm, ra
    madd    rd, rn, rm, ra
    and{s}  rd, rn, imm
    and{s}  rd, rn, rm
    orr{s}  rd, rn, imm
    orr{s}  rd, rn, rm
    eor{s}  rd, rn, imm
    cmp     rn, rm
    cbnz    rn, <label>
    cbz     rn, <label>
    b       <label>
    b.gt    <label>
    b.ge    <label>
    b.lt    <label>
    b.le    <label>
    b.eq    <label>
    b.ne    <label>
    b.mi    <label>
    b.pl    <label>
    bl      <label>
    ret
    svc 0        

    

-----
##  Debugger
The debugger has been moved to a standalone program called armdb. See [the guide](armdb_guide.md) for usage instructions
-----
## REPL
There is a simple repl interface available for armsim that can be used to test out individual instructions or sequence of instructions. Currently it does not allow you to use any memory accessing instructions (such as ldr or str) but all instructions that only affect registers should work. Launch the repl by running `python armsim.py` with no files listed 
-----
## armsim As a Library
armsim can be imported into another python program to be configured and executed programmatically (for use in an autograder, for example). See [this](armsim_lib.md) document for instructions on how to do so.
