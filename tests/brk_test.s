.text
.global _start

_start:

main:
    /**********************
     * Allocate heap memory with brk:
     * 1) call brk with invalid address 
     *    which returns current heap address
     * 2) increment current address with desired
     *    amount of memory
     * 3) call brk again with this address
     * Deallocate heap memory:
     * 1) put original address returned from 1)
     *    above and call brk
     **********************/
    
    //brk system call
    mov x8, 214
    //invalid address
    mov x0, 0
    svc 0
    //store the original break in x2
    mov x2, x0 


    //increment break by 8
    add x0, x0, 8
    
    //brk system call
    mov x8, 214
    svc 0
    
    /********************
     * At this point brk has been set to 
     * the original + 8, but the OS has
     * rounded this up to an entire page
     * of memory (=4096,=0x1000)
     ********************/
    
    mov x4, 4
    mov x3, 3
    //store 4 at the last 8 bytes of the page
    mov x5, 0xff8
    str x4, [x2, x5]
    //store 3 at the first 8 bytes of the page
    str x3, [x2]
    
    //verify that values can be retrieved
    ldr x4, [x2,x5]
    ldr x3, [x2]
    //deallocate
    mov x0, x2
    mov x8,214
    svc 0 
    
    //put 7 in x0 to return
    add x0, x3, x4
    //exit
    mov x8,93
    svc 0
