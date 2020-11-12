import armsim
def printx1():
    print(armsim.reg['x1'])

armsim.linked_labels['printx1:']=printx1
armsim.main()
