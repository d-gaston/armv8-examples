import armsim
from itertools import chain
import sys,re

'''
###################################################################
#                              armdb                              #
###################################################################
A simple debugger interface for armsim. The high level operation is
that a line of the assembly is printed out, then the user is prompted
for a command (i.e. the line will not execute automatically), and then 
the command is executed. The supported commands can be read with the h 
command, here is a more detailed description of their semantics:

p:
    The program code is scanned and the used registers are extracted
    Each register in this list is printed on a single line with its value
    followed by another line with the Z and N flags
heap:
    Prints out all elements of the heap contained from the beginning of the heap
    to the program break (set with the brk system call). Info stored outside
    of this is not displayed, even if it is technically on the heap
stk <num>:
    Prints out the <num> top elements of the stack. If no number is specified, the default number of 
    elements to print out is 10
d  <vars>:
    Display the memory contents pointed at by the variable. Output depends
    on the directive the variable was declared with:
    asciz : list of chars
    8byte : list of 8 byte integers
    space : list of bytes
    =     : integer value of variable
n:
    Executes the line displayed above the prompt, increments the program
    counter, resets xzr to zero, and prints monitored registers, if any
mr <regs>:
    This command is to be followed by a list of registers to be monitored.
    Monitored registers are printed out after executing a line or reaching
    a breakpoint. Illegal registers are silently ignored if they are mixed 
    in with legal registers. If only illegal registers are listed the user 
    gets a message
cmr <regs>:
    This command clears the listed monitored registers. Illegal registers 
    are silently ignored. If no registers are listed, ALL monitored
    registers are cleared
b <nums>:
    Adds breakpoints at the INSTRUCTIONS (not source line #'s) specified
    Checks that the breakpoints are legal (in range, not labels). The 
    user is informed of any illegal breakpoints
rb <nums>
    Removes the specified breakpoints. If a nonexistent breakpoint is
    listed the user is informed. If no breakpoints are listed ALL of
    the breakpoints are removed
c:
    Continues to the next breakpoint or to the end of the program.
    Executed lines and monitored registers are printed if a breakpoint
    is reached. If the end of the program is reached, monitored registers
    are printed
ls:
    Lists the instructions with their INSTRUCTION NUMBER, NOT source
    line number, with an indicator showing the current instruction
lhc:
    Lists the L_abel H_it C_ounts for each label in the program, displayed
    in sorted order
<enter>
    Pressing enter with no other input executes the last executed 
    command. If there is no previous command the user is informed of this
h:
    Displays an abbreviated description of the commands
q:
    Quits the debugger by breaking out of the main loop    
    
There is currently no restart capability; when the program ends, the 
debugger exits

'''

help_str = "simple debugger interface for armsim. commands are\n"\
+"  p            print all registers used in program and flags\n"\
+"  heap         print the heap from the beginning to the break\n"\
+"  stk <num>    print the n top elements of the stack\n"\
+"  stk          print the 10 top elements of the stack\n"\
+"  d <vars>     display the memory held at each <var> as bytes\n"\
+"  n            next instruction\n"\
+"  mr  <regs>   monitored register(s) will print after each line\n"\
+"  cmr <regs>   clear specified register(s) from monitor list\n"\
+"  cmr          clear entire monitor list\n"\
+"  b  <nums>    breakpoint at line number(s)\n"\
+"  rb <nums>    remove breakpoint at line number(s)\n"\
+"  rb           remove all breakpoints\n"\
+"  c            continue to next breakpoint or end of program\n"\
+"  ls           list program with instruction numbers\n"\
+"  lhc          print the current label hit counts\n"\
+"  <enter>      execute previous command\n"\
+"  h            help\n"\
+"  q            quit\n"
'''
procedure to print a list of separated registers on a single line,
followed by a newline after the last one. Used to print used registers
with the p command or monitored registers.
'''
def print_regs(reg_list):
    for r in reg_list:
        print("{}: {}".format(r, armsim.reg[r]), end=' | ')
    if(reg_list):
        print()
        
