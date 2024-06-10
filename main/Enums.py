from enum import Enum
#conn
class ConnType(Enum):#id
    InternalRoutor = 1
    ExternalRouter = 2
    
class ArmCommands(Enum):#id
    ArmStill = 0
    ArmGrab = 1
    ArmTransport = 2 
    ArmClose = 3
    ArmOpen = 4
    
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
    Waiting = 0 #(internal)
    Rotate = 1 #RotateDegrees
    