from enum import Enum
#conn
class ConnType(Enum):#id
    InternalRoutor = 1
    ExternalRouter = 2
    
class ArmStates(Enum): #0 = no paper, 1 = holding paper, 2 = grabbing or dropping paper
    top = 2
    middle = 0
    carrying = 1
    downOpen = 2
    downClosed = 1

class AiMode(Enum):#id
    Searching = 0
    Found = 1 #unnecessary
    EnRoute = 2 
    ArmDown = 3
    PickingUp = 4
    HoldCheck = 5
    ReturnCarry = 6
    DropCheck = 7
    
class CamExposure(Enum):
    default = 'default'
    high = 'small'
    medium = 'medium'
    low = 'large'

class ControllCMDs(Enum):
    Waiting = None #(internal)
    Rotate = lambda a:f'chassis move z {a[0]} z_speed 50;' #RotateDegrees; 1 arg
    MoveWheels = lambda a:f'chassis wheel w1 {a[0]} w2 {a[0]} w3 {a[0]} w4 {a[0]};'
    StopWheels = lambda a:f'chassis wheel w1 0 w2 0 w3 0 w4 0;'
    SetArmPos = lambda a:f'robotic_arm moveto x {a[0]} y {a[1]};'
    CamExposure = lambda a:f'camera exposure {a[0].value};' #(use enum) default, small, medium, large
    SensorIR = lambda a:f'ir_distance_sensor measure {a[0]};' #on, off    
    _GetIRDistance = lambda a:f'ir_distance_sensor distance {a[0]} ?;'
    OpenGrip = lambda a:f'robotic_gripper open {a[0]};' #arg = 1-4 closing force
    CloseGrip = lambda a:f'robotic_gripper close {a[0]};' #arg = 1-4 opening force
    #EveryNonLiveComedyShowEver = lambda a:f'sound event applause {a[0]};' #no note needed (arg = int = amt claps)
    
#print(ControllCMDs.Rotate(5, 50))

class GetValueCMDs(Enum):
    GetIRDistance = lambda Args, RetTyp:[ControllCMDs._GetIRDistance, Args, RetTyp] #1: args, 2:expected datatype
    
    
