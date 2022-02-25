# Overview of armsim tests

The main entry point for testing armsim is `test_runner.py`, which is located in the top level directory. This program should be run after any change is made to armsim. If a test fails, the program stops at that test, no further tests are executed.

There are three main types of tests:

+ **Dedicated Test Programs**: These are the tests located in the current directory. `test_runner.py` runs each one and verifies that the return value (the value in the x0 register) is equal to 7 (this value was picked arbitrarily, the important thing is that all tests follow the same convention). Read the comments in these files for further information about these tests.
+ **Instruction Tests**: Runs instructions that don't have memory side effects and checks the results. These are reduntant in terms of testing functionality, but offer a higher granularity than the dedicated test programs or example programs. That way if one of these instructions is broken, it's a bit easier to find. They are located in `instruction_tests.py`, which is itself imported into `test_runner.py`. Because the program stops after a test failure, these are the first tests to run.
+ **Example Program Tests**: These are selected from the programs located in ../examples. Currently, in `test_runner.py`, the two most complex programs, sort.s and collatz.s, are tested for correct output. This increases confidence in the simulator by going beyond the contrived tests in the previous categories. 

`test_runner.py` also verifies the functionality of the static code checks. This is done primarily by turning on each check, then trying to run a program that is known to violate that check. If no such program exists currently, a small modification is made to the in memory representation of the program to make it fail. For instance, to verify that duplicate labels are not accepted, we simply append two duplicate labels to the instruction list.

Note: After each test in `test_runner.py`, the reset() method should be called on armsim in order to keep tests independent.
