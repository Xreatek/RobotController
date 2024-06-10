from robomaster import robot as IRO

import robomaster.camera as RoCam
import robomaster.led as ROLED

import threading
import queue

import traceback
import time

from Enums import *
import SubFuncs
import ImgStream

class SubFuncClass:
    def __init__(self, RobotConn):
        self.procent = int() #battery procentage
        self.CY_pos = float()
        self.CX_pos = float()
        self.AY_pos = float()
        self.AX_pos = float()
        
        #subscribe Subscriber functions 
        RobotConn.battery.sub_battery_info(1,SubFuncs.GetPerc, self)
        RobotConn.chassis.sub_position(0, 1, SubFuncs.GetPos, self)
        RobotConn.robotic_arm.sub_position(1, SubFuncs.GetArmPos, self)

class RobotInterface:
    def __init__(self, MainSettings, GlobVars):
        self.MainSettings = MainSettings #saving Global settings in class
        self.GlobVars = GlobVars
        #genereal settings
        self.Speed = self.MainSettings.Speed
        self.AngleSpeed = self.MainSettings.AngleSpeed
        
        #Robot Interface
        self.command = ControllCMDs.Waiting
        self.args = self.GlobVars.RoCmdArgs
        self.DoneCmd = self.GlobVars.RoDone
        self.Connection = self._MakeConnection()
        self.Stream = threading.Thread(target=ImgStream.Stream, args=[self.Connection, MainSettings, GlobVars])
        self.Stream.start()
        
        self.Connection.led.set_led(comp=ROLED.COMP_ALL, r=0, g=0, b=0, effect=ROLED.EFFECT_OFF)
        #self.Subbed = SubFuncClass(self.Connection) #unnecessary for now..
        print("Robot Controller Connected")
        self.GlobVars.ConnState.set()
        
        #Starts ai robot interface
        self.InterfaceLoop()
            
            
    def _MakeConnection(self):
        RoConn = IRO.Robot()
        _ConTempts = 0
        while True:
            try:
                if self.MainSettings.ConnectionType == ConnType.ExternalRouter:
                    #if needed can set custom ips
                    if self.MainSettings.RobotIp != None:
                        print("robot ip set")
                        IRO.config.ROBOT_IP_STR = self.MainSettings.RobotIP#"10.249.48.13"

                    if self.MainSettings.HostIp != None:
                        print("local ip set")
                        IRO.config.LOCAL_IP_STR = self.MainSettings.HostIp #"10.249.48.12"
                    #IntrRobot.config.DEFAULT_PROTO_TYPE = IntrRobot.protocol.DUSS_MB_TYPE_REQ

                    RoConn.initialize(conn_type='sta', proto_type="udp")
                elif self.MainSettings.ConnectionType == ConnType.InternalRoutor:
                    RoConn.initialize(conn_type='ap')
                #print(RoConn.ip)
                break
            except ConnectionRefusedError as e:
                print(f"Connection rejected! Retrying...")
                time.sleep(0.5)
                
                if _ConTempts >= 40:
                    Warning("Reconnecting Failed!")
                    self.GlobVars.runState.clear()
                    return False
                else:
                    _ConTempts += 1
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error establishing connection:{e} | trace: {traceback.format_exc()}")
                break
        print("Robot Version:{0}".format(RoConn.get_version()))
        return RoConn
    
    
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
                time.sleep(0.05)#otherwise camera would 💩 itself because it would have only a few nano seconds to get a image
            
            elif self.command == ControllCMDs.Rotate:
                RotateDegrees = self.args.pop() #rotate degrees
                self.Connection.chassis.move(x=0,y=0, z=RotateDegrees ,xy_speed=0.0, z_speed=30).wait_for_completed()
                print('Rotation done!')
                self.DoneCmd.set()
                
                