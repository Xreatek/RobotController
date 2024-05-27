import threading as td
import queue
import traceback
import pygame
from random import randint
import time

from Enums import *
from robomaster import led
from robomaster import chassis
from robomaster import robot as SeeRoFunction
import RobotConn as RobotConnMod

#SETTINGS
class ConfigClass:
    def __init__(self):
        self.ConnectionType = ConnType.InternalRoutor
        self.NormalSpeed = 250 #rpm (keep in mind angle and speed are calculated the same)
        self.FastSpeed = 200
        self.TurnAngle = 80 #turning rpm
        self.SlowAngle =  25
        self.ArmSpeed = 1
        
        #safety settings
        self.SafeMode = True
        self.MaxRPM = 225 #be carefull please..
        
        #unstable options
        self.FPSCap = 60
        self.CamWin = True
        self.ResizeMainFBFeed = True

sett = ConfigClass()

runnin = td.Event()
runnin.set()

RoConn = RobotConnMod.Connection(runnin, sett.ConnectionType) #not sure if runin will trigger globally if stored in class
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
ToldToStop, FirstCamFrame, NewFrame = False, False, False
ArmBusy, ArmCmd = False, 0 #1:arm busy with cmd,
pw1, pw2, pw3, pw4 = 0, 0, 0, 0 #movement values
w1, w2, w3, w4 = 0, 0, 0, 0 #prev movement vals


#INITIATE ROBOT MODULES
#camera
if sett.CamWin:
    FrameQueue = queue.Queue(2)
    CamBufThread = td.Thread(target=RoConn.Start_Cam_Buffer_Queue, args=(screen, FrameQueue, sett.ResizeMainFBFeed))
    CamBufThread.start()
#led
RoLed = robot.led
RoChas = robot.chassis
RoBat = robot.battery
RoArm = robot.robotic_arm
RoGrip = robot.gripper

RoLed.set_led(comp=led.COMP_ALL, r=randint(1, 150), g=randint(1, 150), b=randint(1, 150), effect=led.EFFECT_ON) #test conn with leds

#subscribe functions
def GetPerc(procent, s):
        s.procent = procent
        
def GetPos(ChasisC, s):
    s.CY_pos = ChasisC[0]
    s.CX_pos = ChasisC[1]
    print(f'Y_pos: {str(ChasisC[0])}, X_pos: {str(ChasisC[1])}')
    
def GetArmPos(ArmC, s):
    s.AY_pos = ArmC[0]
    s.AX_pos = ArmC[1]
    print(f'arm y:{str(ArmC[0])}, arm x:{str(ArmC[1])}')

class SubbedIntrFuncClass:
    def __init__(s):
        s.procent = int() #battery procentage
        s.CY_pos = float()
        s.CX_pos = float()
        s.AY_pos = float()
        s.AX_pos = float()
        
        #subscribe Subscriber functions 
        RoBat.sub_battery_info(20,GetPerc, s)
        RoChas.sub_position(0, 1, GetPos, s)
        RoArm.sub_position(1, GetArmPos, s)
        
    
SubVals = SubbedIntrFuncClass()


#def GetPro(pro):
#    print(pro)
#
#RoBat.sub_battery_info(1,GetPro)

#fun
ArmY, ArmX, Claw = 0, 0, 0
PArmY, PArmX, PClaw = 0,0,0
RoConn.ConFree.wait()
RoConn.ConFree.clear()
RoArm.recenter()
RoConn.ConFree.set()

