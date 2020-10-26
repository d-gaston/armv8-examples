.text
.global _start

_start:

main:
    //setup
    mov x0, 2
    mov x1, 5
    ldr x2, =data
    
    //stp/ldp 
    stp x0, x1, [x2]
    ldp x0, x1, [x2]
    //stp/ldp imm offset
    stp x0, x1, [x2, 0x10]
    ldp x0, x1, [x2, 0x10]
    
    //stp/ldp pre/post indexing
    mov x3, x2
    stp x0, x1, [x2, #0x10]!
    ldp x0, x1, [x2], #-0x10
    stp x0, x1, [x2], #0x10
    ldp x0, x1, [x2, #-0x10]!
    //x2 should be unchanged
    cmp x2, x3
    bne error
    
    //if x0 and x1 are unchanged as expected, final result should
    //be 7
    add x0, x0, x1
    mov x8, #93
    svc 0
    
    
    
error:
    mov x0, -1
    mov x8, #93
    svc 0



.bss
data: .space 32
