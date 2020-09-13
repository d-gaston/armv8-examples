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
     * Demonstration of a 
     * simple loop construct.
     * The loop will be used to 
     * print a message 10 times
     **************************/
    
    /******************
     * Our counter will be
     * kept in x4
     ******************/
     mov x4, #10
 /***************
  * Declare a label .loop: that
  * we will jump to. Labels can generally
  * be used to jump anywhere in the program
  * For example, let's use a jump to avoid
  * this call to exit:
  ***************/
    b .loop

    /********************
     * Exit syscall
     *********************/
    mov x8, #93
    svc 0
    
 /***************
  * Thanks to b .loop
  * our program arrives here
  * and avoids the premature
  * exit
  ****************/
.loop:
    /********************
     * Write syscall
     *********************/ 
    mov x0, #1
    ldr x1, =message
    ldr x2, =len
    mov x8, 0x40
    svc 0
    /********************
     * Decrement x4
     *********************/
    sub  x4, x4, 1
    /********************
     * Compare and Branch on Zero compares a given 
     * register to zero. If the register does not equal
     * zero, the jump is taken to the given label
     *********************/    
    cbnz x4, .loop
    /********************
     * Exit syscall
     *********************/
    mov x8, #93
    svc 0
    

.data
message: .asciz "hello world\n"
len = . - message
 


