.text
.global _start

_start:

main:
    
    
    ldr x0, =array
    ldr x1, =array_len
    bl sort
    ldr x0, =sorted
    ldr x1, =array_len
    bl sort
    ldr x0, =reverse
    ldr x1, =array_len
    bl sort
    ldr x0, =nearly_sorted
    ldr x1, =array_len
    bl sort
    
    //put a breakpoint here and examine array; it should be sorted
    mov x8, 93
    svc 0 
    

    

 /*************************
  *  Insertion sort (from https://en.wikipedia.org/wiki/Insertion_sort)
  *  i ← 1
  *  while i < length(A)
  *      x ← A[i]
  *      j ← i - 1
  *      while j >= 0 and A[j] > x
  *          A[j+1] ← A[j]
  *          j ← j - 1
  *      end while
  *      A[j+1] ← x
  *      i ← i + 1
  *  end while
  *  x0 : addr of array
  *  x1 : len of array
 *************************/    
sort:
    /******************
     * Correspondences: 
     * x0 : A
     * x1 : length(A)
     * x2 : i
     * x3 : j
     * x4 : x
     * x5 : A[j]
     * x6 : j + 1
     * NB. indexes must be multiples of 8, since that is the size of
     * an integer. Languages like C take care of this detail for you,
     * allowing you to seamlessly use 3 to refer to the 4th element.
     ******************/
    //i ← 1 
    mov x2, 8
    
    
    .loop:
    
        //x ← A[i]
        ldr x4, [x0, x2]
        
        //j ← i - 1
        subs x3, x2, 8
        
        ..loop:
            //while j >= 0 and A[j] > x
	        //flag is set when subtracting from j
            bpl .true
            b .end
            .true:
            ldr x5, [x0, x3]
            cmp x5, x4
            ble .end
            
            //A[j+1] ← A[j]
            add x6, x3, 8
            str x5, [x0, x6]
            
            //j ← j - 1
            subs x3, x3, 8
            
            b ..loop
            .end:
         
        //A[j+1] ← x
        add x6, x3, 8
        str x4, [x0, x6]
             
        //i ← i + 1
        add x2, x2, 8
        
        //while i < length(A)
        cmp x2, x1
        blt .loop

    ret

.data
array: .8byte 9,0,3,8,6,2,7,1,4,5
array_len = . - array
sorted: .8byte 0,1,2,3,4,5,6,7,8,9
reverse: .8byte 9,8,7,6,5,4,3,2,1,0
nearly_sorted: .8byte 9,1,2,3,4,5,6,7,8,0
