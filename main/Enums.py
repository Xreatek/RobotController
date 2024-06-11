from enum import Enum
#conn
class ConnType(Enum):#id
    InternalRoutor = 1
    ExternalRouter = 2
    
class OpTypes(Enum):#id
    AI = 0
    Human = 1

class AiMode(Enum):#id
    Searching = 0
    Found = 1 
    EnRoute = 2 
    PickingUp = 3
    HoldCheck = 4
    ReturnCarry = 5
    DropCheck = 6

class ControllCMDs(Enum):#amt of vars passed
    Waiting = None #(internal)
    Rotate = lambda a:f'chassis move z {a} z_speed 50;' #RotateDegrees; 1 arg
    
    
    #ArmGrab = 0
    #ArmTransport = 0
    #ClawClose = 0
    #ClawOpen = 0
    
#print(ControllCMDs.Rotate(5, 50))