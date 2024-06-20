import threading
import traceback
import queue
import collections
import time

from Enums import *
import Controller
import Observer

class Settings:
    def __init__(self) -> None:
        self.ConnectionType = ConnType.ExternalRouter
        
        print('0 or 1 make sure the other robot has the opeside value')
        RoID = input() 
        self.robotID = RoID
        
        print('13 or 14')
        _ENDIP = input()
        self.RobotIp = f'10.249.48.{_ENDIP}' #school '192.168.2.7' #None or ip string '10.249.48.13' '10.249.48.14'
        #self.RobotIp = f'10.249.48.13'
        
        #self.RobotIp = '192.168.2.7' #home
        #self.RobotIp = '192.168.28.86' #hotspot 
        
        
        #self.HostIp = '192.168.2.28' #None or ip string
        
        self.RobotPort = '40923'
        
        self.AllowedLostFrames = 10 #how many frames is the ai allowed to not find crumpeld paper before returning to searching
        self.Speed = 50 #rpm only
        self.AngleSpeed = 25
        self.IrFloorDistance = 42 #1~ bellow floor distance used to know if looking at floor :mindblown: (low arm level)
        
        self.InClawNormalized = 0.65 #if picking up too early make this higher if it is missing it while in claw then lower value
        
        self.Visualize = True
        self.DisplayRawStream = False
        self.DataCollector = False #if true AI not activated
        
        self.ReviverEnabled = False #disable for testing

class GlobalVariables:
    def __init__(self) -> None:
        self.runState = threading.Event()
        self.runState.set()
        self.ConnState = threading.Event()
        
        #Command Vars 
        self.RoCmd = collections.deque(maxlen=1) #max queue size of 1 so no backingup
        self.RoCmdArgs = collections.deque(maxlen=1) #use lists for multiple
        
        self.ExpcData = threading.Event() # excpect data if set controller will send data
        self.InterfaceData = queue.Queue(maxsize=1) #controller data tunnel
        
        
        self.RoDone = threading.Event() #able to recieve new commands and not busy with prev
        self.RoDone.set() #default true
        self.WaitForRoStatic = threading.Event()
        
        #Stream Vars
        self.ImgStream = collections.deque(maxlen=2)

class ThreadMasterClass:
    def __init__(self) -> None:
        self.Settings = Settings()
        self.GlobalVars = GlobalVariables()
        
        print('Starting robot controller')
        self.RobotController = threading.Thread(name='RobotController', target=Controller.RobotInterface, args=[self.Settings, self.GlobalVars])
        self.RobotController.start() #make monitor that restarts interface when it crashes
        try:
            self.GlobalVars.ConnState.wait(timeout=30)
        except Exception as e:
            print(f'Problem waiting for connection to be made. | {e}')
            exit(503) #connection problems error code
        print('Controller running')
        
        #starting observer
        self.Observer = threading.Thread(name='Observer', target=Observer.AiObserver, args=[self.Settings, self.GlobalVars])
        self.Observer.start()
        
        #makes sure sdk keeps running or stops it if false when error occurs
        self.Reviver()
    
    def Reviver(self):
        try:
            while self.GlobalVars.runState.is_set():#self.GlobalVars.runState.is_set():
                InterfaceAlive = self.RobotController.is_alive()
                #print(f'Interface state: {InterfaceAlive}')
                if not InterfaceAlive:
                    if self.Settings.ReviverEnabled:
                        print("Stopped interface")
                        #time.sleep(5)
                        print("Restarting Controller Thread")
                        #self.GlobalVars.runState.set()
                        self.RobotController = threading.Thread(target=Controller.RobotInterface, args=[self.Settings, self.GlobalVars])
                        self.RobotController.start() #make monitor that restarts interface when it crashes
                        self.GlobalVars.ConnState.wait(timeout=10)
                        #self.GlobalVars.RoCmdArgs.append(90)
                        #self.GlobalVars.RoCmd.append(ControllCMDs.Rotate)
                    else:
                        print("rip the camera crashed")
                        self.GlobalVars.runState.clear()
            
                time.sleep(0.1)
        except KeyboardInterrupt:
            print('keyboard normal exit from reviver')
            self.GlobalVars.runState.clear()
            self.GlobalVars.ConnState.clear()
        except Exception as e:
            print(f'Error occured in reviver. {e}, Trace: {traceback.format_exc()}')
        print(f'Reviver ended. Runstate: {self.GlobalVars.runState.is_set()}')


if __name__ == "__main__":
    ThreadMasterClass()
        

#name threads so img stream can see if controller is still running if not it will end so runtime can start a new one
#or stream can be replaced to the main controller

#starting connection

#-runtime observer
#√ starts components
#sets robot controlls in a loop to see if it stopped and if true then
#   it will reinstate the robot controlls(observer should not be effected since it will just have to wait a bit longer on its image but no variables should be lost.)
#(if needed same could be done for observer)

#-robot controlls
#√ make connection then return
#√ main robot controller sets up subscribers video stream etc
#√ robot controller in loop waiting for commands and updating current image when ai isnt busy

#-ai observer
#√ waits untill connection is made
#√ if in search mode (optional: wandering)
#√   waits for new camera frame
#√   then if something is found it calculates the rotation angle and sends that as a command to the robot as angle to turn (mean while no updates to camera(maybe))
#√   !once rotated as calculated mode is set to confirm mode 

#√elif in confirm mode 
#!   crop or track to only see directly infront of robot if something
#√   if paper is detected then: slowly move forward
#√       When paper is lost set arm into grabbing mode
#√       !then mode is set to preGrabConfirmMode
#√   else (if no paper is detected in crop mode)
#√       !mode is set to search mode

#√elif in preGrabConfirmMode
#√   check if paper is still detected and right infront of the robot
#√   if not^ then correct rotation until paper is right infront of the camera
#√   !when succeeded go into grabbing mode  

#elif in grabbingMode
#   drive towards paper checking each time if angle is still in acceptable margin of error 
#   if inside margin of error
#       continue forwards untill distance sensor output is close enough or ai camera detects paper inside claw area
#       !then close claw and go to objectRetrival
#   else when outside of margin of error
#       Correct papers angle offset compared to the robots

#elif objectRetrival
#   Set arm into carry mode and move towards paper container
#   if at container align robot with box so it can drop inside
#       when aligned robot will drop held paper
#       then robot rotates 180 degrees
#       !Then robot is set back to search mode