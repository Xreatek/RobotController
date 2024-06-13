from ultralytics import YOLO
import cv2 as cv
from Enums import *
import math
import random

import time
import datetime
import traceback

class AiObserver:
    def __init__(self, MainSettings, GlobalVariables) -> None:
        self.MainSettings = MainSettings
        self.GlobeVars = GlobalVariables
        
        #settings
        self.Visualize = self.MainSettings.Visualize
        
        #object detector
        if not self.Visualize:
            self.model = YOLO("./model/M2V9.pt") #best for now: M2V9 imgsz:640
            self.model.cuda(0)
            self.model.info()
            self.classNames = ["paper"]
        
        #variables
        self.runState = self.GlobeVars.runState
        self.ImgStream = self.GlobeVars.ImgStream
        self.mode = AiMode.Searching
        
        #Robot Interface Commands
        self.InterfaceDone = self.GlobeVars.RoDone
        
        #wait for first frame
        while self.runState.isSet():
            try:
                FirstFrame = self.ImgStream.popleft()
                height, self.imgWidth, _ = FirstFrame.shape
                break
            except IndexError: 
                time.sleep(0.01)
                continue
            except Exception as e:
                print(f'Ran into error while getting first frame Error:{e}, Trace:{traceback.format_exc()}')
                self.runState.clear()
        print("Got first frame.")    
        
        #start main observerloop
        self.AiMain()
        
        #self.imgsz = 640 #do not change requires a new model
    
    def Interface(self, command, args=None):
        if self.InterfaceDone.isSet():
            if args != None:
                self.GlobeVars.RoCmdArgs = args
            self.GlobeVars.RoCmd = command
        else:
            print(f"Interfaced before Cmd was done! cmd:{command}, args:{args}")
            
    def TurnToWad(self, detectPos): #returns angle required to turn
        RelativePos = detectPos / self.imgWidth
        return (RelativePos - 0.5) * 120 #the fov of the cam is 120 
        
    def AiMain(self):
        while self.runState.isSet():
            try:
                #print("Ai Vision")
                InputImg = self.ImgStream.popleft()        
                #InputImg = InputImg[120:600, 320:960] #sizing to a dataset of 640 so W:640 H:480
                                #  Y(120-600) X(320-960)
                                #for wad angle 120/2=60 320/2=160
                #Dataset collection
                if self.MainSettings.DataCollector: #merge recovery branch with main
                    if random.randint(0,1):
                        print("captured frame")
                        cv.imwrite(f'./DataSet/{time.time()}_{datetime.datetime.now().day}_{datetime.datetime.now().month}.jpg', InputImg)
                        time.sleep(0.5)
                    continue
                results = self.model(InputImg, stream=False, conf=0.5, iou=0.5 ,show=self.Visualize, verbose=False)
                
                if self.mode == AiMode.Searching and results[0]:
                    boxes = results[0].boxes
                    print(boxes)
                    #TurnAngle = self.TurnToWad()
                    continue
                    #print("search")
                    
                    
            except IndexError:
                time.sleep(0.05)
                continue
            except Exception as e:
                print(f'Error in Ai runtime {e},  Trace:{traceback.format_exc()}')
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()