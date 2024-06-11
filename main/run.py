import threading as td
import queue
import traceback
import pygame
import cv2 as cv
from random import randint
import time
import json

import robomaster.action
import robomaster.robot

from Enums import *
import robomaster
from robomaster import led
from robomaster import chassis
from robomaster import camera as RMCam
from robomaster import robot as SeeRoFunction
import RobotConn as RobotConnMod
from robomaster import exceptions

#loading AI

#Loaded AI

#start logging
#robomaster.enable_logging_to_file()

#SETTINGS
class ConfigClass:
    def __init__(self):
        self.ConnectionType = ConnType.ExternalRouter
        self.Opperator = OpTypes.Human
        self.NormalSpeed = 40 #rpm (keep in mind angle and speed are calculated the same)
        self.FastSpeed = 160
        self.TurnAngle = 80 #turning rpm
        self.SlowAngle =  25
        self.ArmSpeed = 1
        
        #safety settings
        self.SafeMode = True
        self.MaxRPM = 225 #be carefull please..
        
        #unstable options
        self.FrameMissingReconn = 5 #amount of times queue can be empty before reconnection
        self.FPSRecon = 15
        self.ReconTimeout = 8
        self.FPSCap = 10
        self.CamWin = True #when ai you wouldnt poke out their eyes right..?
        self.ResizeMainFBFeed = True

sett = ConfigClass()

runnin = td.Event()
runnin.set()

RoConn = RobotConnMod.Connection(runnin, sett.ConnectionType, sett) #not sure if runin will trigger globally if stored in class
robot = RoConn.me #get the robot

#modules are initialized
pygame.init()

class window:
    def __init__(self):
        self.MaxYDim = 720
        self.MaxXDim = 1280
        
        self.s = pygame.display.set_mode((self.MaxXDim, self.MaxYDim))

screen = window()

clock = pygame.time.Clock()

#set default values
ToldToStop, FirstCamFrame, NewFrame, ReconnState, ArmChanged = False, False, False, False, False
ArmBusy, ArmCmd, ReConnTimeout, FrameTry = False, 0, (time.time()+sett.ReconTimeout), 0
pw1, pw2, pw3, pw4 = 0, 0, 0, 0 #movement values
w1, w2, w3, w4 = 0, 0, 0, 0 #prev movement vals

robot.led.set_led(comp=led.COMP_ALL, r=randint(1, 150), g=randint(1, 150), b=randint(1, 150), effect=led.EFFECT_ON) #test conn with leds

#subscribe functions
def GetPerc(procent, s):
        s.procent = procent
        
def GetPos(ChasisC, s):
    s.CY_pos = ChasisC[0]
    s.CX_pos = ChasisC[1]
    #print(f'Y_pos: {str(ChasisC[0])}, X_pos: {str(ChasisC[1])}')
    
def GetArmPos(ArmC, s):
    NegGlitchZero = 4294967297 #this is because of a glitch cuz the moron developers of this 💩 sdk are using a unsigned int for coordinates
    NegDetect = 2147483648 #2^31 so it will catch negative numbers
    if ArmC[0] > NegDetect: 
        s.AX_pos = ArmC[0] - NegGlitchZero
    else:
        s.AX_pos = ArmC[0]
        
    if ArmC[1] > NegDetect:
        s.AY_pos =  ArmC[1] - NegGlitchZero
    else:
        s.AY_pos = ArmC[1]
    #print(f'Arm_Y:{s.AY_pos}, Arm_X:{s.AX_pos}')

class SubbedIntrFuncClass:
    def __init__(s, RoConn, sett):
        s.procent = int() #battery procentage
        s.CY_pos = float()
        s.CX_pos = float()
        s.AY_pos = float()
        s.AX_pos = float()
        
        #subscribe Subscriber functions 
        #make sure to re-sub after restart
        RoConn.me.battery.sub_battery_info(1,GetPerc, s)
        RoConn.me.chassis.sub_position(0, 1, GetPos, s)
        RoConn.me.robotic_arm.sub_position(1, GetArmPos, s)
        
SubVals = SubbedIntrFuncClass(RoConn, sett)
#RoArm = RoConn.me.robotic_arm
#RoArm.sub_position(5, GetArmPos, SubVals)


