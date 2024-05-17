import threading as td
import queue
import traceback
import pygame
from random import randint
import time

import Enums as E
from robomaster import led
from robomaster import chassis
from robomaster import battery
battery.logger
import RobotConn as RobotConnMod

#SETTINGS
class ConfigClass:
    def __init__(self):
        self.ConnectionType = E.ConnType.ExternalRouter
        
        #iykyk options
        self.ResizeMainFBFeed = True

settings = ConfigClass()

runnin = td.Event()
runnin.set()

RoConn = RobotConnMod.Connection(runnin, settings.ConnectionType) #not sure if runin will trigger globally if stored in class
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
CamBufThread = td.Thread(target=RoConn.Start_Cam_Buffer_Queue, args=(screen, FrameQueue, settings.ResizeMainFBFeed))
CamBufThread.start()
#led
RoLed = robot.led
RoChas = robot.chassis

RoLed.set_led(comp=led.COMP_ALL, r=randint(1, 150), g=randint(1, 150), b=randint(1, 150), effect=led.EFFECT_ON) #test conn with leds

#set default values
Speed = 0.0
MoveAngle = 0.0
ToldToStop = False

LStopTime = time.time()
MoveUpdate = time.time()
Frame = 0
x, y, z = 0, 0, 0 #movement values
py, px, pz = 0, 0, 0 #prev movements
while runnin.is_set():
    #WKey, AKey, SKey, DKey = False, False, False, False
    pmk = 0 #(pressed movement keys)
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
    if WKey: pmk += 1
    DKey = keys[pygame.K_d]
    if DKey: pmk += 1
    AKey = keys[pygame.K_a]
    if AKey: pmk += 1
    SKey = keys[pygame.K_s]
    if SKey: pmk += 1
    print(pmk)

    #Chasis movement
    if pmk > 2:
        print("Too many keys pressed")
    elif pmk <= 0:
        if ToldToStop == False:
            try:
                print("stopmove")
                time.sleep(0.1)
                robot.chassis.drive_wheels(0,0,0,0, timeout=0)
                ToldToStop = True
            except BaseException as e:
                print("Could not send command.")
    else:
        x, y, z = 0, 0, 0 #sets them at begin of movement
        print("key states"+str(WKey)+str(AKey)+str(SKey)+str(DKey)+str(pmk))
        if WKey:
            x += 1
        if AKey:
            y += -1
        if DKey:
            y += 1
        if SKey:
            x += -1
        
        if ((px != px+x) or (py != py+y) or (pz != pz+z)):#if movement values are different from last frame
            print(str(x)+","+str(y)+","+str(z))
            MoveRedo = time.time()+10
            robot.chassis.drive_speed(x,y,z, timeout=0)#x(Forward) y(Diagonal) z(Gay), seconds
            px, py, pz = x, y, z
            x, y, z = 0, 0, 0 #sets them at begin of movement
        elif (time.time() > MoveRedo):
            MoveUpdate = time.time()+4
            robot.chassis.drive_speed(px,py,pz, timeout=0)
            
    #(After events fired!) load things to show in window
    CamImg = pygame.image.frombuffer(FrameQueue.get(timeout=5), (screen.MaxXDim, screen.MaxYDim),"RGB") #cam frame

    #render
    screen.s.fill("gray")
    screen.s.blit(CamImg, (0,0))
    
    # flip() the display to put your work on screen
    #pygame.display.flip()
    pygame.display.update()

    clock.tick(60)  # limits FPS to 60
    Frame +=1

pygame.event.post(pygame.event.Event(pygame.QUIT))

pygame.quit()
FrameQueue.task_done()

runnin.clear()
robot.close()
