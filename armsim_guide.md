# armsim Guide
--------------------
The goal of this program is to simulate an arm64 processor executing a compiled .s file. It attempts to be compatible with the format of gnu assembler files and supports a subset of the instructions and directives. The basic operation of the simulator is that it first reads in a .s file line by line and separates the input into code and symbol declarations.The data in static memory is simulated with a python list, where each element represents one byte as an int. It attempts to execute each line of code by matching against regular expressions that encode the instruction format, and updating global variables appropriately based on that execution. All text is converted to lower case, meaning that indentifiers are not case sensitive (so variable = VARIABLE).
Run a program with `python armsim.py <program>.s`
## Currently supported:
### System Calls:
    read       0x3f  (63) --stdin only
    write      0x40  (64) --stdout only
    getrandom  0x116 (278)
### Labels:
Can be any text (current no numbers) prepended with any number of periods or underscores and should end in a colon. The same label cannot be declared twice. Since text is converted to lowercase, LABEL: and label: would count as the same. Labels must be declared on their ***OWN*** line.
### Directives:
Directives are information for an assembler. These aren't needed for writing simple programs to test out instructions
* .data    (declare a region of initialized data)
    * .asciz   (declare a string in the .data section)
    * . -      (find the length of the previously declared item within the .data section)
    * =        (assignment of a variable to a constant value within the .data section)
* .bss     (declare a region of unitialized data)
    * .space   (declare an empty buffer in the .bss section)
### Instructions:
**{s} means that 's' can be optionally added to the end of an instruction to make the result affect the flags**
*rd = destination register*
*rn = first register operand*
*rm = second register operand*
*imm = immediate value (aka a number)*
   
    ldr     rd,=<var>
    ldr     rd,[rn]
    mov     rd,imm
    mov     rd,rn
    sub{s}  rd, rn, imm
    sub{s}  rd, rn, rm
    add{s}  rd, rn, imm
    add{s}  rd, rn, rm
    udiv    rd, rn, rm
    msub    rd, rn, rm, ra
    and     rd, rn, imm
    cmp     rn, rm
    cbnz    rn, <label>
    cbz     rn, <label>
    b       <label>
    b.gt    <label>
    b.lt    <label>
    svc 0   

    
### Comments 
(Must NOT be on same line as stuff you want read into the program):

    //text
    /*text*/
    /*
    text
    */
-----
##  Debugger
Run the program in debug mode by including the --debug flag: `python armsim.py <program>.s --debug` or`python armsim.py --debug <program>.s ` 
Current commands are: 

    p flags      print flags
    p x1 x2..xn  print all registers listed
    q            quit
    n            next instruction
    ls           list program with line numbers
    b  <num>     breakpoint at line number
    rb <num      remove breakpoint at line number
    c            continue to next breakpoint
    <enter>      repeat previous command
    h            help (display this message)
-----
## REPL
There is a simple repl interface available for armsim that can be used to test out individual instructions or sequence of instructions. Currently it does not allow you to use any memory accessing instructions (such as ldr or str) but all instructions that only affect registers should work. Launch the repl by running `python armsim.py` with no files listed 