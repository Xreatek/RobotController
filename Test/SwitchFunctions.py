import logging
from enum import Enum
import enum

logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

def create_switch(*args): #Each case: [Enum, Func]
    _Switch_Dict = dict()
    for a in args:
        _Switch_Dict[a[0]] = a[1]#asigning function too dict key/given enum
    return _Switch_Dict
        
def run_switch(i, _Switch_dict, *args, **kwargs):
    _Switch_dict.get(i, lambda: logging.error("Switch: Outside range!"))(*args, **kwargs)

#test user code
if __name__ == '__main__':
    def f1(lala=1): print(f"function 1 printed {lala}")
    def f2(balin): print(f"function 2 printed {balin}")#this will error though since no value is attached 
    def f3(testing, multiple, variables="works"): print(f"function 3 printed {testing} {multiple} {variables}")
    def f4(): print("function 4 printed")

    class enm(Enum): f1 = 1; f2 = 2; f3 = 3; f4 = 4;

    SwitchEnum = create_switch([enm.f1, f1], [enm.f2, f2], [enm.f3, f3], [enm.f4, f4]) #way 1
    SwitchInt = create_switch([1, f1], [2, f2], [3, f3], [4, f4]) #way 2
    
    print(f'#1 Switch can use enums: {SwitchEnum} or you can use #2 interger: {SwitchInt} BUT do NOT use them together.')
    #way 1    
    run_switch(enm.f1, SwitchEnum)
    run_switch(enm.f2, SwitchEnum, "should'nt use empty")
    run_switch(enm.f3, SwitchEnum, "it", "just")
    run_switch(enm.f3, SwitchEnum, 1, 2, 3)
    #way 2
    run_switch(1, SwitchInt)
    run_switch(2, SwitchInt, "should'nt use empty")
    run_switch(3, SwitchInt, "it", "just")
    run_switch(3, SwitchInt, 1, 2, 3)
    
    
    
    