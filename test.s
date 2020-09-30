main:
mov x0,32
mov x1,24
.WHILE:
    SUB X2,X0,X1
    CBZ X2,.END
.IF:
    CMP X1,X0
    B.GT .ELSE
    SUB X0,X0,X1
    B .WHILE
.ELSE:
    SUB X1,X1,X0
    B .WHILE
.END:
    SVC 0
