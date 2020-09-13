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

	/********************
	 * a main label is included so that 
     * gdb can be used for debugging 
	 *********************/
main:
	/**************************
	 * Program overview:
     * An overview an example usage
     * of the write syscall
	 **************************/



	/********************
	 * Write syscall
	 * syscall number: 0x40 (64)
	 * first arg: file descriptor 
	 *    1 is the fd for stdout
	 * second arg: pointer to string
	 *    here it is stored in message
	 * third arg: num of chars to print
	 *    here it's the length of message
	 *********************/
	 
	 
    mov x0, #1
    /********************
     * Difference between ldr and mov:
     * mov is for moving values between 
     * registers or moving constants into registers
     * ldr is for loading a value from memory
     *********************
     * This instruction loads the value stored
     * at the memory address message
     *********************/
    ldr x1, =message
    /*********************
     * This instruction could be
     *     mov x2,#13 
     * if we know the length
     ********************/
    ldr x2, =len
    mov x8, 0x40
    /********************
	 * This tells the OS to execute the syscall
	 *********************/
    svc 0

	/********************
	 * Exit syscall
	 * syscall number: 0x5d (93)
	 * no arguments
	 *********************/
    mov x8, #93
    svc 0
    
    
/***********************************  
 *The data section is for initialized data
 **********************************/    
.data
message: .asciz "hello world\n"
/*len equals current position (the dot) minus address of message,
  which gives us the length of the string. Handy shortcut*/
len = . - message

/***********************************
 * Let's look at how this is laid out in the executable:
 * 000000d0: e000 4100 0000 0000 0d00 0000 0000 0000  ..A.............
 * 000000e0: 6865 6c6c 6f20 776f 726c 640a 0000 0000  hello world.....
 * When we do 
 *     ldr x1, =message
 * it gets translated to 
 *     ldr     x1, 0x4000d0
 * When running the program we see that x1 gets the value 0x4100e0
 * which is indeed what is stored at 0x4000d0. This is a pointer to the
 * "hello world\n" string which is passed to the write syscall and printed
 * Similarly, ldr x2, =len becomes
 *     ldr     x2, 0x4000d8
 * which loads the value stored there into x2. Again we can see from the memory
 * dump that the value there is 0xd (13).
 **********************************/    


