import threading as td
import traceback
import time
import pygame
import random

from robomaster import robot as IntrRobot
from robomaster import camera as IntrCam
from robomaster import led as IntrLed

import cv2 as cv
#import robomaster as irm
import Enums as E

class Connection:
    def __init__(self, runinEvnt ,ConnType) -> None:
        self.runnin = runinEvnt
        self.ConFree = td.Event() #(connection not locked)problems may arise if more async threads comunicate with the sdk so that both resume at the same time then make async comunication func
        self.me = self._EstablishConn(ConnType)
        self.APType = ConnType
        
        self.cam = self.me.camera
        self.cam.start_video_stream(display=False, resolution=IntrCam.STREAM_360P)
        
    def _EstablishConn(s, ConnType):
        #IntrRobot.client.CLIENT_MAX_EVENT_NUM=2
        RoConn = IntrRobot.Robot()
        _ConTempts = 0
        while True:
            try:
                if ConnType == E.ConnType.ExternalRouter:
                    #if needed can set custom ips
                    IntrRobot.config.LOCAL_IP_STR = "10.249.48.12"
                    IntrRobot.config.ROBOT_IP_STR = "10.249.48.13"

                    RoConn.initialize(conn_type='sta', proto_type="tcp")
                elif ConnType == E.ConnType.InternalRoutor:
                    RoConn.initialize(conn_type='ap')
                break
            except ConnectionRefusedError as e:
                print(f"Connection rejected! Retrying (Hold esc to stop)")
                time.sleep(0.5)
                keys = pygame.key.get_pressed()
                
                if keys[pygame.K_ESCAPE]:
                    s.runnin.clear()
                    return False
                
                if _ConTempts >= 40:
                    Warning("Reconnecting Failed!")
                    s.runnin.clear()
                    return False
                else:
                    _ConTempts += 1
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error establishing connection:{e} | trace: {traceback.format_exc()}")
                break
        print("Robot Version:{0}".format(RoConn.get_version()))
        s.ConFree.set()
        return RoConn
            
def RobotCloseOldAP(rs):
    try:
        if rs.runnin.is_set():
            ApType = rs.APType
            #rs.me.reset()
            rs.cam.stop()
            rs.me.close()
            print("cleared connection")
            #time.sleep(1)
            return ApType
    except Exception as e:
        print(f'Could not reconnect. | {e}')

if __name__ == "__main__":
    import run
    run