#Functions
def RoReConn(OldRoConn, ReconnState, sett):
    if not ReconnState:
        try:
            if sett.CamWin:
                OldRoConn.cam.stop_video_stream()
            ReconnState = True
            print('Reconnecting')
            ReconTime = time.time()
            #RoLed.set_led(comp=led.COMP_ALL, r=255, g=0, b=0, effect=led.EFFECT_ON)
            #robot.reset_robot_mode()
            RoConn = RobotConnMod.RobotCloseOldAP(OldRoConn)
            OldRoConn = None
            #Reseting all variables
            RoConn = RobotConnMod.Connection(runnin, sett.ConnectionType, sett) 
            robot = RoConn.me
            #robot.led.set_led(comp=led.COMP_ALL, r=5, g=240, b=20, effect=led.EFFECT_ON)
            robot.led.set_led(comp=led.COMP_ALL, r=randint(1, 200), g=randint(1, 200), b=randint(1, 200), effect=led.EFFECT_ON) #test conn with leds
            #robot.reset()
            print(f"Reconnected! Took {str(time.time()-ReconTime)} sec.")
            ReconnState = False
            SubVals = SubbedIntrFuncClass(RoConn, sett)
            return RoConn, robot, SubVals
        except Exception as e:
            print(f'RoReConn Func Error! | {e}')
            runnin.clear()
            

#def GetPro(pro):
#    print(pro)
#
#RoBat.sub_battery_info(1,GetPro)

#fun
ArmY, ArmX, Claw = 0, 0, 0
PArmY, PArmX, PClaw = 0,0,0

#Arm Movements
def ArmCarry(RoConn):
    #SeeRoFunction.robotic_arm.RoboticArm.moveto(0,0).wait_for_completed(timeout=10)
    RoConn.me.robotic_arm.moveto(120,40).wait_for_completed(timeout=3)
    cf = RoConn.cam.read_cv2_image(strategy="newest", timeout=4) #removes fragmentation
    
def OpenHand(RoConn, Power=100):
    #SeeRoFunction.gripper.Gripper.open(0)
    RoConn.me.gripper.open(Power)
    
def CloseHand(RoConn, Power=500):
    #SeeRoFunction.gripper.Gripper.close()
    RoConn.me.gripper.close(Power)
    
def ArmPickUp(RoConn):
    RoConn.me.robotic_arm.moveto(180,0).wait_for_completed(timeout=3) #Y,X
    cf = RoConn.cam.read_cv2_image(strategy="newest", timeout=4) #removes fragmentation
    RoConn.me.robotic_arm.moveto(180,-90).wait_for_completed(timeout=3) #Y,X 
    cf = RoConn.cam.read_cv2_image(strategy="newest", timeout=4) #removes fragmentation

try:
    RoConn.me.robotic_arm.moveto(120,40).wait_for_completed(timeout=3)
    #robot.robotic_arm.moveto(120,-50).wait_for_completed(timeout=4) possible search mode
except Exception as e:
    print("Arm Cordinates too much", e)
#RoConn.ConFree.set()
while runnin.is_set():
    print("WhileLoop")
    if sett.CamWin:
        try:
            #print("getting image")
            #cf = RoConn.cam.Re(timeout=1 , strategy='newest') #camera stream
            cf = RoConn.cam.read_cv2_image(strategy="newest", timeout=4) #image taken
            #self.ConFree.set()
            ecf = cv.cvtColor(cf, cv.COLOR_BGR2RGB)
            if sett.ResizeMainFBFeed:
                ecf = cv.resize(ecf, (screen.MaxXDim, screen.MaxYDim))
            CamImg = pygame.image.frombuffer(ecf, (screen.MaxXDim, screen.MaxYDim),"RGB")
            if FirstCamFrame:
                FirstCamFrame = False
            screen.s.blit(CamImg, (0,0))
            #print("done w image")
        except Exception as e:
            print(f'FrameQueue Error:{e}, Trace: {traceback.format_exc()}')
            if not FirstCamFrame and FrameTry >= sett.FrameMissingReconn:
                FrameTry = 0
                RoConn, robot, SubVals = RoReConn(RoConn, ReconnState, sett)
                ReConnTimeout = (time.time()+sett.ReconTimeout) #resetting timeout for fps drop detection
            else:
                FrameTry += 1
                if sett.Opperator == OpTypes.AI:
                    RunAiFrame = False #Run Ai This Frame? disable
        FrameTry = 0
        
    #Ai movement things yeah
    
