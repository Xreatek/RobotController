import traceback

import time
import cv2

class Stream:
    def __init__(self, RoConnection, MainSettings, GlobVars) -> None:
        self.MainSettings = MainSettings
        self.GlobVars = GlobVars
        
        self.RobotCam = RoConnection.camera
        self.runState = self.GlobVars.runState
        
        self.ImgStream = self.GlobVars.ImgStream
        
        #robot init
        try:
            self.VidStream = self.RobotCam.start_video_stream( display=self.MainSettings.DisplayRawStream , resolution=MainSettings.StreamRes)
            
            #self.VidStream = cv2.
        except Exception as e:
            print(f"Error starting stream! stopping program. error: {e} trace: {traceback.format_exc()}")
            self.runState.clear()
        
        self.MediaStream()
    
    def MediaStream(self):
        while self.runState.is_set():
            Frame = self.RobotCam.read_video_frame(timeout=5, strategy="newest") #lmao video dies yeah
            #Frame = self.RobotCam.take_photo()
            self.ImgStream.append(Frame)
            
            