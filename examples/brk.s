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
