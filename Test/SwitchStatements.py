import logging


def Func0(extext="Empty..."):
        
    print(f"Function0, {extext}")
    
def Func1(extext="Empty..."):
    print(f"Function1, {extext}")

def Func2(extext="Empty..."):
    print(f"Function2, {extext}")

def switch(i, *args, **kwargs):
    switcher={ #args are values without a key (5) while kwargs are keyed values (i=5)
        0:lambda: Func0(*args, **kwargs),
        1:lambda: Func1(*args, **kwargs),
        2:lambda: Func2(*args, **kwargs),
    }
    switcher.get(i, lambda: print('Invalid switch case input!'))()

switch(0,extext=5)
switch(1)
switch(0,extext="Hello World")
switch(1,"Hello World!") #orderd so it sets the first var of the function
