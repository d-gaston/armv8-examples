.global _start

_start:

main:

    mov x0, 2
    mov x1, 5
    ldr x2, =data
    
    //use x4 as offset register
    mov x4, 0x10
    
    //str/ldr 
    str x0, [x2]
    ldr x0, [x2]
    //str/ldr imm offset 
    str x0, [x2, 0x10]
    ldr x0, [x2, 0x10]
    //str/ldr reg offset 
    str x0, [x2, x4]
    ldr x0, [x2, x4]
    
    //str/ldr pre/post indexing
    mov x3, x2
    str x0, [x2, 8]!
    str x1, [x2, 8]!
    ldr x1, [x2], -8
    ldr x0, [x2], -8
    str x0, [x2], 8
    str x1, [x2], 8
    ldr x1, [x2, -8]!
    ldr x0, [x2, -8]!
    //x2 should be back to original
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
