import re
import sys
import os

'''
*******************
* ArmSim Overview *
*******************
The goal of this program is to simulate an arm64 processor
executing a compiled .s file. It attempts to be compatible
with the format of gnu assembler files and supports a subset
of the instructions and directives. The basic operation of
the simulator is that it first reads in a .s file line by 
line and separates the input into code and symbol declarations. 
The data in static memory is simulated with a python list, where
each element represents one byte as an int. It attempts to execute 
each line of code by matching against regular expressions that encode 
the instruction format, and updating global variables appropriately 
based on that execution. All text is converted to lower case, 
meaning that identifiers are not case sensitive 
(so variable = VARIABLE).
Currently supported:
  System Calls:
    read      0x3f  (63) --stdin only
    write     0x40  (64) --stdout only
    getrandom 0x116 (278)
  Labels:
    Can be any text (current no numbers) prepended with
    any number of periods or underscores and should end in 
    a colon. The same label cannot be declared twice. Since 
    text is converted to lowercase, LABEL: and label: would 
    count as the same. Labels must be declared on their OWN 
    line.
  Directives:
    .data    (declare a region of initialized data)
        .asciz   (declare a string in the .data section)
        . -      (find the length of the previously declared item within the .data section)
        =        (assignment of a variable to a constant value within the .data section)
    .bss     (declare a region of unitialized data)
        .space   (declare an empty buffer in the .bss section)

  Instructions:
    **{s} means that 's' can be optionally added to the end of an
    instruction to make the result affect the flags**
    rd = destination register
    rn = first register operand
    rm = second register operand
    imm = immediate value (aka a number)
    ldp     rt, rt2, [rn]
    ldp     rt, rt2, [rn, imm]
    ldp     rt, rt2, [rn, imm]! //pre index
    ldp     rt, rt2, [rn], imm  //post index
    stp     rt, rt2, [rn]
    stp     rt, rt2, [rn, imm]
    stp     rt, rt2, [rn, imm]! //pre index
    stp     rt, rt2, [rn], imm  //post index
    ldr     rd, =<var>
    ldr     rd, [rn]
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
    lsr     rd, rn, imm
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

    
Comments (Must NOT be on same line as stuff you want read into the program):
  //text
  /*text*/
  /*
  text
  */
'''

'''
Global state variables
'''
#list to hold the instructions
asm = []
STACK_SIZE = 4096
#dict of register names to values. Will always be numeric values       
reg = {'x0':0,'x1':0,'x2':0,'x3':0,'x4':0,'x5':0,'x6':0,'x7':0,'x8':0,'x9':0,'x10':0,
'x11':0,'x12':0,'x13':0,'x14':0,'x15':0,'x16':0,'x17':0,'x18':0,'x19':0,'x20':0,
'x21':0,'x22':0,'x23':0,'x24':0,'x25':0,'x26':0,'x27':0,'x28':0,'fp':0,'lr':0,'sp':0,'xzr':0}
#program counter
pc = 0
#Note: Python doesn't really have overflow and it would
#be a pain to simulate, so the v (signed overflow) flag
#is implicitly zero
#negative flag
n_flag = False 
#zero flag
z_flag = False 

'''
A map of string to int, where int will either be
an index into the mem array or a size in bytes.
Basically, vars declared with a : will be addresses and
vars declared with = will be literals
'''
sym_table = {}
'''
Data is stored as a list. Each element is an int that represents a byte. 
String data gets "converted" by doing list(bytes(str,'ascii')) and numbers 
get converted into a list from their byte representation using list(int.tobytes()).
It is accessed with an index and a size using the format [addr:addr+size].
The stack pointer also points to the end of this list and grows down.
It's first filled with static data, then extended to fit the stack.
The sp (stack pointer) register will point to the end of this list
'''
mem = []

'''
Static Rule Variables:
Specify properties that a program must have
--disallow certain instructions
--require/forbid recursion
'''
#A list that contains the mnemonic of instructions that you don want used 
#for a particular run of the the program
forbidden_instructions = []

#recursion flags
forbid_recursion = False
require_recursion = False
#loop flag
forbid_loops = False

