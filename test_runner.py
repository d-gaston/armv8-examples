import armsim
#run instruction tests
import instruction_tests
import sys
from io import StringIO,BytesIO


with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
#automatic stdin input/supress stdout
stdin = sys.stdin
stdout = sys.stdout
sys.stdout = StringIO()
sys.stdin = StringIO('37')
armsim.run()
assert armsim.reg['x0'] == 22, "collatz of 37 should not be {}".format(armsim.reg['x0'])
sys.stdin = stdin
sys.stdout = stdout

armsim.reset()



'''
exit code in x0 for all test cases should be 7
'''
with open('tests/arithmetic_test.s','r') as f:
	armsim.parse(f.readlines())
armsim.run()
assert armsim.reg['x0'] == 7, "arithmetic_test returned incorrect value of {}".format(armsim.reg['x0'])
armsim.reset()
with open('tests/branch_test.s','r') as f:
	armsim.parse(f.readlines())
armsim.run()
assert armsim.reg['x0'] == 7, "arithmetic_test returned incorrect value of {}".format(armsim.reg['x0'])
armsim.reset()


