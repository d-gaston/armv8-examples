import armsim
#run instruction tests
import instruction_tests



'''
exit code for all programs in  tests/ should be 7
'''
with open('tests/arithmetic_test.s','r') as f:
	armsim.parse(f.readlines())
armsim.run()
assert armsim.reg['x0'] == 7, "arithmetic_test returned incorrect value of {}".format(armsim.reg['x0'])
armsim.reset()

