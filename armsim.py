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
meaning that indentifiers are not case sensitive 
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
    ldr     rd,=<var>
    ldr     rd,[rn]
    mov     rd,imm
    mov     rd,rn
    sub{s}  rd, rn, imm
    sub{s}  rd, rn, rm
    add{s}  rd, rn, imm
    add{s}  rd, rn, rm
    asr     rd, rn, rm
    lsr     rd, rn, rm
    udiv    rd, rn, rm
    sdiv    rd, rn, rm
    mul     rd, rn, rm
    msub    rd, rn, rm, ra
    madd    rd, rn, rm, ra
    and{s}  rd, rn, imm
    orr{s}  rd, rn, imm
    eor{s}  rd, rn, imm
    cmp     rn, rm
    cbnz    rn, <label>
    cbz     rn, <label>
    b       <label>
    b.gt    <label>
    b.lt    <label>
    b.eq    <label>
    b.ne    <label>
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
#list to represent the stack
s=[0]*1001 
#dict of register names to values. Will always be numeric values       
reg = {'sp':1000,'lr':0,'x0':0,'x1':0,'x2':0,'x3':0,'x4':0,'x5':0,'x6':0,'x7':0,'x8':0,'x9':0,'x10':0,
'x11':0,'x12':0,'x13':0,'x14':0,'x15':0,'x16':0,'x17':0,'x18':0,'x19':0,'x20':0,
'x21':0,'x22':0,'x23':0,'x24':0,'x25':0,'x26':0,'x27':0,'x28':0,'x29':0,'x30':0,'xzr':0}
#program counter
pc = 0
#negative flag
n_flag = False 
#zero flag
z_flag = False 

'''
A map of string to int, where int will either be
an index into the static_mem array or a size in bytes.
Basically, vars declared with a : will be addresses and
vars declared with = will be literals
'''
sym_table = {}
'''
Static data is stored as a list. Each element is an int that represents a byte. 
String data gets "converted" by doing list(bytes(str,'ascii')) and numbers 
get converted into a list from their byte representation using list(int.tobytes()).
It is accessed with an index and a size using the format [addr:addr+size].
'''
static_mem = []



'''
This procedure reads the lines of a program (which can be a .s file
or just a list of assembly instructions) and populates the
sym_table, static_mem, and asm data structures. It uses
boolean flags to determine which datastructure is currently
being populated. These flags change upon encountering specific
keywords. Those keywords are .data or .bss for declaring constants
and buffers and main: for code. Although this diverges from the 
standard it forces people to put a main label in their code, which
is needed for using gdb
'''

