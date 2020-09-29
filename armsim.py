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
    .bss     (declare a region of unitialized data)
    .asciz   (declare a string)
    . -      (find the length of the previously declared item)
    .space   (declare an empty buffer)
    =        (assignment of a variable to a constant value)
  Instructions:
    **{s} means that 's' can be optionally added to the end of an
    instruction to make the result affect the flags**
    
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
    cbnz    <label>
    cbz     <label>
    b       <label>
    b.gt    <label>
    b.lt    <label>
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
n = False 
#zero flag
z = False 

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
		#Don't convert string literals to lower case, so split on quote
		#and everything to the left becomes lower
        line = line[0:line.find('\"')].lower() + line[line.find('\"'):]
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
        if(code and not comment and len(line)>0):asm.append(line)
        if((data or bss) and not comment):
            #remove quotes and whitespace surrouding punctuation 
            #spaces following colons and periods are not touched so
            #that string literals are not altered
            line = re.sub('["]','',line)
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
    global pc,n,z
    #remove spaces around commas
    line = re.sub('[ ]*,[ ]*',',',line)
    #octothorpe is optional, remove it
    line = re.sub('#','',line) 
    '''
    regexes
    '''

    rg = '(?:xzr|x[0-9]+)'
    #immediates will always be the final operand so the $ is necessary
    num = '(?:0x[0-9a-f]+|[0-9]+)$'
    var = '[a-z]+'
    lab = '[._]*[a-z]+'
    '''
    ldr instructions
    '''
    #ldr rd, =<var>
    if(re.match('ldr {},={}'.format(rg,var),line)):
        rd = re.findall(rg,line)[0]
        v = re.findall('='+var,line)[0][1:]
        reg[rd] = sym_table[v]
        return
    #ldr rd, [rn]>
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
    #add{s} rd, rn, imm
    if(re.match('adds? {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] + imm
        if('adds' in line):
            n = True if(reg[rd] < 0) else False
            z = True if(reg[rd] == 0) else False        
        return
    #add{s} rd, rn, rm
    if(re.match('adds? {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] + reg[rm]
        if('adds' in line):
            n = True if(reg[rd] < 0) else False
            z = True if(reg[rd] == 0) else False        
        return
    #sub{s} rd, rn, imm
    if(re.match('subs? {},{},{}'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] - imm
        if('subs' in line):
            n = True if(reg[rd] < 0) else False
            z = True if(reg[rd] == 0) else False
        return
    #sub{s} rd, rn, rm
    if(re.match('subs? {},{},{}'.format(rg,rg,rg),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        rm = re.findall(rg,line)[2]
        reg[rd] = reg[rn] - reg[rm]
        if('subs' in line):
            n = True if(reg[rd] < 0) else False
            z = True if(reg[rd] == 0) else False
        return
    #For now treat un/signed division the same, since everything
    #is signed in python
    #(u)div rd, rn, rm
    if(re.match('u?div {},{},{}'.format(rg,rg,rg),line)):
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
    '''
    compare instructions
    '''
    #cmp rn, rm
    if(re.match('cmp {},{}'.format(rg,rg),line)):
        rn = re.findall(rg,line)[0]
        rm = re.findall(rg,line)[1]
        z = True if reg[rn] == reg[rm] else False
        n = True if reg[rn] < reg[rm] else False
        return
    '''
    logical instructions
    '''
    #and rd, rn, imm
    if(re.match('and {},{},{}$'.format(rg,rg,num),line)):
        rd = re.findall(rg,line)[0]
        rn = re.findall(rg,line)[1]
        imm = int(re.findall(num,line)[0],0)
        reg[rd] = reg[rn] & imm    
        return 
    '''
    branch instructions
    '''
    #cbnz <label>
    if(re.match('cbnz {},{}'.format(rg,lab),line)):
        rn = re.findall(rg,line)[0]
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(reg[rn] != 0):pc = asm.index(label+':') 
        return
    #cbz <label>
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
        if(n): pc=asm.index(label+':')
        return
    #b.gt <label>
    if(re.match('b\.gt {}'.format(lab),line)):
        #the third match is the label
        label = re.findall(lab,line)[2]
        if(not z and not n): pc=asm.index(label+':')
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
 
def main():
	global pc
	with open(sys.argv[1], 'r') as f:
		parse(f.readlines())
	while pc != len(asm):
		line=asm[pc]
		#if a label in encountered, inc pc and skip
		if(re.match('[._]*[a-z]+:$',line)):pc+=1;continue
		execute(line)
		reg['xzr'] = 0
		pc+=1
if __name__ == "__main__":
	main()
