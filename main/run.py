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
        self.ConnectionType = ConnType.ExternalRouter
        self.NormalSpeed = 50 #rpm (keep in mind angle and speed are calculated the same)
        self.FastSpeed = 200
        self.TurnAngle = 70 #turning rpm
        self.SlowAngle =  25
        
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

RoLed.set_led(comp=led.COMP_ALL, r=randint(1, 150), g=randint(1, 150), b=randint(1, 150), effect=led.EFFECT_ON) #test conn with leds

#subscribe functions
def GetPerc(procent, s):
        s.procent = procent
        
def GetPos(data, s):
    s.Y_pos = data[0]
    s.X_pos = data[1]
    #print(f'Y_pos: {str(data[0])}, X_pos: {str(data[1])}')

class SubbedIntrFuncClass:
    def __init__(s):
        s.procent = int() #battery procentage
        s.Y_pos = float()
        s.X_pos = float()
        
        #subscribe Subscriber functions 
        RoBat.sub_battery_info(20,GetPerc, s)
        RoChas.sub_position(0, 1, GetPos, s)
        
        
    
SubVals = SubbedIntrFuncClass()


#def GetPro(pro):
#    print(pro)
#
#RoBat.sub_battery_info(1,GetPro)

while runnin.is_set():
    
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
    #Arm Keys
    ArmUp = keys[pygame.K_1]
    ArmDown = keys[pygame.K_2]
    
    ArmOut = keys[pygame.K_3]
    Armin = keys[pygame.K_4]
    
    ArmOpen = keys[pygame.K_5]
    ArmClose = keys[pygame.K_6]
    #info keys
    PowerRead = keys[pygame.K_p]
    if PowerRead:
        print(f"Current power procentage: {str(SubVals.procent)}%")

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