def parse(lines)->None:
    #booleans for parsing .s file
    comment = False
    code = False
    data = False
    bss = False 
    '''
    This is a counter that is used to assign an "address" in static_mem
    to a symbol. Basically the value in sym_table when a key is one of 
    the user defined variables. It's incremented for every variable encountered
    by the size of the data stored in static_mem
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
        if("main:" in line):code = True;data = False;bss = False;continue
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
            before it is written to static_mem
            '''
            if(re.match('.*:\.asciz.*',line)):
                #Don't convert string literals to lower case, so split on quote
                #and everything to the left becomes lower
                line = line[0:line.find('\"')].lower() + line[line.find('\"'):]
                #remove quote characters
                line = re.sub('["]','',line)            
                line = line.split(":.asciz ")
                sym_table[line[0]] = index
                sym_table[line[0]+"_SIZE_"] = len(line[1])
                static_mem.extend(list(bytes(line[1],'ascii')))
                index+=len(list(line[1]))
                continue
            '''
            A similar procedure is done the .space directive is used
            We first check if a previously declared variable is being
            used to determine the size. If so we fetch it and use that,
            otherwise we just use the number provided. We append a list
            with n zero values to static_mem where n is the size we found
            Additionally, the size is stored in a shadow entry
            '''
            if(re.match('.*:\.space.*',line)):
                line = line.lower()
                line = line.split(":.space ")
                sym_table[line[0]] = index
                if(line[1] in sym_table):
                    size = sym_table[line[1]]
                    static_mem.extend(list([0]*size))
                    index+=size
                    sym_table[line[0]+"_SIZE_"] = size
                else:
                    size = int(line[1])
                    static_mem.extend(list([0]*size))
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
    #verify that labels have not be redeclared
    labels = [l for l in asm if(re.match('[._]*[a-z]+:',l))]
    if(len(labels)>len(set(labels))):raise ValueError("You can't declare the same label more than once")
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
KeyError exception will be thrown
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
    rg = '(?:sp|xzr|x[0-9]+)'
    #immediates will always be the final operand so the $ is necessary
    #[-] makes sure negatives are detected
    num = '[-]?(?:0x[0-9a-f]+|[0-9]+)$'
    var = '[a-z]+'
    lab = '[.]*[0-9a-z_]+'
    '''
    ldr instructions
    '''
    #ldr rd, =<var>
    if(re.match('ldr {},={}'.format(rg,var),line)):
        rd = re.findall(rg,line)[0]
        v = re.findall('='+var,line)[0][1:]
        reg[rd] = sym_table[v]
        return
    #ldr rd, [rn]
    if(re.match('ldr {},\[{}\]'.format(rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        addr = reg[rn]
        #load 8 bytes starting at addr and convert to int
        reg[rd] = int.from_bytes(bytes(static_mem[addr:addr+8]),'little')
        return
    '''
    mov instructions
    '''
    #mov rd, imm
    if(re.match('mov {},{}'.format(rg,num),line)):
        rd = re.findall(rg,line)[0]
        imm = int(re.findall(num,line)[0],0)
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
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] >> imm
    #lsl rd, rn, imm
    if(re.match('lsl {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] << imm
    #add{s} rd, rn, imm
    if(re.match('adds? {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
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
        imm = int(re.findall(num,line)[0],0)
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
        z_flag = True if reg[rn] == reg[rm] else False
        n_flag = True if reg[rn] < reg[rm] else False
        return
    #cmp rn, imm
    if(re.match('cmp {},{}'.format(rg,num),line)):
        rn = re.findall(rg,line)[0]
        imm = int(re.findall(num,line)[0],0)
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
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] & imm   
        if('ands' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False 
        return 
    #orr{s} rd, rn, imm
    if(re.match('orrs? {},{},{}$'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] | imm
        if('orrs' in line):
            n_flag = True if(reg[rd] < 0) else False
            z_flag = True if(reg[rd] == 0) else False    
        return 
    #eor{s} rd, rn, imm
    if(re.match('eors? {},{},{}$'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
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
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(reg[rn] != 0):pc = asm.index(label+':') 
        return
    #cbz rn, <label>
    if(re.match('cbz {},{}'.format(rg,lab),line)):
        rn = re.findall(rg,line)[0]
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(reg[rn] == 0):pc = asm.index(label+':') 
        return
    #b <label>
    if(re.match('b {}'.format(lab),line)):
        #the second match is the label
        label = re.findall(lab,line)[1]
        pc = asm.index(label+':')
        return
    #b.lt <label>
    if(re.match('b\.lt {}'.format(lab),line)):
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(n_flag): pc=asm.index(label+':')
        return
    #b.gt <label>
    if(re.match('b\.gt {}'.format(lab),line)):
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(not z_flag and not n_flag): pc=asm.index(label+':')
        return
    #b.eq <label>
    if(re.match('b\.eq {}'.format(lab),line)):
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(z_flag): pc=asm.index(label+':')
        return
    #b.ne <label>
    if(re.match('b\.ne {}'.format(lab),line)):
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(not z_flag): pc=asm.index(label+':')
        return
    '''
    system call handler
    Currently supported: Read and write to stdin/stdout, getrandom
    '''
    #svc 0
    if(re.match('svc 0',line)):
        syscall = int(reg['x8'])
        if(syscall==93):sys.exit()
        #write
        if(syscall==64):
            length = reg['x2']
            addr = reg['x1']
            output = bytes(static_mem[addr:addr+length]).decode('ascii')
            #if there is a newline char in the output,
            #remove it and print normally, else print
            #with no newline
            if('\\n' in output):
                output = output.replace('\\n','')
                print(output)
            else:
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
            static_mem[addr:addr+len(enter)] = list(bytes(enter,'ascii'))
            #return value is # of bytes read
            reg['x0'] = len(enter)
        #getrandom
        if(syscall==278):
            addr = reg['x0']
            quantity = reg['x1']
            #the number of random bytes requested is written to static_mem
            static_mem[addr:addr+quantity] = list(os.urandom(quantity))
            reg['x0'] = quantity  
        return
    raise ValueError("Unsupported instruction or syntax error: "+line)
    
'''
This procedure runs the code normally to the end
'''
def run():
    global pc
    while pc != len(asm):
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
    while(True):
        line = asm[pc]
        cmd = input('> ').lower()
        if(not cmd and prevcmd):
            cmd = prevcmd
        if(cmd.startswith('q')):break
        elif(cmd.startswith('p ')):
            for r in set(re.findall('x[0-9]+',cmd)):
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
    global reg,z_flag,n_flag
    reg = {r:0 for r in reg}
    reg['sp'] = 1000
    static_mem.clear()
    asm.clear()
    sym_table.clear()
    n_flag = False;z_flag = False
    
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
            print(reg['x0'])
if __name__ == "__main__":
    main()
