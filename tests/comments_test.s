.text
.global _start

_start:


main:
  /*****************
  * This test is a derivative of the more readable 
  * 'arithmetic_test.s'. The functionality reamins, 
  * however, the program is meant to succeed if the 
  * parser can correctly parse comments.
  ******************/

    //exit code should be 7
    mov x0, 7           //  ALPHA
    mov x1, x0          //  BETA

    add x0, x0, 1234    /* GAMMA */ 
    /* DELTA */ sub x0, x0, 1200   

    sub x0,/* EPSILON */x0, 34
    
    /*
    * ZETA 
    */mov x2, 0xffffffff 
    /*
    * ETA
    */mul x0, x0, x2 /*
    * THETA
    */udiv x0, x0, x2 /*
    * IOTA
    */

    lsl x0, x0, 6 /* KAPPA *//* LAMBDA */
    /* MU */lsl /* NU */x0,/* XI */ x0/*OMNICRON*/, 6
    asr x0, x0, 3
    asr x0, x0, 9



    mov x2,2
    mov x3,3
    msub x0,x2,x3,x0
    madd x0,x2,x3,x0

    cmp x0,x1
    b.eq correct
    mov x0,-1
correct:
    /* exit */
    mov x8, #93
    svc #0