#    if sett.Opperator == OpTypes.AI and RunAiFrame:
#        try:
#            print("Ai Vision")
#
#            #if CurrentAiMode == AiMode.Searching:
#                print("searching")
#                #here ai detect
#                results = model(cf, stream=True)
#                # coordinates
#                for r in results:
#                    boxes = r.boxes
#
#                    for box in boxes:
#                        # bounding box
#                        print(box)
#                        x1, y1, x2, y2 = box.xyxy[0]
#                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values
#
#                        # put box in cam
#                        cv.rectangle(cf, (x1, y1), (x2, y2), (255, 0, 0), 3)
#
#                        # confidence
#                        #confidence = math.ceil((box.conf[0]*100))/100
#                        #print("Confidence --->",confidence)
#
#                        # class name
#                        #cls = int(box.cls[0])
#                        #print("Class name -->", classNames[cls])
#
#                        # object details
#                        org = [x1, y1]
#                        font = cv.FONT_HERSHEY_SIMPLEX
#                        fontScale = 1
#                        color = (255, 0, 0)
#                        thickness = 2
#
#                        #cv.putText(cf, classNames[cls], org, font, fontScale, color, thickness)
#
#                cv.imshow('Webcam', cf)
#                cv.waitKey(1)
#        except Exception as e:
#            print(f'Ai had exception: {e}')
#            continue    
    
    #End of Ai movement things... yeah    

    #RoArm.moveto( x=0 , y=0 )
    #WKey, AKey, SKey, DKey = False, False, False, False
    mk = 0 #(pressed movement keys)
    #poll events
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: #window closed
            print("Window Closed")
            runnin.clear()
            
    #setting keyboard
    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_ESCAPE]:
        print("Escape Pressed")
        runnin.clear()
    #keys.index(pygame.K_w)
    #keys for switch statement could add pressed keys to list then itterate over list length and use switch to find the appropriate response for the pressed key
    WKey = keys[pygame.K_w]
    if WKey: mk += 1
    DKey = keys[pygame.K_d]
    if DKey: mk += 1
    AKey = keys[pygame.K_a]
    if AKey: mk += 1
    SKey = keys[pygame.K_s]
    if SKey: mk += 1
    mk = WKey+DKey+AKey+SKey
    #angle keys
    LAngleKey = keys[pygame.K_LEFT]
    RAngleKey = keys[pygame.K_RIGHT]
    
    SideKeys = LAngleKey+RAngleKey
    if mk == 0 and SideKeys>0:
        mk = 1
    #Toggle Keys
    SlowTurn = keys[pygame.K_LCTRL]
    FastMove = keys[pygame.K_LSHIFT]
    
    #info keys
    PowerRead = keys[pygame.K_p]
    if PowerRead:
        print(f"Current power procentage: {str(SubVals.procent)}%")
        #RoConn.ConFree.wait()
        #RoConn.ConFree.clear()
        #RoArm.moveto(x=0, y=80).wait_for_completed()
        #RoConn.ConFree.set()
        #ArmY, ArmX, Claw = 0, 0, 0
        
    ReConnKey = keys[pygame.K_m]
    if ReConnKey:
        RoConn, robot, SubVals = RoReConn(RoConn, ReconnState, sett)
        ReConnTimeout = (time.time()+sett.ReconTimeout) #resetting timeout for fps drop detection        

    
    if keys[pygame.K_1]:
        print("OpenHand")
        OpenHand(RoConn)
        
    if keys[pygame.K_2]:
        print("CloseHand")
        CloseHand(RoConn)
    
    if keys[pygame.K_3]:
        print("Carry Arm")
        ArmCarry(RoConn)
    
    if keys[pygame.K_4]:
        print("PickUp Arm")
        ArmPickUp(RoConn)   
    
    #Chasis movement
    if mk > 2:
        print("Too many keys pressed")
    elif mk <= 0:
        if ToldToStop == False:
            try:
                #print("stopmove")
                #RoConn.ConFree.wait()
                #RoConn.ConFree.clear()
                print('Run Stop command')
                robot.chassis.drive_wheels(0,0,0,0, timeout=3)
                print('Done Stop command')
                #RoConn.ConFree.set()
                ToldToStop = True
            except Exception as e:
                print("Could not send command.")
                ToldToStop = False
    else:
        w1, w2, w3, w4 = 0, 0, 0, 0
        #print("key states"+str(WKey)+str(AKey)+str(SKey)+str(DKey)+str(mk))
        
        #correcting for wheel resistance
        offset = mk 
        if mk > 1:
            offset = 1.6
        
        if FastMove:
            MoveSpeed =  sett.FastSpeed
        else:
            MoveSpeed = sett.NormalSpeed
            
        if SlowTurn:
            AngleSpeed = sett.SlowAngle
        else:
            AngleSpeed = sett.TurnAngle
        
        if WKey: #w1 = Upper Right, w2= Upper Left, w3 = Lower Left, w4 = Lower Right (from back view of robot)
            w1 += MoveSpeed/offset
            w2 += MoveSpeed/offset
            w3 += MoveSpeed/offset
            w4 += MoveSpeed/offset
        if AKey: #up = + down = - (test if this actually works)
            w1 += MoveSpeed/offset #outward up
            w2 += 0-(MoveSpeed/offset)  #inward down
            w3 += MoveSpeed/offset #inward up
            w4 += 0-(MoveSpeed/offset) #outward down
        if DKey:
            w1 += 0-(MoveSpeed/offset)
            w2 += MoveSpeed/offset
            w3 += 0-(MoveSpeed/offset)
            w4 += MoveSpeed/offset
        if SKey:
            w1 += 0-MoveSpeed/offset
            w2 += 0-MoveSpeed/offset
            w3 += 0-MoveSpeed/offset
            w4 += 0-MoveSpeed/offset
        
        if LAngleKey:#w1 = Upper Right, w2= Upper Left, w3 = Lower Left, w4 = Lower Right (from back view of robot)
            w1 += AngleSpeed/offset #L
            w4 += AngleSpeed/offset
            w2 += 0-AngleSpeed/offset #R
            w3 += 0-AngleSpeed/offset
        if RAngleKey:#w1 = Upper Right, w2= Upper Left, w3 = Lower Left, w4 = Lower Right (from back view of robot)
            w1 += 0-AngleSpeed/offset #L
            w4 += 0-AngleSpeed/offset
            w2 += AngleSpeed/offset #R
            w3 += AngleSpeed/offset
        
        if ((pw1 != pw1+w1) or (pw2 != pw2+w2) or (pw3 != pw3+w3) or (pw4 != pw4+w4)):#if movement values are different from last frame
            if sett.SafeMode: #saftey
                if w1 > sett.MaxRPM:
                    pw1 = w1
                    w1 = sett.MaxRPM
                    Warning("Wheel RPM is going over safety limit!")
                if w2 > sett.MaxRPM:
                    pw2 = w2
                    w2 = sett.MaxRPM
                    Warning("Wheel RPM is going over safety limit!")
                if w3 > sett.MaxRPM:
                    pw3 = w3
                    w3 = sett.MaxRPM
                    Warning("Wheel RPM is going over safety limit!")
                if w4 > sett.MaxRPM:
                    pw4 = w4
                    w4 = sett.MaxRPM
                    Warning("Wheel RPM is going over safety limit!")
                    
                
            ToldToStop = False
            #print("URW"+str(w1)+", ULW:"+str(w2)+", LLW:"+str(w3)+", LRW:"+str(w4))
            MoveRedo = time.time()+10
            
            #RoConn.ConFree.wait()
            #RoConn.ConFree.clear()
            robot.chassis.drive_wheels(w1,w2,w3,w4, timeout=3)
            #robot.action_dispatcher.get_msg_by_action
            #RoConn.ConFree.set()
            #robot.chassis.drive_speed(x,y,z, timeout=0)#x(Forward) y(Diagonal) z(Gay), seconds
            pw1, pw2, pw3, pw4 = w1, w2, w3, w4
            w1, w2, w3, w4 = 0, 0, 0, 0 #sets them at begin of movement
        #elif (time.time() > MoveRedo):
        #    MoveUpdate = time.time()+4
        #    robot.chassis.drive_speed(px,py,pz, timeout=0)
            
    #(After events fired!) load things to show in window
    
    #print(clock.get_fps())
    if (clock.get_fps() <= sett.FPSRecon) and (time.time() > ReConnTimeout):
        robomaster.action.registered_actions.clear()
    #    RoConn, robot, SubVals = RoReConn(RoConn, ReconnState, sett)
    #    ReConnTimeout = (time.time()+sett.ReconTimeout) #resetting timeout for fps drop detection
    pygame.display.update()
    clock.tick(sett.FPSCap)  # limits FPS to 30
    RunAiFrame = True
    #print("ticked")
#if sett.CamWin:
#    FrameQueue.task_done()
print("Main Stopping")

RoConn.cam.stop_video_stream()

runnin.clear()
robot.led.set_led(comp=led.COMP_ALL, r=5, g=5, b=0, effect=led.EFFECT_ON)
robot.close()

pygame.display.quit()
pygame.quit()