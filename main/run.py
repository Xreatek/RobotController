import threading as td
import queue
import traceback
import pygame
from random import randint
import time
import datetime

from Enums import *
from robomaster import led
from robomaster import chassis
from robomaster import battery
import RobotConn as RobotConnMod

#SETTINGS
class ConfigClass:
    def __init__(self):
        self.ConnectionType = ConnType.ExternalRouter
        self.NormalSpeed = 150 #rpm (keep in mind angle and speed are calculated the same)
        self.TurnAngle = 50 #turning rpm
        
        
        #unstable options
        self.SafeMode = True
        self.MaxRPM = 200 #be carefull please..
        self.FPSCap = 30
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

#INITIATE ROBOT MODULES
#camera
FrameQueue = queue.Queue(2)
CamBufThread = td.Thread(target=RoConn.Start_Cam_Buffer_Queue, args=(screen, FrameQueue, sett.ResizeMainFBFeed))
CamBufThread.start()
#led
RoLed = robot.led
RoChas = robot.chassis

RoLed.set_led(comp=led.COMP_ALL, r=randint(1, 150), g=randint(1, 150), b=randint(1, 150), effect=led.EFFECT_ON) #test conn with leds

#set default values
ToldToStop = False
SupFmTm = sett.FPSCap/1000
lft = time.monotonic #get miliseconds
FirstCamFrame = False
SupAnglMovSetFps = ()
    
#Frame = 0
pw1, pw2, pw3, pw4 = 0, 0, 0, 0 #movement values
w1, w2, w3, w4 = 0, 0, 0, 0 #se #prev movements

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
    if mk == 0 and (LAngleKey or RAngleKey):
        mk = 1
    
    #print(mk)

    #Chasis movement
    if mk > 2:
        print("Too many keys pressed")
    elif mk <= 0:
        if ToldToStop == False:
            try:
                #print("stopmove")
                time.sleep(0.1)
                robot.chassis.drive_wheels(0,0,0,0, timeout=0)
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
        
        
        if WKey: #w1 = Upper Right, w2= Upper Left, w3 = Lower Left, w4 = Lower Right (from back view of robot)
            w1 += sett.NormalSpeed/offset
            w2 += sett.NormalSpeed/offset
            w3 += sett.NormalSpeed/offset
            w4 += sett.NormalSpeed/offset
        if AKey: #up = + down = - (test if this actually works)
            w1 += sett.NormalSpeed/offset #outward up
            w2 += 0-(sett.NormalSpeed/offset)  #inward down
            w3 += sett.NormalSpeed/offset #inward up
            w4 += 0-(sett.NormalSpeed/offset) #outward down
        if DKey:
            w1 += 0-(sett.NormalSpeed/offset)
            w2 += sett.NormalSpeed/offset
            w3 += 0-(sett.NormalSpeed/offset)
            w4 += sett.NormalSpeed/offset
        if SKey:
            w1 += 0-sett.NormalSpeed/offset
            w2 += 0-sett.NormalSpeed/offset
            w3 += 0-sett.NormalSpeed/offset
            w4 += 0-sett.NormalSpeed/offset
        
        if LAngleKey:#w1 = Upper Right, w2= Upper Left, w3 = Lower Left, w4 = Lower Right (from back view of robot)
            w1 += sett.TurnAngle/offset #L
            w4 += sett.TurnAngle/offset
            w2 += 0-sett.TurnAngle/offset #R
            w3 += 0-sett.TurnAngle/offset
        if RAngleKey:#w1 = Upper Right, w2= Upper Left, w3 = Lower Left, w4 = Lower Right (from back view of robot)
            w1 += 0-sett.TurnAngle/offset #L
            w4 += 0-sett.TurnAngle/offset
            w2 += sett.TurnAngle/offset #R
            w3 += sett.TurnAngle/offset
        
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
            
            robot.chassis.drive_wheels(w1,w2,w3,w4, timeout=1)
            #robot.chassis.drive_speed(x,y,z, timeout=0)#x(Forward) y(Diagonal) z(Gay), seconds
            pw1, pw2, pw3, pw4 = w1, w2, w3, w4
            w1, w2, w3, w4 = 0, 0, 0, 0 #sets them at begin of movement
        #elif (time.time() > MoveRedo):
        #    MoveUpdate = time.time()+4
        #    robot.chassis.drive_speed(px,py,pz, timeout=0)
            
    #(After events fired!) load things to show in window
    if FirstCamFrame: #or it will show black and die
        CamFrame = PrevCamFrame
        try:
            CamFrame = FrameQueue.get_nowait()
            CamImg = pygame.image.frombuffer(CamFrame, (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame
            PrevCamFrame = CamFrame
        except:
            CamImg = pygame.image.frombuffer(PrevCamFrame, (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame
    else:
        CamFrame = FrameQueue.get()
        CamImg = pygame.image.frombuffer(CamFrame, (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame
        FirstCamFrame = True
        PrevCamFrame = CamFrame
    
    #render
    screen.s.fill("gray")
    screen.s.blit(CamImg, (0,0))
    
    # flip() the display to put your work on screen
    #pygame.display.flip()
    pygame.display.update()

    clock.tick(sett.FPSCap)  # limits FPS to 30

FrameQueue.task_done()

runnin.clear()
robot.close()

pygame.display.quit()
pygame.quit()