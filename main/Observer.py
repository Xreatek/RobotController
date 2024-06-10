from ultralytics import YOLO
import cv2 as cv
from Enums import *
import math 

import time
import traceback

class AiObserver:
    def __init__(self, MainSettings, GlobalVariables) -> None:
        self.MainSettings = MainSettings
        self.GlobeVars = GlobalVariables
        
        #settings
        self.Visualize = self.MainSettings.Visualize
        
        #object detector
        self.model = YOLO("./model/CurProp.pt")
        self.classNames = ["paper"]
        
        #variables
        self.RunState = self.GlobeVars.runState
        self.ImgStream = self.GlobeVars.ImgStream
        self.mode = AiMode.Searching
        
        #Robot Interface Commands
        self.InterfaceDone = self.GlobeVars.RoDone
        
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
    
    def AiMain(self):
        while self.RunState.is_set():
            try:
                print("Ai Vision")

                if self.mode == AiMode.Searching:
                    print("search")
                    image = self.ImgStream.pop()
                    
                    #cv.imshow("test", image)
                    #cv.waitKey(1)


                if self.Visualize:
                    print("Visualize")
                    #here ai detect
                    results = self.model(self.frame, stream=True)
                    # coordinates
                    for r in results:
                        boxes = r.boxes

                        for box in boxes:
                            # bounding box
                            print(box)
                            x1, y1, x2, y2 = box.xyxy[0]
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

                            # put box in cam
                            cv.rectangle(self.frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

                            # confidence
                            #confidence = math.ceil((box.conf[0]*100))/100
                            #print("Confidence --->",confidence)

                            # class name
                            #cls = int(box.cls[0])
                            #print("Class name -->", classNames[cls])

                            # object details
                            org = [x1, y1]
                            font = cv.FONT_HERSHEY_SIMPLEX
                            fontScale = 1
                            color = (255, 0, 0)
                            thickness = 2

                            #cv.putText(cf, classNames[cls], org, font, fontScale, color, thickness)

                    cv.imshow('Webcam', self.frame)
                    cv.waitKey(1)
            except IndexError:
                time.sleep(0.01) #to reduce some lag getting images
            except Exception as e:
                print(f'Ai observer ran into an error {e}, traceback: {traceback.format_exc()}')
                