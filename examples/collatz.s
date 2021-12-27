.text
.global _start

_start:

main:
    /*******************************
     * Collatz Counter
     * This program will get a number from the user, convert from
     * ascii to a a number, then use a recursive subroutine to 
     * calculate the number of steps for the collatz conjecture to
     * reach 1 for that input. This program serves as an example for
     * how to write simple subroutines in ARM assembly
     * The three subroutines are:
     *   str2int - convert at most 7 bytes of number characters to an int
     *   collatz - calculate the number of steps for collatx conjecture 
     *   to reach 1
     *   int2str - convert an int to at most 7 bytes of number characters
     * Limitations:
     * -Input/output string can be no longer than 8 bytes (register length)
     * so 7 number chars + newline (not gonna bother for the case where it's
     * 8 number chars and no newline)
     * This is because I won't be using load/store byte instructions
     * since they require using the W registers 
     *******************************/
    //allocate stack space for local variable. Even though we only need space for 
    //one variable, the stack pointer (sp) must be aligned on a 16 byte boundary.
    sub sp, sp, 16
    
   /***********************
    * Print out prompt
    ***********************/
    mov x0, #1
    ldr x1, =prompt
    ldr x2, =plen
    mov x8, 0x40
    svc 0
    

   /***********************
    * Read 8 bytes maximum
    ***********************/
    mov x0, #1
    ldr x1, =entry
    mov x2, 8
    mov x8, 0x3f
    svc 0
    

    mov x1, x0
    ldr x0, =entry
   /***********************
    * Pointer to input is in x0
    * bytes entered is in x1 
    * (returned from syscall)
    ***********************/
    
   /***********************
    * The Branch with Link (bl) instruction jumps unconditionally to the
    * address of the label but unlike the b instruction it saves the 
    * address of the next instruction (the return address) in the link
    * register (x30 aka lr). The RETurn instruction performs an unconditional
    * jump to the address in the link register.
    ***********************/
    bl str2int
    
    //if input is 0, quit
    cbz x0, exit
    
    bl collatz
    
    //save collatz steps value on stack
    str x0, [sp, 8]
    
    bl int2str
    
    
    
   /***********************
    * Load pointer to "steps" variable
    * and store result of int2str there
    ***********************/    
    ldr x1, =steps
    str x0, [x1]
    
   /***********************
    * Print out "report" string
    ***********************/
    mov x0, #1
    ldr x1, =report
    ldr x2, =rlen
    mov x8, 0x40
    svc 0
   /***********************
    * Print out "steps" string
    ***********************/
    mov x0, #1
    ldr x1, =steps
    mov x2, 8
    mov x8, 0x40
    svc 0
    
    //retrieve collatz steps to use as exit value
    ldr x0, [sp, 8]
  exit:
    //restore stack
    add sp, sp, 16
   /********************
    * Exit syscall 
    *********************/
    mov x8, #93
    svc 0
    
/*************************
 * Algorithm:
 * extract lowest byte, with a bitmask, 
 * convert to int by subtracting 0x30, then multiply by 
 * a power of ten depending on the position. The bytes of the 
 * number string are stored in little endian order. Example:
 * '123\n' is 0x0a333231, most significant place is 10^2
 * So 1) 0x0a333231 & 0xff = 0x31
 *    2) 0x31 - 0x30 = 0x1
 *    3) 0x1 * 100 = 100
 *    4) 0x0a333231 >> 8 = 0x0a3332
      5) multiplier = multiplier / 10
 *    6) goto 1 until multiplier = 0
 * x0 - pointer to string
 * x1 - string length
 *************************/   
