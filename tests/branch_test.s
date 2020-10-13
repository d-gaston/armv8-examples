.text
.global _start

_start:

main:

    /************************
     * A test case for the conditional branches
     * The correct exit value is put in x0 at the start,
     * and if all branches are taken correctly the program
     * will exit with that value. If not, it will exit
     * with an incorrect value
     ************************/
     
     mov x0, 7 
     
     //test "equal" part of ge and le (+ eq)
     mov x1, 7
     cmp x0, x1
     ble L1
     b bad_exit
     L1:
     bge L2
     b bad_exit
     L2:
     beq L3
     b bad_exit
     L3:
     //test "less" part of le and lt (+ ne)
     mov x1, 8
     cmp x0, x1
     blt L4
     b bad_exit
     L4:
     ble L5
     b bad_exit
     L5:
     bne L6
     b bad_exit
     L6:
     //test "greater" part of ge and gt (+ ne)
     mov x1, 6
     cmp x0, x1
     bgt L7
     b bad_exit
     L7:
     bge L8
     b bad_exit
     L8:
     bne L9
     b bad_exit
     L9:
     //test plus and minus conditions
     mov x1, 8
     subs x2, x0, x1
     bmi L10
     b bad_exit
     L10:
     //these should have same effect
     adds x2, x0, x1
     subs x2, x1, x0
     bpl L11
     b bad_exit
     L11:
     //pl should also branch on zero
     subs x2, x0, 7
     bpl L12
     b bad_exit
     L12:
     //conditional branch instructions
     subs x1, x0, 7
     cbz x1, L13
     b bad_exit
     L13:
     subs x1, x0, 6
     cbnz x1, L14
     b bad_exit
     L14:
     
/********************
    * Exit syscall
    *********************/
    //x0 should still have 7 in it
    mov x8, #93
    svc 0
     
     
     
     
bad_exit:
   /********************
    * Exit syscall
    *********************/
    mov x0, 1
    mov x8, #93
    svc 0
