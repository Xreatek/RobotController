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
        self.me = self._EstablishConn(ConnType)
        self.cam = self.me.camera
        self.cam.start_video_stream(display=False, resolution=IntrCam.STREAM_540P)
        
        #return self
        
    def _EstablishConn(s, ConnType):
        RoConn = IntrRobot.Robot()
        if ConnType == E.ConnType.ExternalRouter:
            #if needed can set custom ips
            IntrRobot.config.LOCAL_IP_STR = "192.168.34.144"
            IntrRobot.config.ROBOT_IP_STR = "192.168.34.223"
            
            RoConn.initialize(conn_type='sta')
        elif ConnType == E.ConnType.RobotRoutor:
            RoConn.initialize(conn_type='ap') 
        print("Robot Version:{0}".format(RoConn.get_version()))
        return RoConn
    
    def Start_Cam_Buffer_Queue(self, WinFo, FrameQ, ReSize=True):
        while self.runnin.is_set():
            try:
                cf = self.cam.read_cv2_image(timeout=120 , strategy='newest')
                cf = cv.cvtColor(cf, cv.COLOR_BGR2RGB)
                if ReSize:
                    cf = cv.resize(cf, (WinFo.MaxXDim, WinFo.MaxYDim))            
            except Exception as e:
                print("Cam FB Err: ", e)
                self.runnin.clear()#stopping main run
                break

            try:
                if(FrameQ.qsize() < 2):
                    FrameQ.put_nowait(cf)
                else:
                    FrameQ.get_nowait()
                    FrameQ.put_nowait(cf)
            except FrameQ.Empty as e:
                print("Queue was emptied while putting in queue")
                if self.runnin.is_set():
                    try:
                        FrameQ.put(cf, timeout=10)
                    except:
                        self.runnin.clear()
                        break
                continue
            except Exception as e:
                print(traceback.format_exc())
                print("Error :", e)
                self.runnin.clear()
            time.sleep(0.033) #0.033~30fps the specs it says the cam can do
        
        print("StoppedCamBuffer")
            
if __name__ == "__main__":
    import run
    run