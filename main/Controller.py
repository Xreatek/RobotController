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

class RobotInterface:
    def __init__(self, MainSettings, GlobVars):
        self.MainSettings = MainSettings #saving Global settings in class
        self.GlobVars = GlobVars
        #genereal settings
        self.Speed = self.MainSettings.Speed #wont change anything yet
        self.AngleSpeed = self.MainSettings.AngleSpeed #wont change anything yet
        
        #Robot Interface
        self.runState = GlobVars.runState
        self.command = ControllCMDs.Waiting
        self.args = self.GlobVars.RoCmdArgs
        self.DoneCmd = self.GlobVars.RoDone
        self.WaitForRoStatic = self.GlobVars.WaitForRoStatic
        self.Connection = self._MakeConnection()
        print("Robot Controller Connected")
        self.GlobVars.ConnState.set()
        
        self.IsDataCMD = self.GlobVars.ExpcData
        self.DataQueue = self.GlobVars.InterfaceData
        
        self.stoppedStream = threading.Event()#to make sure controller doesnt end before the camera port has been closed
        self.stoppedStream.set() #technically not running
        self.DisplayRawStream = self.MainSettings.DisplayRawStream
        if self.DisplayRawStream:
            self._RawStream = collections.deque(maxlen=1)
            self._Stream = threading.Thread(name='Camera_Stream', target=ImgStream.Stream, args=[self._RawStream, self.stoppedStream, self.MainSettings, self.GlobVars])
            self._Stream.start()
            self._ImgStream = self.GlobVars.ImgStream
            self._CamRelay = threading.Thread(name='Frame_Relay', target=self._StreamRelay, args=[])
            self._CamRelay.start()
        else:
            self._RawStream = self.GlobVars.ImgStream
            self._Stream = threading.Thread(name='Camera_Stream', target=ImgStream.Stream, args=[self._RawStream, self.stoppedStream, self.MainSettings, self.GlobVars])
            self._Stream.start()
            
        #self.Subbed = SubFuncClass(self.Connection) #unnecessary for now..
        self.DoneCmd.set()
        
        #Starts ai robot interface
        self.InterfaceLoop()
        #end of robot interface initiation
            
    def _MakeConnection(self):
        address = (self.MainSettings.RobotIp, int (self.MainSettings.RobotPort))
        Connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Connecting..")
        bootupCMDs=list()
        bootupCMDs.append(str('command;').encode('utf-8'))
        bootupCMDs.append(str('stream on;').encode('utf-8'))
        #bootupCMDs.append(str('ir_distance_sensor measure off;').encode('utf-8'))
        Connection.connect(address)
        for cmd in bootupCMDs:
            print(cmd)
            Connection.send(cmd)
            try:
                buf = Connection.recv(1024)
                print(buf.decode('utf-8'))
            except socket.error as e:
                print("Socket Error while connecting! :", e)
                sys.exit(1)
        print("Connection made!")
        return Connection
    
    def _StreamRelay(self):
        while self.GlobVars.ConnState.isSet() and self.runState.isSet():
            try:
                Frame = self._RawStream.popleft()
                #F = cv2.flip(F, 1)
                self._ImgStream.append(Frame)
                cv.imshow('IP Camera stream',Frame)
                if cv.waitKey(1) == ord('q'):
                    print('stream relay cleared')
                    self.runState.clear()
                    #self.GlobalVars.ConnState.clear() #cam does not look at runstate
                    
            except IndexError: time.sleep(0.0001);
            except Exception as e:
                print(f'Caught error: {e} Traceback: {traceback.format_exc()}')
        cv.destroyAllWindows()
        
    def WaitUntilStatic(self):
        while self.runState.is_set() and self.WaitForRoStatic.is_set():
            self.Connection.send(str('chassis status ?;').encode('utf-8'))
            #time.sleep(0.1)#let the command be received
            try:
                buf = self.Connection.recv(1024)
                buf.decode('utf-8')
                #print(f'Static state: {buf[0]-48}') #look at if below for explaination
                
                #print(f'state buf: {buf}, cut:{buf[0]}')
                if buf[0] == 49: #first value is 48 when false 49 when true (i know its bad but it is what it is)
                    self.WaitForRoStatic.clear()
                    
            except Exception as e:
                print(f"Problem sending stop stream {e}, Trace:{traceback.format_exc()}")
                self.runState.clear()
    
    
    def InterfaceLoop(self): 
        while self.GlobVars.ConnState.is_set() and self.runState.is_set(): 
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
                time.sleep(0.0001)# to not stress out controller
            else:
                try:
                    CmdArgs = self.args.pop()
                except IndexError:
                    CmdArgs = None
                cmd = self.command(CmdArgs)
                #print(cmd)
                self.Connection.send(cmd.encode('utf-8')) #wait untill complete <- to do!
                #time.sleep(0.2)
                try:
                    buf = self.Connection.recv(1024)
                    if self.IsDataCMD.is_set():
                        BufContent = buf.decode('utf-8')
                        #print(f'Contoler Reply: {BufContent}')
                        self.DataQueue.put(BufContent)
                        self.IsDataCMD.clear()
                        #print("sent and cleared data buffer")
                except Exception as e:
                    print(f"Problem sending stop stream {e}, Trace:{traceback.format_exc()}")
                if self.WaitForRoStatic.is_set():
                    print('Running command until robot static')
                    self.WaitUntilStatic()
                #print("Command finished!")
                self.DoneCmd.set()
        print("Controller stopping..")
        #self.Connection.send(str('ir_distance_sensor measure off;').encode('utf-8'))
        self.Connection.send(str('stream off;').encode('utf-8'))
        self.stoppedStream.wait(timeout=6)
        self.Connection.send(str('quit;').encode('utf-8'))
        time.sleep(0.5) #make sure close doesnt arive ealier
        self.Connection.close()
        print('Controller stopped.')
    
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()