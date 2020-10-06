import armsim

'''
This procedure executes a single line in isolation and puts the result
(if any) in x0. This is checked against the result parameter. "Isolation"
means that we assume that we can't use the results in one test in another test
Thus the branch instructions can't be tested with this procedure.
Up to 3 values can be passed in to put into operand registers. These will
go in x1, x2, and x3. Additionally arguments for flags can be passed in.
Note that more complex instructions (i.e. ones that hit memory or ones
with dependencies on prior sequences will be tested with integration tests
TODO: make identifying failing test in output easier 
'''
def check(line:str, result:int, x1=0,x2=0,x3=0, zeroFlag = False, negFlag = False):
	armsim.reg['x1'] = x1; armsim.reg['x2'] = x2; armsim.reg['x3'] = x3;
	armsim.execute(line)
	assert armsim.reg['x0'] == result, \
	"Expected result {} not equal to actual result {}\n\tLine executed: {}".format(result,armsim.reg['x0'],line)
	assert armsim.z_flag == zeroFlag, "Zero flag should not be {} after executing {}".format(zeroFlag,line) 
	assert armsim.n_flag == negFlag, "Negative flag should not be {} after executing {}".format(negFlag,line)
	armsim.reset()

check('mov x0, #1',result = 1)
check('mov x0, x1',result = 1, x1 = 1)

check('add x0, x1, x1', result = 2, x1 = 1)
check('adds x0, x1, x1', result = 0, x1 = 0, zeroFlag = True)
check('adds x0, x1, x1', result = -2, x1 = -1, negFlag = True)
check('add x0, x1, #1', result = 2, x1 = 1)
check('adds x0, x1, #0', result = 0, x1 = 0, zeroFlag = True)
check('adds x0, x1, #-1', result = -2, x1 = -1, negFlag = True)

check('sub x0, x1, x2', result = 1, x1 = 2, x2 = 1)
check('subs x0, x1, x1', result = 0, x1 = 1, zeroFlag = True)
check('subs x0, x1, x2', result = -1, x1 = 1, x2 = 2, negFlag = True)
check('sub x0, x1, #1', result = 1, x1 = 2)
check('subs x0, x1, #1', result = 0, x1 = 1, zeroFlag = True)
check('subs x0, x1, #2', result = -1, x1 = 1, negFlag = True)

check('asr x0, x1, #1', result = 1, x1 = 2)
check('asr x0, x1, #6', result = 1, x1 = 64)

check('lsl x0, x1, #1', result = 2, x1 = 1)
check('lsl x0, x1, #3', result = 80, x1 = 10)

check('mul x0, x1, x1', result = 100, x1 = 10)
check('udiv x0, x1, x2', result = 10, x1 = 100, x2 = 10)
check('udiv x0, x1, x2', result = 10, x1 = 101, x2 = 10)

check('cmp x1, #1',result = 0, x1 = 0, zeroFlag = False, negFlag = True)
check('cmp x1, #1',result = 0, x1 = 1, zeroFlag = True, negFlag = False)
check('cmp x1, #1',result = 0, x1 = 2, zeroFlag = False, negFlag = False)
