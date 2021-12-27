.text
.global _start

_start:
/*****************
 * Guessing Game
 * ----------------
 * This is a simple game in which a random number is 
 * generated and the user must guess it. The number will
 * always be between 0 and 9 to avoid the issue of converting
 * multiple ascii characters to an int. This program introduces
 * the syscall getrandom as well as several new assembly instructions:
 *   udiv: unsigned divide
 *   msub: multiply and subtract
 *   cmp:  compare
 *   b.lt: branch less than
 *   b.gt: branch greather than
 *   and:  logical and
 *****************/

main:

   /********************
    * getrandom syscall
    * syscall number: 0x116 (278)
    * first arg: buffer 
    * second arg: number of bytes to write
    * third arg: flags
    *    we won't be using these here
    * return val: # of bytes written to buffer
    *********************/
    ldr x0, =num
    mov x1, 8
    mov x8, 278
    svc 0

   /********************
    * Now we want to take the result in 
    * num and make it a number between
    * 0 and 9. To do this we'll divide the
    * random number by 9 and calculate the
    * remainder.
    * Since we don't have the modulo operator (% in C)
    * we'll have to calculate it in the following way:
    * remainder = dividend - quotient x divisor
    * We'll map them to the follwing registers:
    * x5: remainder
    * x2: divisor (9)
    * x4: dividend (the random number)
    * x3: quotient
    *********************/
    mov  x2, 9
    
   /********************
    * num contains the address of the random
    * bytes we wrote earlier. To get the byte's
    * themselves we need to dereference the address,
    * but we can't do ldr x6, [num] so we load it 
    * into a register first.
    ********************/
    ldr  x6, =num
    ldr  x4, [x6]
    
    /********************
    * Unsigned DIVide takes the form
    * UDIV rd, rn, rm with the sematics
    * rd = rn ÷ rm
    * This is an integer division, so 3/2 would be 1, not 1.5
    ********************/
    udiv x3, x4, x2
    
   /********************
    * MSUB is an interesting instruction
    * it's Multiply and SUBtract with the form
    * MSUB rd, rn, rm, ra 
    * with the sematics
    * rd = ra − rn × rm
    * This will allow us to calculate:
    * remainder = dividend - quotient x divisor
    * (x5)        (x4)       (x3)       (x2)
    ********************/
    msub x5, x3, x2, x4

gameLoop:
    /*write syscall*/
    mov x0, #1
    ldr x1, =prompt
    ldr x2, =plen
    mov x8, 0x40
    svc 0

   /*read syscall*/
   /***********************
    * We need to read 2 bytes even though
    * only one is needed for the number 
    * character, since enter produces a character
    * as well. If not dealt with, it will stay in
    * the buffer and be consumed by the next
    * call to read
    ***********************/
    mov x0, #1
    ldr x1, =guess
    mov x2, 2
    mov x8, 0x3f
    svc 0

   /**********************
    * convert ascii digit 
    * to number by subtracting
    * ascii value for '0' which
    * is 0x30 (48). But first we 
    * have to get rid of the enter 
    * character. To do this we'll 
    * use a bitmask to extract the 
    * byte we want.
    * The bitmask works by using a logical
    * operation to "select" the bits that
    * we want. We can use the fact that
    * 0 AND anything is 0 and 1 AND anything is itself
    * to keep only the lower byte. To illustrate:
    * 
    *     don't want      want to keep
    *     1 0 1 1         1 1 0 1
    * AND 0 0 0 0         1 1 1 1
    * ---------------------------
    *     0 0 0 0         1 1 0 1
    **********************/
    ldr x6, =guess
    ldr x4, [x6]
    and x4, x4, 0xFF
    sub x4, x4, 48
    
   /**********************
    * CoMPare performs a subtraction of rn - rm
    * given cmp rn, rm and throws away the result
    * The appropriate flags (N,V,Z) are set according
    * to the result. The conditional branches then
    * read the flags to decide whether or not to
    * take the jump
    **********************/
    cmp x4, x5
    b.gt .tooHigh
    b.lt .tooLow
    
   /*********************
    * We could add another branch 
    * for the equals case, but it's
    * easier to just let it fall through
    * In other words, if the above two 
    * conditions are not met, execution
    * will continue to here.
    *********************/
    /*write syscall*/
    mov x0, #1
    ldr x1, =equal
    ldr x2, =eLen
    mov x8, 0x40
    svc 0
   /********************
    * Exit syscall
    *********************/
    mov x8, #93
    svc 0

    .tooHigh:
      /*write syscall*/
      mov x0, #1
      ldr x1, =guessHigh
      ldr x2, =ghLen
      mov x8, 0x40
      svc 0 
      b gameLoop
    .tooLow:
      /*write syscall*/
      mov x0, #1
      ldr x1, =guessLow
      ldr x2, =glLen
      mov x8, 0x40
      svc 0 
      b gameLoop
      
      
.data
prompt: .asciz "Guess a number between 0 and 9: "
plen = .-prompt

guessHigh: .asciz "Too high! Try again\n"
ghLen = .-guessHigh

guessLow: .asciz "Too low! Try again\n"
glLen = .-guessLow

equal: .asciz "Congratulations! You guessed it!\n"
eLen = .-equal

.bss
guess: .space 8
num: .space 8
