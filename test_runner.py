import armsim
#run instruction tests
import instruction_tests
import sys
from io import StringIO,BytesIO

'''
collatz.s is currently the most complex program, so it's 
worth having an automated test to make sure it's working
'''
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
    armsim.forbid_loops = False
    
#test forbid_recursion flag
armsim.forbid_recursion = True
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error with collaz.s when recursion forbidden"
except ValueError:
    #expected
    armsim.forbid_recursion = False
      
#test require_recursion flag
armsim.require_recursion = True
try:
    armsim.check_static_rules()
    #expected
    armsim.require_recursion = False  
except ValueError:
    assert False, "check_static_rules should NOT raise error with collaz.s when recursion required"
 
#forbidden instructions
armsim.forbidden_instructions = ['mov']
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error with collaz.s when mov instr forbidden"
except ValueError:
    #expected
    armsim.forbidden_instructions.clear()

#duplicate labels
armsim.asm.append('duplicate_label:')
armsim.asm.append('duplicate_label:')
try:
    armsim.check_static_rules()
    assert False, "check_static_rules should raise error when duplicate labels added"
except ValueError:
    #expected
    armsim.asm.pop()
    armsim.asm.pop()

armsim.reset() 
  
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


