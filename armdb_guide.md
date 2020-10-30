# armdb Guide
--------------------
A simple debugger interface for armsim. To run: `python armdb.py <program>.s` The high level operation is that a line of the assembly is printed out, then the user is prompted for a command (i.e. the line will not execute automatically), and then the command is executed. The supported commands can be read with the h command, here is a more detailed description of their semantics:
    p:
        The program code is scanned and the used registers are extracted. Each register in this list is printed on a single line with its value followed by another line with the Z and N flags
    q:
        Quits the debugger by breaking out of the main loop
    n:
        Executes the line displayed above the prompt, increments the program counter, resets xzr to zero, and prints monitored registers, if any
    mr <regs>:
        This command is to be followed by a list of registers to be monitored. Monitored registers are printed out after executing a line or reaching a breakpoint. Illegal registers are silently ignored if they are mixed in with legal registers. If only illegal registers are listed the user gets a message
    cmr <regs>:
        This command clears the listed monitored registers. Illegal registers are silently ignored. If no registers are listed, ALL monitored registers are cleared
    b <nums>:
        Adds breakpoints at the INSTRUCTIONS (not source line #'s) specified. Checks that the breakpoints are legal (in range). The user is informed of any illegal breakpoints
    rb <nums>
        Removes the specified breakpoints. If a nonexistent breakpoint is listed the user is informed. If no breakpoints are listed ALL of the breakpoints are removed
    c:
        Continues to the next breakpoint or to the end of the program. Executed lines and monitored registers are printed if a breakpoint is reached. If the end of the program is reached, monitored registers are printed
    ls:
        Lists the instructions with their INSTRUCTION NUMBER, NOT source line number, with an indicator showing the current instruction
    <enter>
        Pressing enter with no other input executes the last executed command. If there is no previous command the user is informed of this.
    h:
        Displays an abbreviated description of the commands
    
    
There is currently no restart capability; when the program ends, the debugger exits
