import re
import sys
'''
*******************
* ArmSim Overview *
*******************
The goal of this program is to simulate an arm64 processor
executing a compiled .s file. It attempts to be compatible
with the format of gnu assembler files and supports a subset
of the instructions and directives. The basic operation of
the simulator is that it first reads in a .s file line by 
line and parses the code and directives into a list of 
instructions and a map of symbols, respectively. Then
it attempts to execute each line of code by matching against
regular expressions that encode the instruction format, and
updating global variables appropriately based on that execution.

Currently supported:
  Directives:
    .data    (declare a region of initialized data)
    .bss     (declare a region of unitialized data)
    .asciz   (declare a string)
    . -      (find the length of the previously declared item)
    .space   (declare an empty buffer)
    =        (assignment of a variable to a constant value)
  Instructions:
    ldr rd,=<var>
    mov rd,imm
    mov rd,rn
    sub rd, rn, imm
    cbnz <label>
    b <label>
    svc 0 (system call)

Comments (Must NOT be on same line as stuff you want read into the program):
  //text
  /*text*/
  /*
  text
  */

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
#booleans for parsing .s file
comment = False
code = False
data = False
bss = False
'''
A map of string to int, where int will either be a literal
such as the length of a string or an index into the static
mem array.
'''
sym_lookup = {}
'''
For storing string data as a list. It is accessed with an index
and a size using the format [addr:addr+size].
'''
static_mem = []
'''
This is a counter that is used to assign an "address" to a symbol.
Basically the value in sym_lookup when a key is one of the user
defined variables. It's incremented for every variable encountered
'''
index = 0
'''
This loop reads the lines of the .s file and populates the
sym_lookup, static_mem, and asm data structures. It uses
boolean flags to determine which datastructure is currently
being populated. These flags change upon encountering specific
keywords. Those keywords are .data or .bss for declaring constants
and buffers and main: for code. Although this diverges from the 
standard it forces people to put a main label in their code, which
is needed for using gdb
'''
with open(sys.argv[1], 'r') as f:
    for line in f.readlines():
        #line = line.rstrip()
        line =line.lower().strip()
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
            line = re.sub('["]','',line)
            line = re.sub('[ ]*:[ ]*',':',line)
            line = re.sub('[ ]*\.[ ]*','.',line)
            line = re.sub('[ ]*-[ ]*','-',line)
            line = re.sub('[ ]*=[ ]*','=',line)
            '''
            When encountering something like s: .asciz "a"
            we want to make s a new key in the sym_lookup dict and 
            set its value equal to the second element after
            splitting on the string ":.asciz". Additionally
            we save the length of the string in a "shadow entry"
            in sym_lookup in case someone wants to find the length
            using the -. idiom
            '''
            if(re.match('.*:\.asciz.*',line)):
                line = line.split(":.asciz ")
                sym_lookup[line[0]] = index
                sym_lookup[line[0]+"_SIZE_"] = len(line[1])
                static_mem.extend(list(line[1]))
                index+=len(list(line[1]))
                continue
            '''
            A similar procedure is done the .space directive is used
            We first check if a previously declared variable is being
            used to determine the size. If so we fetch it and use that,
            otherwise we just use the number provided. We append a list
            with n junk values to static_mem where n is the size we found
            '''
            if(re.match('.*:\.space.*',line)):
                line = line.split(":.space ")
                sym_lookup[line[0]] = index
                if(line[1] in sym_lookup):
                    size = sym_lookup[line[1]]
                    static_mem.extend(list('0'*size))
                    index+=size
                    sym_lookup[line[0]+"_SIZE_"] = size
                else:
                    size = int(line[1])
                    static_mem.extend(list('0'*size))
                    index+=size
                    sym_lookup[line[0]+"_SIZE_"] = size
                continue    
            '''
            If using the len=.-str idiom to store str length, we
            lookup the length of str that we stored in sym_lookup
            dict when handling .asciz in the format str_SIZE_ 
            '''         
            if(re.match('(.)+=.-(.)+',line)):
                line = line.split("=.-")
                if(line[1] not in sym_lookup):
                    raise KeyError("Can't find length of undeclared variable "+line[1])
                sym_lookup[line[0]] = sym_lookup[line[1]+"_SIZE_"]
                continue
            '''
            This is for when constants are declared with the = sign
            Do the same lookup procedure as above, else just assign
            to the provided constant
            '''
            if(re.match('(.)+=[a-z0-9]+',line)):
                line = line.split("=")
                if(line[1] in sym_lookup):
                    sym_lookup[line[0]] = sym_lookup[line[1]]
                else:
                    sym_lookup[line[0]] = int(line[1])  
'''
This procedure dispatches and executes the provided line
of assembly code. In order to deal with the myriad
addressing modes, a regex method is used to match
the line to the appropriate action.The procedure returns after 
executing the matched instruction. If no match is
found an exception is thrown. Both hexadecimal
and decimal immediate values are supported. The register
naming convention is rd for destination register, rn
for the first arg register and rm for the second arg regsiter
Notes:
-int(str,0) means that both numerical strings and hex strings
will be properly converted
-Error message is very general, so any syntax errors or use 
of unsupported instructions will throw the same error.
-the current regex will match illegal register names, so a
KeyError exception will be thrown
'''
def execute(line):
    global pc,n,z
    #remove spaces around commas
    line = re.sub('[ ]*,[ ]*',',',line)
    #octothorpe is optional, remove it
    line = re.sub('#','',line) 
    '''
    ldr instructions
    '''
    #ldr rd,=<var>
    if(re.match('ldr x[0-9]+,=[a-z]+$',line)):
        rd = re.findall('x[0-9]+',line)[0]
        var = re.findall('=[a-z]+',line)[0][1:]
        reg[rd] = sym_lookup[var]
        return
    '''
    mov instructions
    '''
    #mov rd,imm
    if(re.match('mov x[0-9]+,(?:0x)?[0-9a-f]+$',line)):
        rd = re.findall('x[0-9]+',line)[0]
        imm = int(re.findall('(?:0x)?[0-9a-f]+$',line)[0],0)
        reg[rd] = imm
        return
    #mov rd,rn
    if(re.match('mov x[0-9]+,x[0-9]+$',line)):
        rd = re.findall('x[0-9]+',line)[0]
        rn = re.findall('x[0-9]+',line)[1]
        reg[rd] = reg[rn]
        return
    '''
    sub/s instructions
    '''
    #sub rd, rn, imm
    if(re.match('sub x[0-9]+,x[0-9]+,(?:0x)?[0-9a-f]+$',line)):
        rd = re.findall('x[0-9]+',line)[0]
        rn = re.findall('x[0-9]+',line)[1]
        imm = int(re.findall('(?:0x)?[0-9a-f]+$',line)[0],0)
        reg[rd] = reg[rn] - imm
        return
    '''
    branch instructions
    '''
    #cbnz <label>
    if(re.match('cbnz x[0-9]+,[._]*[a-z]+$',line)):
        rn = re.findall('x[0-9]+',line)[0]
        #the third match is the label
        label = re.findall('[._]*[a-z]+',line)[2]
        if(reg[rn] != 0):pc = asm.index(label+':') 
        return
    #b <label>
    if(re.match('b [._]*[a-z]+$',line)):
        #the second match is the label
        label = re.findall('[._]*[a-z]+',line)[1]
        pc = asm.index(label+':')
        return
    '''
    system call handler
    Currently supported: Read and write to stdin/stdout
    '''
    #svc 0
    if(re.match('svc[ ]+0',line)):
        syscall = int(reg['x8'])
        if(syscall==93):sys.exit()
        if(syscall==64):
            length = reg['x2']
            addr = reg['x1']
            output = static_mem[addr:addr+length]
            output = ''.join(output)
            #if there is a newline char in the output,
            #remove it and print normally, else print
            #with no newline
            if('\\n' in output):
                output = output.replace('\\n','')
                print(output)
            else:
                print(output, end='') 
        if(syscall==63):
            length = reg['x2']
            addr = reg['x1']
            enter = input()
            enter+='\n'
            #truncate input based on # of chars read
            enter = enter[:length]
            static_mem[addr:addr+len(enter)] = list(enter)
            reg['x0'] = len(enter)
        return
    raise ValueError("Unsupported instruction or syntax error: "+line)
           
    
#verify that labels have not be redeclared
labels = [l for l in asm if(re.match('[._]*[a-z]+:',l))]
if(len(labels)>len(set(labels))):raise ValueError("You can't declare the same label more than once")

#main loop
while pc != len(asm):
    line=asm[pc]
    execute(line)
    reg['xzr'] = 0
    pc+=1