'''
This procedure reads the lines of a program (which can be a .s file
or just a list of assembly instructions) and populates the
sym_table, mem, and asm data structures. It uses
boolean flags to determine which datastructure is currently
being populated. These flags change upon encountering specific
keywords. Those keywords are .data or .bss for declaring constants
and buffers and main: or _start: for code. 
'''
def parse(lines)->None:
    global STACK_SIZE
    #booleans for parsing .s file
    comment = False
    code = False
    data = False
    bss = False 
    '''
    This is a counter that is used to assign an "address" in mem
    to a symbol. Basically the value in sym_table when a key is one of 
    the user defined variables. It's incremented for every variable encountered
    by the size of the data stored in mem
    '''
    index = 0
    
    for line in lines:
        line = line.strip()
        #convert multiple spaces into one space 
        line = re.sub('[ \t]+',' ',line) 
        if('/*' in line and '*/' in line):continue
        if('//' in line):continue
        if("/*" in line):comment = True;continue
        if("*/" in line):comment = False;continue
        if(".data" in line):data = True;code = False;bss = False;continue
        if(".bss" in line):data = False;code = False;bss = True;continue
        if("main:" in line or "_start:" in line):code = True;data = False;bss = False;continue
        if(code and not comment and len(line)>0):line = line.lower();asm.append(line)
        if((data or bss) and not comment):
            #remove quotes and whitespace surrouding punctuation 
            #spaces following colons and periods are not touched so
            #that string literals are not altered
            line = re.sub('[ ]*:',':',line)
            line = re.sub('[ ]*\.','.',line)
            line = re.sub('[ ]*-[ ]*','-',line)
            line = re.sub('[ ]*=[ ]*','=',line)
            '''
            When encountering something like s: .asciz "a"
            we want to make s a new key in the sym_table dict and 
            set its value equal to the second element after
            splitting on the string ":.asciz". Additionally
            we save the length of the string in a "shadow entry"
            in sym_table in case someone wants to find the length
            using the -. idiom. The string gets converted to bytes
            before it is written to mem
            '''
            if(re.match('.*:\.asciz.*',line)):
                #Don't convert string literals to lower case, so split on quote
                #and everything to the left becomes lower
                line = line[0:line.find('\"')].lower() + line[line.find('\"'):]             
                #remove quote characters
                line = re.sub('["]','',line)
                #escape characters get mangled to \\<char>, convert to \<char>
                #for now just tab, carriage return, and newline 
                line = line.replace('\\n','\n')
                line = line.replace('\\t','\t')
                line = line.replace('\\r','\r')
                line = line.split(":.asciz ")
                sym_table[line[0]] = index
                sym_table[line[0]+"_SIZE_"] = len(line[1])
                mem.extend(list(bytes(line[1],'ascii')))
                index+=len(list(line[1]))
                continue
            '''
            A similar procedure is done the .space directive is used
            We first check if a previously declared variable is being
            used to determine the size. If so we fetch it and use that,
            otherwise we just use the number provided. We append a list
            with n zero values to mem where n is the size we found
            Additionally, the size is stored in a shadow entry
            '''
            if(re.match('.*:\.space.*',line)):
                line = line.lower()
                line = line.split(":.space ")
                sym_table[line[0]] = index
                if(line[1] in sym_table):
                    size = sym_table[line[1]]
                    mem.extend(list([0]*size))
                    index+=size
                    sym_table[line[0]+"_SIZE_"] = size
                else:
                    size = int(line[1])
                    mem.extend(list([0]*size))
                    index+=size
                    sym_table[line[0]+"_SIZE_"] = size
                continue    
            '''
            If using the len=.-str idiom to store str length, we
            lookup the length of str that we stored in sym_table
            dict when handling .asciz in the format str_SIZE_ 
            '''         
            if(re.match('(.)+=.-(.)+',line)):
                line = line.lower()
                line = line.split("=.-")
                if(line[1] not in sym_table):
                    raise KeyError("Can't find length of undeclared variable "+line[1])
                sym_table[line[0]] = sym_table[line[1]+"_SIZE_"]
                continue
            '''
            This is for when constants are declared with the = sign
            If assigning an existing value, look it up in the sym_table
            and if it's not there, then assume a number is being assigned. 
            '''
            if(re.match('(.)+=[a-z0-9]+',line)):
                line = line.lower()
                line = line.split("=")
                value = 0
                if(line[1] in sym_table):
                    sym_table[line[0]] = sym_table[line[1]]
                else:
                    sym_table[line[0]] = int(line[1])

    #extend mem to make room for the stack, then set the stack pointer
    mem.extend(list([0]*STACK_SIZE))
    reg['sp'] = len(mem) - 1
    
