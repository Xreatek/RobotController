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
    Found = 1 #unnecessary
    EnRoute = 2 
    PickingUp = 3
    HoldCheck = 4
    ReturnCarry = 5
    DropCheck = 6

class ControllCMDs(Enum):
    Waiting = None #(internal)
    Rotate = lambda a:f'chassis move z {a[0]} z_speed 50;' #RotateDegrees; 1 arg
    WheelMove = lambda a:f'chassis wheel w1 {a[0]} w2 {a[0]} w3 {a[0]} w4 {a[0]};'
    
    
    #ArmGrab = 0
    #ArmTransport = 0
    #ClawClose = 0
    #ClawOpen = 0
    
#print(ControllCMDs.Rotate(5, 50))