while runnin.is_set():
    #RoArm.moveto( x=0 , y=0 )
    #WKey, AKey, SKey, DKey = False, False, False, False
    mk = 0 #(pressed movement keys)
    #poll events
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: #window closed
            runnin.clear()
            
    #setting keyboard
    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_ESCAPE]:
        runnin.clear()
    #keys.index(pygame.K_w)
    #keys
    WKey = keys[pygame.K_w]
    if WKey: mk += 1
    DKey = keys[pygame.K_d]
    if DKey: mk += 1
    AKey = keys[pygame.K_a]
    if AKey: mk += 1
    SKey = keys[pygame.K_s]
    if SKey: mk += 1
    #angle keys
    LAngleKey = keys[pygame.K_LEFT]
    RAngleKey = keys[pygame.K_RIGHT]
    
    SideKeys = LAngleKey+RAngleKey
    if mk == 0 and SideKeys>0:
        mk = 1
    #Toggle Keys
    SlowTurn = keys[pygame.K_LCTRL]
    FastMove = keys[pygame.K_LSHIFT]
    
    #Arm 
    ak = 0 #arm Keys (commands)
    #ArmDownOpen = keys[pygame.K_1]
    
    ArmUp = keys[pygame.K_u]
    if ArmUp: ak += 1
    #if ArmUp: ak > 
    ArmDown = keys[pygame.K_j]
    if ArmDown: ak += 1
    if ArmUp and ArmDown:
        ak -= 2
        ArmUp, ArmDown = False, False
        
    ArmIn = keys[pygame.K_h]
    if ArmIn: ak += 1
    ArmOut = keys[pygame.K_k]
    if ArmOut: ak += 1
    if ArmIn and ArmOut:
        ak -= 2
        ArmUp, ArmOut = False, False
    
    ArmOpen = keys[pygame.K_1]
    if ArmOpen: ak += 1
    ArmClose = keys[pygame.K_2]
    if ArmClose: ak += 1
    if ArmOpen and ArmClose:
        ak -= 2
        ArmOpen, ArmClose = False, False
    
    #info keys
    PowerRead = keys[pygame.K_p]
    if PowerRead:
        print(f"Current power procentage: {str(SubVals.procent)}%")
        RoConn.ConFree.wait()
        RoConn.ConFree.clear()
        RoArm.recenter()
        RoConn.ConFree.set()
        ArmY, ArmX, Claw = 0, 0, 0

    #if ak > 0:
    #    if ArmUp: ArmY += sett.ArmSpeed
    #    if ArmDown: ArmY -= sett.ArmSpeed
    #    if ArmOut: ArmX += sett.ArmSpeed
    #    if ArmIn: ArmX -= sett.ArmSpeed
    #    if ArmOpen: Claw += 10
    #    if ArmClose: ArmY -= 10
    #    try:
    #        if ((PArmY != PArmY+ArmY) or (PArmX != PArmX+w2)):
    #            RoConn.ConFree.wait()
    #            RoConn.ConFree.clear()
    #            RoArm.move( x=ArmX , y=ArmY )
    #            RoConn.ConFree.set()
    #            PArmX, PArmY = ArmX, ArmY
    #        if PClaw != PClaw+Claw:
    #            if Claw <= 0:
    #                Claw = 0
    #                PClaw = 0
    #            if Claw >= 100:
    #                Claw = 100
    #                PClaw = 100
    #            if Claw > 50:
    #                RoConn.ConFree.wait()
    #                RoConn.ConFree.clear()
    #                RoGrip.Open(Claw)
    #                RoConn.ConFree.set()
    #            else:
    #                RoConn.ConFree.wait()
    #                RoConn.ConFree.clear()
    #                RoGrip.Close(Claw)
    #                RoConn.ConFree.set()
    #            PClaw = Claw
    #    except:
    #        print("lol")
            
    ##Robot Arm
    #if ArmBusy:
    #    if ArmDownOpen:
    #        print("CommandDownOpen")
        
    
    #Chasis movement
    if mk > 2:
        print("Too many keys pressed")
    elif mk <= 0:
        if ToldToStop == False:
            try:
                #print("stopmove")
                RoConn.ConFree.wait()
                RoConn.ConFree.clear()
                robot.chassis.drive_wheels(0,0,0,0, timeout=2)
                RoConn.ConFree.set()
                ToldToStop = True
            except BaseException as e:
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
            
            RoConn.ConFree.wait()
            RoConn.ConFree.clear()
            robot.chassis.drive_wheels(w1,w2,w3,w4, timeout=2)
            RoConn.ConFree.set()
            #robot.chassis.drive_speed(x,y,z, timeout=0)#x(Forward) y(Diagonal) z(Gay), seconds
            pw1, pw2, pw3, pw4 = w1, w2, w3, w4
            w1, w2, w3, w4 = 0, 0, 0, 0 #sets them at begin of movement
        #elif (time.time() > MoveRedo):
        #    MoveUpdate = time.time()+4
        #    robot.chassis.drive_speed(px,py,pz, timeout=0)
            
    #(After events fired!) load things to show in window
    if not sett.CamWin:
        clock.tick(sett.FPSCap)
        continue
    
    if FirstCamFrame: #or it will show black and die
        CamFrame = PrevCamFrame
        try:
            CamFrame = FrameQueue.get_nowait()
            CamImg = pygame.image.frombuffer(CamFrame, (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame
            screen.s.blit(CamImg, (0,0))
            NewFrame = True
            #print("BlitedFrame!")
        except:
            NewFrame=False
            #continue
            #print("NoNewFrame")
            #CamImg = pygame.image.frombuffer(PrevCamFrame, (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame
    else:
        CamFrame = FrameQueue.get()
        CamImg = pygame.image.frombuffer(CamFrame, (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame
        FirstCamFrame = True
        PrevCamFrame = CamFrame

    # flip() the display to put your work on screen
    #pygame.display.flip()
    #render
    #screen.s.fill("gray")
    if NewFrame:
        pygame.display.update()
        clock.tick(sett.FPSCap)  # limits FPS to 30

if sett.CamWin:
    FrameQueue.task_done()

runnin.clear()
robot.close()

pygame.display.quit()
pygame.quit()