'''
This procedure dispatches and executes the provided line
of assembly code. In order to deal with the myriad
addressing modes, a regex method is used to match
the line to the appropriate action. Once an instruction is matched,
the arguments are extracted with regular epressions.The procedure 
returns after executing the matched instruction. If no match is
found an exception is thrown. Both hexadecimal
and decimal immediate values are supported. The register
naming convention is rd for destination register, rn
for the first arg register and rm for the second arg regsiter
Notes:
-int(str,0) means that both numerical strings and hex strings
will be properly converted
-Error message is very general, so any syntax errors or use 
of unsupported instructions will throw the same error.
-The current regex will match illegal register names, so a
KeyError exception will be thrown in that case
'''
def execute(line:str):
    global pc,n_flag,z_flag
    #remove spaces around commas
    line = re.sub('[ ]*,[ ]*',',',line)
    #octothorpe is optional, remove it
    line = re.sub('#','',line) 
    '''
    regexes
    '''
    rg = '(?:lr|fp|sp|xzr|x[0-9]+)'
    #immediates (hex or dec) will be last in the operand list, even though
    #this matches registers like x12 we will only worry about
    #the match list starting from the end.
    #[-] makes sure negatives are detected
    num = '[-]?(?:0x[0-9a-f]+|[0-9]+)'
    var = '[a-z]+'
    lab = '[.]*[0-9a-z_]+'
    
    
    '''
    ldp instructions
    ''' 
    #ldp rt, rt2, [rn]
    #dollar sign so it doesn't match post index
    if(re.match('ldp {},{},\[{}\]$'.format(rg,rg,rg),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]
        addr = reg[rn]
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        addr += 8
        reg[rt2] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    #ldp rt, rt2, [rn, imm]
    #dollar sign so it doesn't match pre index
    if(re.match('ldp {},{},\[{},{}\]$'.format(rg,rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn] + imm
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        addr += 8
        reg[rt2] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    
    #ldp rt, rt2, [rn, imm]! //pre index
    if(re.match('ldp {},{},\[{},{}\]!'.format(rg,rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]
        imm = int(re.findall(num,line)[-1],0)
        reg[rn] += imm
        addr = reg[rn]
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        addr += 8
        reg[rt2] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    #ldp rt, rt2, [rn], imm //post index
    if(re.match('ldp {},{},\[{}\],{}'.format(rg,rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn]
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        addr += 8
        reg[rt2] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        reg[rn] += imm
        return

    '''
    stp instructions
    '''
    #stp rt, rt2, [rn]
    #dollar sign so it doesn't match post index
    if(re.match('stp {},{},\[{}\]$'.format(rg,rg,rg),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]        
        addr = reg[rn]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        addr += 8
        mem[addr:addr+8] = list(int.to_bytes((reg[rt2]),8,'little'))
        return   
    
    #stp rt, rt2, [rn, imm]
    #dollar sign so it doesn't match pre index
    if(re.match('stp {},{},\[{},{}\]$'.format(rg,rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]
        imm = int(re.findall(num,line)[-1],0)        
        addr = reg[rn] + imm
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        addr += 8
        mem[addr:addr+8] = list(int.to_bytes((reg[rt2]),8,'little'))
        return 
    #stp rt, rt2, [rn, imm]! //pre index
    if(re.match('stp {},{},\[{},{}\]!'.format(rg,rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]        
        imm = int(re.findall(num,line)[-1],0)
        reg[rn] += imm
        addr = reg[rn]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        addr += 8
        mem[addr:addr+8] = list(int.to_bytes((reg[rt2]),8,'little'))
        return
    #stp rt, rt2, [rn], imm //post index
    if(re.match('stp {},{},\[{}\],{}'.format(rg,rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rt2 = re.findall(rg,line)[1]
        rn = re.findall(rg,line)[2]        
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        addr += 8
        mem[addr:addr+8] = list(int.to_bytes((reg[rt2]),8,'little'))
        reg[rn] += imm
        return
    '''
    ldr instructions
    '''
    #ldr rt, =<var>
    if(re.match('ldr {},={}'.format(rg,var),line)):
        rt = re.findall(rg,line)[0]
        v = re.findall('='+var,line)[0][1:]
        reg[rt] = sym_table[v]
        return
    #ldr rt, [rn]
    #dollar sign so it doesn't match post index
    if(re.match('ldr {},\[{}\]$'.format(rg,rg),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        addr = reg[rn]
        #load 8 bytes starting at addr and convert to int
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    #ldr rt, [rn, imm]
    #dollar sign so it doesn't match pre index
    if(re.match('ldr {},\[{},{}\]$'.format(rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn] + imm
        #load 8 bytes starting at addr and convert to int
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    #ldr rt, [rn, rm]
    if(re.match('ldr {},\[{},{}\]'.format(rg,rg,rg),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        addr = reg[rn] + reg[rm]
        #load 8 bytes starting at addr and convert to int
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    #ldr rt, [rn, imm]! //pre index
    if(re.match('ldr {},\[{},{}\]!'.format(rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rn] += imm
        addr = reg[rn]
        #load 8 bytes starting at addr and convert to int
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        return
    #ldr rt, [rn], imm //post index
    if(re.match('ldr {},\[{}\],{}'.format(rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn]
        #load 8 bytes starting at addr and convert to int
        reg[rt] = int.from_bytes(bytes(mem[addr:addr+8]),'little')
        reg[rn] += imm
        return
    '''
    str instructions
    '''
    #str rt, [rn]
    #dollar sign so it doesn't match post index
    if(re.match('str {},\[{}\]$'.format(rg,rg),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        addr = reg[rn]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        return    
    #str rt, [rn, imm]
    #dollar sign so it doesn't match pre index
    if(re.match('str {},\[{},{}\]$'.format(rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn] + imm
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        return    
    #str rt, [rn, rm]
    if(re.match('str {},\[{},{}\]'.format(rg,rg,rg),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        addr = reg[rn] + reg[rm]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        return
    #str rt, [rn, imm]! //pre index
    if(re.match('str {},\[{},{}\]!'.format(rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rn] += imm
        addr = reg[rn]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        return 
    #str rt, [rn], imm //post index
    if(re.match('str {},\[{}\],{}'.format(rg,rg,num),line)):
        rt = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        addr = reg[rn]
        mem[addr:addr+8] = list(int.to_bytes((reg[rt]),8,'little'))
        reg[rn] += imm
        return 
    '''
    mov instructions
    '''
    #mov rd, imm
    if(re.match('mov {},{}'.format(rg,num),line)):
        rd = re.findall(rg,line)[0]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = imm
        return
    #mov rd, rn
    if(re.match('mov {},{}'.format(rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        reg[rd] = reg[rn]
        return
    '''
    arithmetic instructions
    '''
    #asr rd, rn, imm
    if(re.match('asr {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] >> imm
        return
    #lsl rd, rn, imm
    if(re.match('lsl {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] << imm
        return
    #add{s} rd, rn, imm
    if(re.match('adds? {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] + imm
        if('adds' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False        
        return
    #add{s} rd, rn, rm
    if(re.match('adds? {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] + reg[rm]
        if('adds' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False        
        return
    #sub{s} rd, rn, imm
    if(re.match('subs? {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] - imm
        if('subs' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False
        return
    #sub{s} rd, rn, rm
    if(re.match('subs? {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] - reg[rm]
        if('subs' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False
        return
    #mul rd, rn, rm
    if(re.match('mul {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] * reg[rm]
        return
    #For now treat un/signed division the same, since everything
    #is signed in python, but separate in case this changes
    #udiv rd, rn, rm
    if(re.match('udiv {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        #IMPORTANT: use integer division, not floating point
        reg[rd] = reg[rn] // reg[rm]
        return
    #sdiv rd, rn, rm
    if(re.match('sdiv {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        #IMPORTANT: use integer division, not floating point
        reg[rd] = reg[rn] // reg[rm]
        return
    #msub rd, rn, rm, ra
    if(re.match('msub {},{},{},{}'.format(rg,rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        ra = re.findall(rg,line)[3]
        reg[rd] = reg[ra] - reg[rn] * reg[rm]
        return
    #madd rd, rn, rm, ra
    if(re.match('madd {},{},{},{}'.format(rg,rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        ra = re.findall(rg,line)[3]
        reg[rd] = reg[ra] + reg[rn] * reg[rm]
        return
    '''
    compare instructions
    '''
    #cmp rn, rm
    if(re.match('cmp {},{}'.format(rg,rg),line)):
        rn = re.findall(rg,line)[0]
        rm = re.findall(rg,line)[1]
        assert rm != 'sp', "2nd register in cmp can't be sp"
        z_flag = True if reg[rn] == reg[rm] else False
        n_flag = True if reg[rn] < reg[rm] else False
        return
    #cmp rn, imm
    if(re.match('cmp {},{}'.format(rg,num),line)):
        rn = re.findall(rg,line)[0]
        imm = int(re.findall(num,line)[-1],0)
        z_flag = True if reg[rn] == imm else False
        n_flag = True if reg[rn] < imm else False
        return
    '''
    logical instructions
    '''
    #and{s} rd, rn, imm
    if(re.match('ands? {},{},{}$'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] & imm   
        if('ands' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False 
        return 
    #and{s} rd, rn, rm
    if(re.match('ands? {},{},{}$'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] & reg[rm]   
        if('ands' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False 
        return 
    #orr{s} rd, rn, imm
    if(re.match('orrs? {},{},{}$'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] | imm
        if('orrs' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False    
        return 
    #orr{s} rd, rn, rm
    if(re.match('orrs? {},{},{}$'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] | reg[rm]
        if('orrs' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False    
        return 
    #eor{s} rd, rn, imm
    if(re.match('eors? {},{},{}$'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[-1],0)
        reg[rd] = reg[rn] ^ imm
        if('eors' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False
        return 
    '''
    branch instructions
    '''
    #cbnz rn,<label>
    if(re.match('cbnz {},{}'.format(rg,lab),line)):
        rn = re.findall(rg,line)[0]
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(reg[rn] != 0):pc = asm.index(label+':') 
        return
    #cbz rn, <label>
    if(re.match('cbz {},{}'.format(rg,lab),line)):
        rn = re.findall(rg,line)[0]
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(reg[rn] == 0):pc = asm.index(label+':') 
        return
    #b <label>
    if(re.match('b {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        pc = asm.index(label+':')
        return
    #b.lt <label>
    if(re.match('b\.?lt {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(n_flag): pc=asm.index(label+':')
        return
    #b.le <label>
    if(re.match('b\.?le {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(n_flag or z_flag): pc=asm.index(label+':')
        return
    #b.gt <label>
    if(re.match('b\.?gt {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(not z_flag and not n_flag): pc=asm.index(label+':')
        return
    #b.ge <label>
    if(re.match('b\.?ge {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(not n_flag): pc=asm.index(label+':')
        return
    #b.eq <label>
    if(re.match('b\.?eq {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(z_flag): pc=asm.index(label+':')
        return
    #b.ne <label>
    if(re.match('b\.?ne {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(not z_flag): pc=asm.index(label+':')
        return
    #b.mi <label>
    if(re.match('b\.?mi {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(n_flag): pc=asm.index(label+':')
        return
    #b.pl <label>
    if(re.match('b\.?pl {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        if(not n_flag or z_flag): pc=asm.index(label+':')
        return
    #bl <label>
    if(re.match('bl {}'.format(lab),line)):
        #last match is the label
        label = re.findall(lab,line)[-1]
        reg['lr'] = pc
        pc=asm.index(label+':')
        return
    #ret 
    if(re.match('ret',line)):
        pc = reg['lr']
        return
    '''
    system call handler
    Currently supported: Read and write to stdin/stdout, getrandom
    '''
    #svc 0
    if(re.match('svc 0',line)):
        syscall = int(reg['x8'])
        #simulate exit by causing main loop to exit
        if(syscall==93):
            pc = len(asm)
        #write
        if(syscall==64):
            assert reg['x0'] == 1, "Can only write to stdout! (x0 must contain #1)"
            length = reg['x2']
            addr = reg['x1']
            output = bytes(mem[addr:addr+length]).decode('ascii')
            #if the user wants to print a newline they have to include
            #it in their string
            print(output, end='') 
        #read
        if(syscall==63):
            length = reg['x2']
            addr = reg['x1']
            enter = input()
            enter+='\n'
            #truncate input based on # of chars read
            enter = enter[:length]
            #store as bytes, not string
            mem[addr:addr+len(enter)] = list(bytes(enter,'ascii'))
            #return value is # of bytes read
            reg['x0'] = len(enter)
        #getrandom
        if(syscall==278):
            addr = reg['x0']
            quantity = reg['x1']
            #the number of random bytes requested is written to mem
            mem[addr:addr+quantity] = list(os.urandom(quantity))
            reg['x0'] = quantity  
        return
    raise ValueError("Unsupported instruction or syntax error: "+line)
    

'''
Procedure to check that predefined rules about the code 
have been adhered to
Currently checks:
--Code has been detected and parsed into the asm list
--The same label is not declared twice
--forbidden instructions are not used
--recursion is used/not used, depending on flag
--looping is not used, depending on flag
Called in run() and debug(), so should be no
need to call this separately 
'''
def check_static_rules():
    global forbid_recursion, require_recursion
    #label regex
    lab = '[.]*[0-9a-z_]+'
    
    #Make sure code has been detected
    if(not asm):
        raise ValueError("no code detected (remember to include a _start: or main: label)")
    #check for disallowed instructions:
    #--extract mnemonics (string before the first space)
    mnemonics = [i.split(" ")[0] for i in asm if " " in i]
    forbid = set(mnemonics).intersection(forbidden_instructions)
    if(forbid): raise ValueError("Use of {} disallowed".format(forbid))
    
    #verify that labels have not be redeclared
    labels = [l for l in asm if(re.match('{}:'.format(lab),l))]
    if(len(labels)>len(set(labels))):
        raise ValueError("You can't declare the same label more than once")    
    
    
    
    #To check for recursion:
    #--get all labels that are called by the bl instruction
    #--iterate over instruction list, and
    #every time one of these labels is encountered, push
    #onto a "scope" stack
    #--when a bl <label>/ instruction is encountered,
    #check the top of the scope stack. If the label and
    #the TOS are the same, there is recursion.
    #--when a ret instruction is encountered, pop the
    #scope stack
    
    scope = []    
    #check that all BL instructions call existing labels
    for x in asm:
        if(re.match('bl {}'.format(lab),x)):
            #last match is the label
            label = re.findall(lab,x)[-1]  
            if(label+':' not in asm):
                raise ValueError(x + " is calling a nonexistent label")      

    subroutine_labels = [re.findall(lab,x)[-1]+':' for x in asm \
                            if(re.match('bl {}'.format(lab),x))]
    recursed = False
    for instr in asm:
        if(instr in subroutine_labels):
            #don't append the colon of the label
            scope.append(instr[:-1])
        if(re.match('ret', instr)):
            scope.pop()
        #match subroutine call
        if(re.match('bl {}'.format(lab),instr)):
            #last match is the label
            label = re.findall(lab,instr)[-1]
            #check top of stack
            if(label in scope[-1:]):
                recursed = True
    if(forbid_recursion and recursed):
        raise ValueError("recursion is not allowed")
    if(require_recursion and not recursed):
        raise ValueError("you must use recursion")
    #To check for looping:
    #--match any branch instruction except bl
    #--if its label occurs earlier in the instruction
    #listing than the branch, it is a loop
    looped = False
    for i in range(0,len(asm)-1):
        #match branches except for bl
        if(re.match('c?b(?!l )'.format(lab),asm[i])):
            #last match is the label
            label = re.findall(lab,asm[i])[-1]
            if(asm.index(label+':') < i):
                looped = True
    if(forbid_loops and looped):
         raise ValueError("you cannot loop") 
    

    
'''
This procedure runs the code normally to the end. Exceptions are raised
for stack overflow, if no code is detected, and if any forbidden 
instructions are found. The program is considered to have ended when
pc equals the length of the asm list
'''
def run():
    global pc, STACK_SIZE
    check_static_rules()
    while pc < len(asm):
        #check for stack overflow    
        if(reg['sp'] < len(mem) - STACK_SIZE):
            raise ValueError("stack overflow")
        line=asm[pc]
        #if a label in encountered, inc pc and skip
        if(re.match('[.]*[a-z0-9_]+:$',line)):pc+=1;continue     
        execute(line)
        reg['xzr'] = 0
        pc+=1
        
        
'''
Simple REPL for testing instructions. Limited to instructions that
only affect registers (no memory access or jumps). Prints the flags
and affected registers after executing each instruction.
'''
def repl():
    global n_flag,z_flag
    print('armsim repl. operations on memory not supported\ntype q to quit')
    instr = ''
    while(True):
        instr = input('>> ').lower()
        if(instr.startswith('q')):break
        #if enter is pressed with no input skip the rest
        if(not instr):continue
        try:
            execute(instr)
            for r in set(re.findall('x[0-9]+',instr)):
                print("{}: {}".format(r,reg[r]))
            print("Z: {} N: {}".format(n_flag,z_flag))   
        except ValueError as e:
            print(e)
    return

'''
Simple debugger interface for running a .s file. Commands are
p flags      print flags
p x1 x2..xn  print all registers listed
q            quit
n            next instruction
ls           list program with line numbers
b  <num>     breakpoint at line number
rb <num      remove breakpoint at line number
c            continue to next breakpoint
<enter>      repeat previous command
h            help
'''
def debug():
    global pc
    cmd = ''
    prevcmd = ''
    breakpoints = set()
    check_static_rules()
    while(True):
        if(pc == len(asm)): print('reached end of program. exiting...');break       
        line = asm[pc]
        cmd = input('> ').lower()
        if(not cmd and prevcmd):
            cmd = prevcmd
        if(cmd.startswith('q')):break
        elif(cmd.startswith('p ')):
            for r in set(re.findall('(?:lr|fp|sp|xzr|x[0-9]+)',cmd)):
                print("{}: {}".format(r,reg[r]))
            if('flags' in cmd):
                print("Z: {} N: {}".format(z,n))
        elif(cmd.startswith('n')):
            #if a label in encountered, inc pc and skip
            if(re.match('[.]*[0-9a-z_]+:$',line)):pc+=1;print(line);continue
            execute(line)
            print(line)
            pc+=1           
        elif(cmd.startswith('b ')):
            breakpoints.add(int(re.findall('[0-9]+',cmd)[0]))
        elif(cmd.startswith('rb ')):
            breakpoints.remove(int(re.findall('[0-9]+',cmd)[0]))
        #Should continue until breakpoint but not execute it
        elif(cmd.startswith('c')):
            if(breakpoints):
                while(pc not in breakpoints):
                    #if a label in encountered, inc pc and skip
                    if(re.match('[.]*[0-9a-z_]+:$',line)):pc+=1;continue
                    execute(line)
                    pc+=1
                    line = asm[pc]
                print("break at {}: {}".format(pc,line))           
        elif(cmd.startswith('h')):
            print("simple debugger interface for armsim. commands are\n"
                 +"  p flags      print flags\n"
                 +"  p x1 x2..xn  print all registers listed\n"
                 +"  q            quit\n"
                 +"  n            next instruction\n"
                 +"  ls           list program with line numbers\n"
                 +"  b  <num>     breakpoint at line number\n"
                 +"  rb <num>     remove breakpoint at line number\n"
                 +"  c            continue to next breakpoint\n"
                 +"  <enter>      execute previous command\n"
                 +"  h            help")
        elif(cmd.startswith('ls')):
            for i in range(0,len(asm)):
                if(i==pc):
                    #print arrow on current line
                    print("->{}: {}".format(i,asm[i]))
                else:
                    print("  {}: {}".format(i,asm[i]))
        else:
            print("command not recognized")
        prevcmd = cmd
    return
    
'''
A procedure to return the simulator to it's initial state
'''
def reset():
    global reg,z_flag,n_flag,pc
    reg = {r:0 for r in reg}
    mem.clear()
    asm.clear()
    sym_table.clear()
    n_flag = False;z_flag = False
    pc = 0
    
  
   
def main():
    if(not sys.argv[1:]):
        repl()
    else:
        _file = next(arg for arg in sys.argv if arg.endswith('.s'))
        with open(_file,'r') as f:
            parse(f.readlines())
        if(any('--debug' in arg for arg in sys.argv)):
            debug()
        else:
            run()
if __name__ == "__main__":
    main()