str2int:
   /***********************
    * Push return address:
    * sp <- sp - 16
    * *sp <- fp
    * *(sp + 8) <- lr
    ***********************/
    stp fp, lr, [sp, #-16]!
    
    //string length - 1 (because of newline char)
    sub x1, x1, 1
    
    //use x10 as a constant containing for mul/div
    mov x10, 10
    
    //x2 holds power of ten
    mov x2, 1
    
    //get most significant power of ten (# of digits - 1)
    sub x1, x1, 1
  pow:
    cbz x1, endpow
    mul x2, x2, x10
    sub x1, x1, 1
    b pow
    endpow:
    
    //x3 holds ALL bytes of the string
    ldr x3, [x0]
 
    //we will accumulate the result in x5
    mov x5, 0
    
  loop:

    //get first byte (which is the most significant (little endian)
    and x4, x3, 0xff

    //convert char -> int 
    sub x4, x4, 0x30
    
    //multiply by current power of 10
    mul x4, x4, x2
    
    //add to result
    add x5, x5, x4
    
    //decrease power of ten
    udiv x2, x2, x10
    
    //shift by a byte to expose next-most significant byte
    asr x3, x3, 8
    //loop ends when multipler is 0
    cbnz x2, loop
    
    //put result in return value
    mov x0, x5
   /***********************
    * Pop return address
    * fp <- *sp 
    * lr <- *(sp + 8)
    * sp <- sp + 16 
    ***********************/
    ldp fp, lr, [sp], #16
    ret
/*************************
 * Algorithm:
 * Divide number by 10 and convert remainder
 * to string by adding 0x30. This is stored in
 * a register that is shifted left each time
 * to make room in the string. Remember that we
 * are using little endian byte order, which is
 * why we are shifting the least significant bits
 * to the left
 * Example 123
 *   1) num mod 10 = 3
 *   2) char <- 3 + 0x30
 *   3) str OR char = 0x33
 *   4) str << 8 = 0x3300
     5) goto 1 until num is less than 10
 * x0 - int to covert
 *************************/   
 int2str:
    stp fp, lr, [sp, #-16]!
    //use x10 as a constant containing for mul/div
    mov x10, 10
    
    //keep result in x4, starting with newline character
    mov x4,0xa
    
    //make room for the next byte
    lsl x4,x4,8
  .loop:
    //get the remainder in x3 (see guess.s for how this works)
    udiv x2, x0, x10
    msub x3, x10, x2, x0
        //put byte at end of result
    add x3, x3, 0x30
    orr x4, x4, x3
    //mov string by a byte
    lsl x4, x4, 8
    //actually divide number
    udiv x0, x0, x10
    //if number is less than 10, finish 
    cmp x0, 9
    bgt .loop

    //put in most significant byte
    add x3, x0, 0x30
    orr  x4, x4, x3
    //return result
    mov x0, x4
    ldp fp, lr, [sp], #16
    ret
    
 
    
/***********************
 * Algorithm:
 * if arg is even, divide by 2
 * if arg is odd, times 3 + 1
 * if arg is one, return
 * Number of steps is tracked recursively
 * meaning every call is incremented and 
 * the base case is 1
 * Only one recursive call is possible each time so
 * the result can be safely left in a register
 * C translation:
 * int collatz(int num){
 * 	if(num==1) return 1;
 * 	if(num%2==0) return collatz(num/2)+1;
 * 	else return collatz(3*num+1)+1;	
 * }
 ***********************/
collatz:
    stp fp,lr, [sp, #-16]!
    cmp x0,1
    bne recurse
    b terminate
  recurse:
    and x4, x0, 1
    cbz x4, even
  odd:
    mov x3, 3
    mul x0, x0, x3
    add x0, x0, 1
    bl collatz
    add x0, x0, 1
    b terminate
  even:
    asr x0, x0, 1
    bl collatz
    add x0, x0, 1
  terminate:
    ldp fp, lr, [sp], #16
    ret
        
       

.data
prompt: .asciz "Enter a positive number no more than 7 digits: "
plen = .-prompt

report: .asciz "Collatz steps: "
rlen = .-report

.bss
entry: .space 8
steps: .space 8

