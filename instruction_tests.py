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
'''
def check(line:str, result:int, x1=0,x2=0,x3=0, zeroFlag = False, negFlag = False):
	armsim.reg['x1'] = x1; armsim.reg['x2'] = x2; armsim.reg['x3'] = x3;
	armsim.execute(line)
	assert armsim.reg['x0'] == result, \
	"Expected result {} not equal to actual result {}\n\tLine executed: {}".format(result,armsim.reg['x0'],line)
	assert(armsim.z_flag == zeroFlag)
	assert(armsim.n_flag == negFlag)
	armsim.reset()

check('mov x0, 1',result = 1)
check('mov x0, x1',result = 1, x1 = 1)

check('add x0, x1, x1',result = 2, x1 = 1)
check('adds x0, x1, x1',result = 2, x1 = 1)
