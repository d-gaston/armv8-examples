import armsim
#run instruction tests
import instruction_tests
import sys
from io import StringIO,BytesIO



  
'''
Full program tests in /tests directory
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

with open('tests/ldp_stp_test.s','r') as f:
	armsim.parse(f.readlines())
armsim.run()
assert armsim.reg['x0'] == 7, "ldp_stp_test returned incorrect value of {}".format(armsim.reg['x0'])
armsim.reset()

with open('tests/ldr_str_test.s','r') as f:
	armsim.parse(f.readlines())
armsim.run()
assert armsim.reg['x0'] == 7, "ldr_str_test returned incorrect value of {}".format(armsim.reg['x0'])
armsim.reset()

with open('tests/brk_test.s','r') as f:
	armsim.parse(f.readlines())
armsim.run()
assert armsim.reg['x0'] == 7, "brk_test returned incorrect value of {}".format(armsim.reg['x0'])
armsim.reset()




'''
Test the sort program
'''
with open('sort.s','r') as f:
    armsim.parse(f.readlines())
original = armsim.getdata('array')
armsim.run()
assert armsim.getdata('array') == sorted(original), "incorrect result produced after running sort.s"
armsim.reset()  


'''
collatz.s is currently the most complex program, so it's 
worth having an automated test to make sure it's working
'''
#use StringIO to drive collatz program
stdin = sys.stdin

sys.stdout = StringIO()
#supress stdout
stdout = sys.stdout

with open('collatz.s','r') as f:
    armsim.parse(f.readlines())

sys.stdin = StringIO('37')
armsim.run()
assert armsim.reg['x0'] == 22, "collatz of 37 should not be {}".format(armsim.reg['x0'])

armsim.reset()





'''
Tests for check_static_rules()
'''
with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
    
#test forbid_loops flag
armsim.forbid_loops = True
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error with collaz.s when loops forbidden"
except ValueError:
    #expected
    armsim.reset()

#test forbid_recursion flag
with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
armsim.forbid_recursion = True
try:
    sys.stdin = StringIO('37')
    armsim.run()
    assert False, "should raise error with collaz.s when recursion forbidden"
except ValueError:
    #expected
    armsim.reset()
      
#test require_recursion flag
with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
armsim.require_recursion = True
try:
    sys.stdin = StringIO('37')
    armsim.run()
    #expected
    armsim.reset()
except ValueError:
    assert False, "should NOT raise error with collaz.s when recursion required"
 
#forbidden instructions
with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
armsim.forbidden_instructions = {'mov'}
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error with collaz.s when mov instr forbidden"
except ValueError:
    #expected
    armsim.reset()
#duplicate labels
with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
armsim.asm.append('duplicate_label:')
armsim.asm.append('duplicate_label:')
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error when duplicate labels added"
except ValueError:
    #expected
    armsim.reset()
 

#branch to label that doesn't exist
with open('collatz.s','r') as f:
    armsim.parse(f.readlines())
armsim.asm.append('b not_a_label_in_program')
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error nonexistent label in branch"
except ValueError:
    #expected
    armsim.reset()

#restore to std io
sys.stdin = stdin
sys.stdout = stdout
  
  
