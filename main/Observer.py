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
        self.DataCollector = MainSettings.DataCollector
        
        #object detector
        if not self.DataCollector:
            self.model = YOLO("./model/M2V9.pt") #best for now: M2V9 imgsz:640
            self.model.cuda(0)
            self.model.info()
            self.classNames = ["paper"]
        
        #variables
        self.runState = self.GlobeVars.runState
        self.ImgStream = self.GlobeVars.ImgStream
        self.WaitForRoStatic = self.GlobeVars.WaitForRoStatic
        self.mode = AiMode.Searching
        
        #default set
        self.ArmState = ArmStates.middle
        self.CloseBy = False
        
        #Robot Interface Commands
        self.InterfaceDone = self.GlobeVars.RoDone
        
        #wait for first frame
        while self.runState.isSet():
            try:
                FirstFrame = self.ImgStream.popleft()
                self.imgHeight, self.imgWidth, _ = FirstFrame.shape
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
    
    def Interface(self, command, args=None, WaitForDone=False):
        #self.InterfaceDone.wait(timeout=10)
        if self.InterfaceDone.is_set():
            if args != None:
                self.GlobeVars.RoCmdArgs.append(args)
            if WaitForDone:
                self.WaitForRoStatic.set()
                self.GlobeVars.RoCmd.append(command)
                time.sleep(0.3)#give controller time to start command
                self.InterfaceDone.wait(timeout=20)
            else:
                self.GlobeVars.RoCmd.append(command)
                time.sleep(0.3)#give controller time to start command
            
            print("Interface_Completed")
            return True
        else:
            #print(f"Interfaced before Cmd was done! cmd:{command}, args:{args}")
            return False
    
    def RelToScreenSize(self, RelativePos):
        return int(self.imgWidth*RelativePos)
    
    def TurnToWad(self, RelativePos): #returns angle required to turn
        return (RelativePos - 0.5) * 120 #the fov of the cam is 120 

    def GetHorizontalBox(self, results):
        boxes = results[0].boxes
        
        XNormWidthStrt = round(float(boxes.xyxyn[0,0].cpu()), 3)
        XNormWidthEnd = round(float(boxes.xyxyn[0,2].cpu()), 3)
        return XNormWidthStrt+((XNormWidthEnd - XNormWidthStrt)/2) #gets middle of box relative its place on screen
    
    def GetVerticalBox(self, results): #from center
        boxes = results[0].boxes
        
        YNormWidthStrt = round(float(boxes.xyxyn[0,1].cpu()), 3)
        YNormWidthEnd = round(float(boxes.xyxyn[0,3].cpu()), 3)
        return YNormWidthStrt+((YNormWidthEnd - YNormWidthStrt)/2)
        
    def AiMain(self):
        self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForDone=True)
        while self.runState.isSet():
            try:
                #print("Ai Vision")
                InputImg = self.ImgStream.popleft()
                #InputImg = InputImg[120:600, 320:960] #sizing to a dataset of 640 so W:640 H:480 coming model will not need conversion because it has been trained on ep core res
                #                   Y(120-600) X(320-960)
                #for wad angle 120/2=60 320/2=160
                #Dataset collection
                if self.MainSettings.DataCollector: #merge recovery branch with main
                    if random.randint(0,1):
                        print("captured frame")
                        cv.imwrite(f'./DataSet/{time.time()}_{datetime.datetime.now().day}_{datetime.datetime.now().month}.jpg', InputImg)
                        time.sleep(0.5)
                    continue
                results = self.model(InputImg, stream=False, conf=0.6, iou=0.5 ,show=self.Visualize, verbose=False)
               
                if self.mode == AiMode.Searching:
                    if results[0]:
                        XRelPos = self.GetHorizontalBox(results)

                        #DetWPos = self.RelToScreenSize(RelPos)
                        #image = cv.circle(InputImg, (DetWPos,480), radius=5, color=(0, 0, 255), thickness=10)
                        #cv.imshow("win",image)
                        #cv.waitKey(1)

                        TurnAngle = self.TurnToWad(XRelPos)
                        #print(TurnAngle)
                        if abs(TurnAngle) > 3:
                            self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForDone=True)
                        else:
                            print(f'SWITCHING TO "EnRoute" FROM {self.mode}')
                            self.mode = AiMode.EnRoute
                    else:
                        print("Turn")
                        #self.Interface(ControllCMDs.Rotate, [45], WaitForDone=True)
                
                elif self.mode == AiMode.EnRoute:
                    if results[0]:
                        XRelPos = self.GetHorizontalBox(results)
                        YRelPos = self.GetVerticalBox(results)

                        #print(f'Y_Pos: {YRelPos}') #tweak value once arm has been set
                        if YRelPos > 0.6:  #horizontal location under 40%~
                            state = False
                            while state == False and self.runState.is_set():
                                state = self.Interface(ControllCMDs.StopWheels, WaitForDone=True)
                                time.sleep(0.01)
                            self.mode = AiMode.ArmDown
                            time.sleep(0.1)
                            print("Into pickup mode")
                            continue
                        
                        self.Interface(ControllCMDs.MoveWheels, [20], WaitForDone=False)
                    else:
                        self.Interface(ControllCMDs.MoveWheels, [-5], WaitForDone=False)
                        print(f'lost backup maybe? {YRelPos}')
                    time.sleep(0.1)
                    
                elif self.mode == AiMode.ArmDown:
                    
                    if results[0]:
                        XRelPos = self.GetHorizontalBox(results)
                        TurnAngle = self.TurnToWad(XRelPos)
                        if TurnAngle > 1:
                            self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForDone=True)
                            continue
                        print("check distance")
                        #check distance sensor for mesurements
                        #
                        #check ai if in need of correction
                        #get distance
                    
            except IndexError:
                time.sleep(0.05)
                continue
            except Exception as e:
                print(f'Error in Ai runtime {e},  Trace:{traceback.format_exc()}')
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()