def main():
    with open(sys.argv[1],'r') as f:
        armsim.parse(f.readlines())
    armsim.check_static_rules()
    
    #Aliases for armsim fields (reduce using armsim. everywhere)
    reg = armsim.reg
    asm = armsim.asm
    mem = armsim.mem
    lab = armsim.label_regex
    rg = armsim.register_regex
    var = armsim.var_regex
    cmd = ''
    prevcmd = ' '
    breakpoints = set()
    #flag to use so that program can continue from a breakpoint
    came_from_bp = False
    monitors = set()
    used_regs = list(set(chain(*[re.findall(rg,instr) for instr in asm])))
    #sorting isn't perfect, since x10 will come after x1, but it's better
    #than having a random order
    used_regs.sort()
    
    labels = [l for l in asm if(re.match('{}:'.format(lab),l))]
    armsim.label_hit_counts = dict(zip(labels, [0]*len(labels)))
    
    line = asm[armsim.pc]
    #print first line
    #if a label in encountered, inc armsim.pc and skip
    if(re.match(lab+':',line)):
        print("<label {}>".format(line));armsim.pc+=1
        armsim.label_hit_counts[line] += 1
    else:
        print("\t"+line)    
       
    while(True):
        if(armsim.pc >= len(asm)): print('reached end of program. exiting...');break  
        #if a label in encountered, inc armsim.pc and skip
        if(re.match(lab+':',line)):
            armsim.pc+=1;line = asm[armsim.pc];continue 
        cmd = input('(armdb) ').lower().strip()
        if(not cmd and prevcmd):
            cmd = prevcmd
            
        #command switch statement
        if(cmd == 'p'):
            print_regs(used_regs)    
            print("Z: {} N: {}".format(armsim.z_flag,armsim.n_flag))
        elif(cmd.startswith('stk')):
            numList = re.findall('[0-9]+',cmd)
            print("SP: {}".format(hex((reg['sp']))))
            #print provided number of items
            if(numList):
                #should only be 1 element in numList
                num = int(numList[0])
                #stack elements are stored as a list of bytes
                for i in range(0, num*8,8):
                    #remember stack goes down, so move up
                    addr = reg['sp']+i
                    #convert list of 8 bytes to value
                    value = int.from_bytes(bytes(mem[addr:addr+8]),'little')
                    print("<sp+{}>  {}".format(i,hex(value)))
            #print top 10
            else:
                for i in range(0,80,8):
                    addr = reg['sp']+i
                    value = int.from_bytes(bytes(mem[addr:addr+8]),'little')
                    print("<sp+{}>  {}".format(i,hex(value)))
        elif(cmd == 'heap'):
            offset = armsim.brk
            for addr in range(armsim.data_pointer,armsim.brk,8):
                value = int.from_bytes(bytes(mem[addr:addr+8]),'little')
                print("<brk-{}>  {}".format(offset,hex(value)))
                offset -= 8
        elif(cmd.startswith('d ')):
            variables = set(re.findall(var,cmd.replace('d ', '')))
            if(variables):
                for v in variables:
                    print(str(armsim.getdata(v)).replace('[','').replace(']',''))
            else:
                print("no labels specified")
        elif(cmd == 'n'):
            armsim.execute(line)
            armsim.pc+=1
            reg['xzr'] = 0
            #if program has ended we can print monitors and msg
            if(armsim.pc >= len(asm)):
                print_regs(monitors)
                print('reached end of program. exiting...');break 
            line = asm[armsim.pc]
            #print next line
            print("\t"+line)
            print_regs(monitors)
        elif(cmd.startswith('mr')):
            registers = set(re.findall(rg,cmd))
            if(not registers):print("no registers listed")
            monitors = monitors.union(registers)
        elif(cmd.startswith('cmr')):
            registers = set(re.findall(rg,cmd))
            if(registers):
                monitors = monitors.difference()
            else:
                monitors.clear
        elif(cmd.startswith('b ')):
            bps = set(re.findall('[0-9]+',cmd))
            for bp in bps: 
                if(int(bp) not in range(0,len(asm))):
                    print("breakpoint {} out of range".format(bp))
                elif(re.match(lab+':',asm[int(bp)])):
                        print("cannot use label as breakpoint")    
                else:
                    breakpoints.add(int(bp))
            if(not bps):print("no breakpoints listed")

        elif(cmd.startswith('rb')):
            bps = set(re.findall('[0-9]+',cmd))
            for bp in bps: 
                if(int(bp) not in breakpoints):
                    print("breakpoint {} does not exist".format(bp))
                else:
                    print("breakpoint {} removed".format(bp))
                    breakpoints.remove(int(bp))
            if(not bps):breakpoints.clear();print("all breakpoints cleared")
        #Should continue until breakpoint but not execute it
        elif(cmd == 'c'):
                while(armsim.pc < len(asm)):
                    #if a label in encountered, inc armsim.pc and skip
                    line = asm[armsim.pc]
                    if(re.match(lab+':',line)):
                        armsim.label_hit_counts[line] += 1
                        armsim.pc+=1;continue
                    #without the came_from_bp flag, the c command will
                    #keep breaking at the same breakpoint
                    if(armsim.pc in breakpoints and not came_from_bp): 
                        print("break at {}: {}".format(armsim.pc,line))
                        print_regs(monitors)
                        came_from_bp = True
                        break
                    armsim.execute(line)
                    armsim.pc+=1
                    came_from_bp = False
                    reg['xzr'] = 0
                #if program has ended we can print monitors and msg
                if(armsim.pc >= len(asm)):
                    print_regs(monitors) 
                    print('reached end of program. exiting...');break
        elif(cmd == 'ls'):
            for i in range(0,len(asm)):
                if(i==armsim.pc):
                    #print arrow on current line
                    print("->{}: {}".format(i,asm[i]))
                else:
                    print("  {}: {}".format(i,asm[i]))
        elif(cmd == 'lhc'):
            for label in sorted(armsim.label_hit_counts):
                print("{} : {}".format(label,armsim.label_hit_counts[label]), end = ' | ')
            print()
        elif(cmd == 'h'):
            print(help_str)
        elif(cmd == 'q'):break
        else:
            if(cmd == ' '):
                print("no previous command to execute")
            else:
                print("{}: no such command or syntax error".format(cmd))
        prevcmd = cmd

if __name__ == "__main__":
    main()
