import armsim
def printx1():
    print(armsim.reg['x1'])

armsim.linked_labels['printx1:']=printx1
#Launch repl. You can now call printx1 by typing
# bl printx1
#armsim.repl()

#or call from a file
with open('external_func_demo.asm','r') as f:
	armsim.parse(f.readlines())
armsim.run()
