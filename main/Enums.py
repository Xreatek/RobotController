from enum import Enum
#conn
class ConnType(Enum):#id
    InternalRoutor = 1
    ExternalRouter = 2
    
class ArmStates(Enum):
    top = 2
    middle = 1
    down = 0

class AiMode(Enum):#id
    Searching = 0
    Found = 1 #unnecessary
    EnRoute = 2 
    ArmDown = 3
    PickingUp = 4
    HoldCheck = 5
    ReturnCarry = 6
    DropCheck = 7

class ControllCMDs(Enum):
    Waiting = None #(internal)
    Rotate = lambda a:f'chassis move z {a[0]} z_speed 50;' #RotateDegrees; 1 arg
    MoveWheels = lambda a:f'chassis wheel w1 {a[0]} w2 {a[0]} w3 {a[0]} w4 {a[0]};'
    StopWheels = lambda a:f'chassis wheel w1 0 w2 0 w3 0 w4 0;'
    SetArmPos = lambda a:f'robotic_arm moveto x {a[0]} y {a[1]};'
    EnableIR = lambda a:f'ir_distance_sensor measure {a[0]};'
    GetIRDistance = lambda a:f'ir_distance_sensor distance {a[0]} ?;'
    #ArmGrab = 0
    #ArmTransport = 0
    #ClawClose = 0
    #ClawOpen = 0
    
#print(ControllCMDs.Rotate(5, 50))