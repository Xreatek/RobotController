from ultralytics import YOLO
import cv2 as cv
from Enums import *
import math 

class TheAi:
    def __init__(self, RunState, Image) -> None:
        self.RunState = RunState
        self.model = YOLO("./model/CurProp.pt")
        self.classNames = ["paper"]
        self.frame = Image
        self.busy = False
        self.mode = AiMode.Searching
        
        self.imgsz = 640 #do not change requires a new model

    def AiMain(self):
        while self.RunState.is_set():
            print("Ai Vision")

            if self.mode == AiMode.Searching:
                print("searching")
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