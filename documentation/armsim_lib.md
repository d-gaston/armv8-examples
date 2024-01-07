# Using armsim as a Library
--------------------

Although armsim can be used as a standalone command line program, it can also be imported and used in another python program (the main use case for this is an autograder). This document describes basic usage as well as more advanced options.

## Basic usage
--------------------

If the target code is in `my_file.asm`, the following python code performs the necessary setup and executes the program
```python
import armsim
with open('my_file.asm','r') as f:
	armsim.parse(f.readlines())
armsim.run()
```

All parts of the simulator are available for inspection. Most people want to see the values of registers after a program is run. For example, the following snippet runs the code that has been loaded into the simulator and prints out the value in register `x0`:
```python
# after setup
armsim.run()
print(armsim.reg['x0'])
```

If multiple programs are run in the same session, it is important to reset the simulator in between runs. This is done by calling the `reset()` function after the simulator has finished executing:
```python
# after setup
armsim.run()
armsim.reset()
```
`reset()` puts **ALL** variables in the simulator back to their initial state.

**You will need to deal with timeouts separately, armsim does not currently detect infinite loops by default**. 

## Enabling Checks
--------------------
There are a number of checks that armsim can run on the assembly code. These are rules that are enforced on code, allowing you to make assignments like "double a number without using the `mul` instruction." All checks are disabled by default. An exception is thrown in the event than any enabled check is violated. The usage of each check is described in further detail below:

### Forbidden Instructions
Forbidden instructions are stored in a `set`, so simply adding instructions to that set is sufficient to enable this check. No verification of these instructions is done, so ensure that you have spelled the mnemonic correctly.
```python
# prevents programs with the add instruction from being executed
armsim.forbidden_instructions.add('add')
```
### Forbid/Require Recursion
Sometimes it is a useful programming exercise to solve a problem with/without using recursion. Unlike the other checks, this check happens **after** the program is run. 
To forbid recursion:
```python
armsim.forbid_recursion = True
```

To require recursion:
```python
armsim.require_recursion = True
```

### Forbid Loops
This check stops all branch instructions except for `bl` from being used. 
```python
# enables dead code detection
armsim.forbid_loops = True
```
### Check For Dead Code
This check is enabled by setting a boolean variable to `True`. It looks for code following a `ret` or `b` that is not preceded by a label. This is not an exhaustive dead code check, but it covers the most common mistakes students make.
```python
# enables dead code detection
armsim.check_dead_code = True
```
With this check enabled, a program like this will fail to run:
```asm
	mov x0, 1
	ret
	mov x0, 2
```
	

## Calling a Python Function From Assembly
--------------------
This functionality is useful for allowing students to call small debugging functions from the autograder. The following snippets show how you can define a function a function in python and call it from an assembly program:

```python
import armsim
def printx1():
    print(armsim.reg['x1'])

armsim.linked_labels['printx1:']=printx1
with open('external_func_demo.asm','r') as f:
	armsim.parse(f.readlines())
armsim.run()
```
Note that when the label is added to the `linked_labels` dictionary it must include the colon. This is because all labels are stored with their colon, so this detail must be consistent.

external_func_demo.asm:
```asm
main:
	bl printx1
	mov x1, 9
	bl printx1
```
The first call will result in 0 (the default value of a register) being printed out, and the second call will result in 9 being printed out.
