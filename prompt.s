.text            
.global _start

    /********************
     * Syscall format
     * x8 - syscall number
     * If there are args:
     * x0 - first argument
     * x1 - second argument
     * x2 - third argument
     * and so on
     *********************/
_start:

main:
    /**************************
     * Program overview:
     * First we will display a prompt
     * to the user asking for a name
     * with the write syscall
     * Then we will use the read syscall to 
     * take input. This input will be stored 
     * in a buffer we have declared.
     * Finally, we will output a greeting and
     * the user's name with 2 more calls to write
     **************************/
     
    /********************
     * Write syscall
     * syscall number: 0x40 (64)
     * first arg: file descriptor 
     *    1 is the fd for stdout
     * second arg: pointer to string
     *    here it is stored in prompt
     * third arg: num of bytes to print
     *    here it's the length of prompt
     *********************/
    mov x0, #1
    ldr x1, =prompt
    ldr x2, =plen
    mov x8, 0x40
    svc 0
    
    
    /********************
     * Read syscall
     * syscall number: 0x3f (63)
     * first arg: file descriptor 
     *    0 is the fd for stdin
     * second arg: pointer to buffer
     *    here it is stored in "message"
     * third arg: num of bytes to read in
     *    here it's the length of message
     *********************/
    mov x0, #1
    ldr x1, =buffer
    ldr x2, =bufSize
    mov x8, 0x3f
    svc 0
    /*******************
     * Return value is in x0
     * we'll use x4 as a temp register
     * to store it for a later write call
     * We could declare some more memory
     * in the bss section but that's overkill
     * for this
     *******************/
    mov x4, x0
    
    
    /********************
     * Write syscalls 
     *********************/
    mov x0, #1
    ldr x1, =greeting
    ldr x2, =glen
    mov x8, 0x40
    svc 0


    mov x0, #1
    ldr x1, =buffer
    /********************
     * Remember that we stored the bytes entered
     * in x4
     *********************/    
    mov x2,x4
    mov x8, 0x40
    svc 0
    
    /********************
     * Exit syscall
     * syscall number: 0x5d (93)
     * no arguments
     *********************/
    mov x8, #93
    svc 0

.data
prompt: .asciz "enter your name: "
plen = .-prompt 
greeting: .asciz "hello "
glen = .-greeting 
bufSize = 24


/*bss is for uninitialized data*/
.bss
/*declare a buffer of 24 bytes */
buffer: .space bufSize
