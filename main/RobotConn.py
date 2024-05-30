import threading as td
import traceback
import time

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
        RoConn = IntrRobot.Robot()
        if ConnType == E.ConnType.ExternalRouter:
            #if needed can set custom ips
            IntrRobot.config.LOCAL_IP_STR = "10.249.48.12"
            IntrRobot.config.ROBOT_IP_STR = "10.249.48.13"
            
            RoConn.initialize(conn_type='sta', proto_type="tcp")
        elif ConnType == E.ConnType.InternalRoutor:
            RoConn.initialize(conn_type='ap') 
        print("Robot Version:{0}".format(RoConn.get_version()))
        s.ConFree.set()
        return RoConn
    
    def Start_Cam_Buffer_Queue(self, WinFo, FrameQ, ReSize=True):
        while self.runnin.is_set():
            try:
                #self.ConFree.wait()
                #self.ConFree.clear()
                cf = self.cam.read_cv2_image(timeout=10 , strategy='newest')
                #self.ConFree.set()
                cf = cv.cvtColor(cf, cv.COLOR_BGR2RGB)
                if ReSize:
                    cf = cv.resize(cf, (WinFo.MaxXDim, WinFo.MaxYDim))
                #print("FrameBuffered")   
            except TimeoutError as e:
                print("Timed out getting new frame.")
                continue    
            except Exception as e:
                print("Cam FB Err: ", e)
                self.runnin.clear()#stopping main run
                break  
    
        print("StoppedCamBuffer")
            
def RobotFoundNewAP(rs):
    if rs.runnin.is_set():
        #rs.me.reset()
        rs.cam.stop_video_stream()
        rs.me.close()
        time.sleep(10)
        v1 , v2 = rs.runnin, rs.APType
        return Connection(v1, v2)

if __name__ == "__main__":
    import run
    run