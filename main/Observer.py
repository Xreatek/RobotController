from ultralytics import YOLO
import cv2 as cv
from Enums import *
import math
import random

import time
import traceback

class AiObserver:
    def __init__(self, MainSettings, GlobalVariables) -> None:
        self.MainSettings = MainSettings
        self.GlobeVars = GlobalVariables
        
        #settings
        self.Visualize = self.MainSettings.Visualize
        
        #object detector
        self.model = YOLO("./model/MerBestV0.5.pt") #best for now: 0.5
        #self.model.load('../model/M1V9.pt')
        self.model.info()
        self.classNames = ["paper"]
        
        #variables
        self.runState = self.GlobeVars.runState
        self.ImgStream = self.GlobeVars.ImgStream
        self.mode = AiMode.Searching
        
        #Robot Interface Commands
        self.InterfaceDone = self.GlobeVars.RoDone
        
        #wait for first frame
        while self.runState.is_set():
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
        if self.InterfaceDone.is_set():
            if args != None:
                self.GlobeVars.RoCmdArgs = args
            self.GlobeVars.RoCmd = command
        else:
            print(f"Interfaced before Cmd was done! cmd:{command}, args:{args}")
            
    def TurnToWad(self, detectPos): #returns angle required to turn
        RelativePos = detectPos / self.imgWidth
        return (RelativePos - 0.5) * 120 #the fov of the cam is 120 
        
    def AiMain(self):
        while self.runState.is_set():
            try:
                #print("Ai Vision")
                InputImg = self.ImgStream.popleft()        
                InputImg = InputImg[120:600, 320:960] #cv.resize(InputImg, (640, 640)) #resizing to img size that it has been trained on helps big time
                
                #Dataset collection
                if self.MainSettings.DataCollector:
                    if random.randint(0,1):
                        cv.imwrite(f'DataSet/img.jpg', InputImg)
                
                results = self.model(InputImg, stream=False, conf=0.05, iou=0.5 ,show=self.Visualize, device="cuda:0",verbose=False)
                
                if self.mode == AiMode.Searching:
                    #TurnAngle = self.TurnToWad()
                    continue
                    #print("search")
                    
                    
            except IndexError:
                time.sleep(0.01)
                continue
            except Exception as e:
                print(f'Error in Ai runtime {e},  Trace:{traceback.format_exc()}')
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()