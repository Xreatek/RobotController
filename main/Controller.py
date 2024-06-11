import sys
import socket

#from robomaster import robot as IRO

#import robomaster.camera as RoCam
#import robomaster.led as ROLED

import collections
import threading
import queue

import cv2 as cv
import traceback
import time

from Enums import *
#import SubFuncs
import ImgStream

#class SubFuncClass:
#    def __init__(self, RobotConn):
#        self.procent = int() #battery procentage
#        self.CY_pos = float()
#        self.CX_pos = float()
#        self.AY_pos = float()
#        self.AX_pos = float()
#        
#        #subscribe Subscriber functions 
#        RobotConn.battery.sub_battery_info(1,SubFuncs.GetPerc, self)
#        RobotConn.chassis.sub_position(0, 1, SubFuncs.GetPos, self)
#        RobotConn.robotic_arm.sub_position(1, SubFuncs.GetArmPos, self)

class RobotInterface:
    def __init__(self, MainSettings, GlobVars):
        self.MainSettings = MainSettings #saving Global settings in class
        self.GlobVars = GlobVars
        #genereal settings
        self.Speed = self.MainSettings.Speed
        self.AngleSpeed = self.MainSettings.AngleSpeed
        
        #Robot Interface
        self.runState = GlobVars.runState
        self.command = ControllCMDs.Waiting
        self.args = self.GlobVars.RoCmdArgs
        self.DoneCmd = self.GlobVars.RoDone
        self.Connection = self._MakeConnection()
        
        self.DisplayRawStream = self.MainSettings.DisplayRawStream
        if self.DisplayRawStream:
            self._RawStream = collections.deque(maxlen=1)
            self._Stream = threading.Thread(name='Camera_Stream', target=ImgStream.Stream, args=[self._RawStream, self.MainSettings, self.GlobVars])
            self._Stream.start()
            self._ImgStream = self.GlobVars.ImgStream
            self._CamRelay = threading.Thread(name='Frame_Relay', target=self._StreamRelay, args=[])
            self._CamRelay.start()
        else:
            self._RawStream = self.GlobVars.ImgStream
            self._Stream = threading.Thread(name='Camera_Stream', target=ImgStream.Stream, args=[self._RawStream, self.MainSettings, self.GlobVars])
            self._Stream.start()
        
        #self.Subbed = SubFuncClass(self.Connection) #unnecessary for now..
        print("Robot Controller Connected")
        self.GlobVars.ConnState.set()
        self.DoneCmd.set()
        
        #Starts ai robot interface
        self.InterfaceLoop()
            
            
    def _MakeConnection(self):
        address = (self.MainSettings.RobotIp, int (self.MainSettings.RobotPort))
        Connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Connecting..")
        Connection.connect(address)
        Connection.send('command;'.encode('utf-8'))
        try:
            buf = Connection.recv(1024)
            print(buf.decode('utf-8'))
        except socket.error as e:
            print("Socket Error while connecting! :", e)
            sys.exit(1)
        Connection.send('stream on;'.encode('utf-8'))
        print("Connection made!")
        return Connection
    
    def _StreamRelay(self):
        while self.runState.is_set():
            try:
                Frame = self._RawStream.pop()
                #F = cv2.flip(F, 1)
                cv.imshow('IP Camera stream',Frame)
                cv.waitKey(1)
                self._ImgStream.append(Frame)
            except IndexError: time.sleep(0.01);
            except Exception as e:
                print(f'Caught error: {e} Traceback: {traceback.format_exc()}')
    
    def InterfaceLoop(self): 
        while self.GlobVars.runState.is_set(): 
            if self.DoneCmd.is_set():
                try:
                    self.command = self.GlobVars.RoCmd.pop()
                    self.DoneCmd.clear()
                except IndexError:
                    #print("No new interface command.")
                    self.command = ControllCMDs.Waiting
                except Exception as e:
                    print(f"Error getting command: {e} trace: {traceback.format_exc()}")
            
            #command structs
            if self.command == ControllCMDs.Waiting:
                time.sleep(0.3)# to not stress out controller
            else:
                CmdArgs = self.args.pop()
                cmd = self.command(CmdArgs)
                print(cmd)
                self.Connection.send(cmd.encode('utf-8')) #wait untill complete
                try:
                    buf = self.Connection.recv(1024)
                    print(buf.decode('utf-8'))
                except:
                    print("couldnt wait")
                print("Command finished!")
                self.DoneCmd.set()
                
            #elif self.command == ControllCMDs.Rotate:
            #    RotateDegrees = self.args.pop() #rotate degrees
            #    self.Connection.chassis.move(x=0,y=0, z=RotateDegrees ,xy_speed=0.0, z_speed=30).wait_for_completed()
            #    print('Rotation done!')
            #    self.DoneCmd.set()
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()