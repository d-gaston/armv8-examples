.text
.global _start
_start:
main:
   /*****************
    * This test is a sequence of arithmetic instructions
    * that operates on a value in x0 in a way that any
    * changes done by one operation are undone by another
    * e.g. x0 = x0 +1; x0 = x0 - 1
    * so that at the end we have the same value we started with
    * The original value will go in x1 for comparison
    ******************/
    //exit code should be 7
    mov x0, 7
    mov x1, x0

    add x0, x0, 1234
    sub x0, x0, 1200
    sub x0, x0, 34
    mov x2, 0xffffffff
    mul x0, x0, x2
    udiv x0, x0, x2

    lsl x0, x0, 6
    lsl x0, x0, 6
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
