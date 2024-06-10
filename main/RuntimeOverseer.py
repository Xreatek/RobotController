import robomaster.camera as CamResolution

import threading
import queue
import collections
import time

from Enums import *
import Controller
import Observer

class Settings:
    def __init__(self) -> None:
        self.ConnectionType = ConnType.ExternalRouter
        self.RobotIp = None #None or ip string
        self.HostIp = "192.168.2.28" #None or ip string
        
        self.Speed = 50 #rpm (keep in mind angle and speed are calculated the same)
        self.AngleSpeed = 25
        self.Visualize = True
        
        self.StreamRes = CamResolution.STREAM_540P
        self.DisplayRawStream = False
        

class GlobalVariables:
    def __init__(self) -> None:
        self.runState = threading.Event()
        self.runState.set()
        self.ConnState = threading.Event()
        
        #Command Vars 
        self.RoCmd = collections.deque(maxlen=1) #max queue size of 1 so no backingup
        self.RoCmdArgs = collections.deque(maxlen=1) #use lists for multiple
        self.RoDone = threading.Event() #able to recieve new commands and not busy with prev
        self.RoDone.set() #default true
        
        #Stream Vars
        self.ImgStream = collections.deque(maxlen=1)

class ThreadMasterClass:
    def __init__(self) -> None:
        self.Settings = Settings()
        self.GlobalVars = GlobalVariables()
        
        print('Starting robot controller')
        self.RobotController = threading.Thread(target=Controller.RobotInterface, args=[self.Settings, self.GlobalVars])
        self.RobotController.start() #make monitor that restarts interface when it crashes
        try:
            self.GlobalVars.ConnState.wait(timeout=30)
        except Exception as e:
            print(f'Problem waiting for connection to be made. | {e}')
            exit(503) #connection problems error code
        print('Controller running')
        
        #self.GlobalVars.RoCmdArgs.append(90); self.GlobalVars.RoCmd.append(ControllCMDs.Rotate) #90 degree rotation test
        
        #starting observer
        self.Observer = threading.Thread(target=Observer.AiObserver, args=[self.Settings, self.GlobalVars])
        self.Observer.start()
        
        #makes sure sdk keeps running
        self.Reviver()
    
    def Reviver(self):
        while self.GlobalVars.runState.is_set():
            InterfaceAlive = self.RobotController.isAlive()
            #print(f'Interface state: {InterfaceAlive}')
            if not InterfaceAlive:
                print("Restarting Controller Thread")
                self.RobotController = threading.Thread(target=Controller.RobotInterface, args=[self.Settings, self.GlobalVars])
                self.RobotController.start() #make monitor that restarts interface when it crashes
            time.sleep(0.1)
        

if __name__ == "__main__":
    import sys
    sys.setrecursionlimit(1000000000) #dont ask...
    print(sys.getrecursionlimit()) #I promise it's not my fault...
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
#if in search mode (optional: wandering)
#   waits for new camera frame
#   then if something is found it calculates the rotation angle and sends that as a command to the robot as angle to turn (mean while no updates to camera(maybe))
#   !once rotated as calculated mode is set to confirm mode 

#elif in confirm mode 
#   crop to only see directly infront of robot if something
#   if paper is detected then: slowly move forward
#       When paper is lost set arm into grabbing mode
#       !then mode is set to preGrabConfirmMode
#   else (if no paper is detected in crop mode)
#       !mode is set to search mode

#elif in preGrabConfirmMode
#   check if paper is still detected and right infront of the robot
#   if not^ then correct rotation until paper is right infront of the camera
#   !when succeeded go into grabbing mode  

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