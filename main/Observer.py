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
            self.model = YOLO("./model/MM3V9.pt") #best for now: M2V9 imgsz:640
            self.model.cuda(0)
            self.model.info()
            self.classNames = ["paper"]
        
        #variables
        self.runState = self.GlobeVars.runState
        self.ImgStream = self.GlobeVars.ImgStream
        self.WaitForRoStatic = self.GlobeVars.WaitForRoStatic
        
        self.DataReq = self.GlobeVars.ExpcData
        self.DataQueue = self.GlobeVars.InterfaceData
        
        self.mode = AiMode.Searching
        
        #default set
        self.researchTimeout = 0
        self.ArmState = ArmStates.middle
        self.CloseBy = False
        self.driving = False
        
        #Robot Interface Commands
        self.InterfaceDone = self.GlobeVars.RoDone
        
        #wait for first frame
        while self.runState.isSet():
            try:
                FirstFrame = self.ImgStream.popleft()
                self.imgHeight, self.imgWidth, _ = FirstFrame.shape
                self.imgWidth = 960
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
        try:
            if self.InterfaceDone.is_set():
                if args != None:
                    self.GlobeVars.RoCmdArgs.append(args)
                if WaitForDone: #always start with a command that moves any part on the robot otherwise "static robot" will never be true. and by proxy waitfordone also wont.
                    self.WaitForRoStatic.set()
                    self.GlobeVars.RoCmd.append(command)
                    time.sleep(0.6)#give controller time to start command
                    self.InterfaceDone.wait(timeout=30)
                else:
                    self.GlobeVars.RoCmd.append(command)
                    time.sleep(0.3)#give controller time to start command

                print("Interface_Completed")
                return True
            else:
                #print(f"Interfaced before Cmd was done! cmd:{command}, args:{args}")
                return False
        except Exception as e:
            print(f'Command interface error {e}, Trace:{traceback.format_exc()}')
            print('Are you sure you are starting with a command that makes the robot move? Before setting WaitForDone to True?') #read "if waitfordone" line for explanation
            self.runState.clear()
    
    def DataInterface(self, InList=None, WaitForDone=False): #InList 0:Command, 1:Args, 2:Type return data should be in
        try:
            if len(InList) < 2:
                print('You forgot to give args and or excpected data type. Exiting..')
                self.runState.clear()
                return False, None
            
            Command = InList[0] #optimize in future
            Args = InList[1] #put together
            ReturnType = InList[2]
            
            print('DataInterface Start')
            self.DataReq.set()
            success = self.Interface(Command, Args, WaitForDone)
            
            print('Wait for data')
            Data = self.DataQueue.get(timeout=30)
            Data = str(Data)
            Data = Data[:-2] #removes " ;" (incl the space)
            if type(Data) != ReturnType:
                if ReturnType == list:#lists will always return strings
                    print("loop through string and append value inbetween spaces")
                    self.runState.clear()
                else:    
                    FloatData = round(float(Data), 5) #intermediary, rounding to save frame time
                    print(f'string: {Data} type:{type(Data)}')
                    Data = ReturnType(FloatData)
            
        except Exception as e:
            print(f'Observer datainterface error {e}, Trace: {traceback.format_exc()}')
            self.runState.clear()
        return success, Data
        
        
    
    
    def RelToScreenSize(self, RelativePos):
        return int(self.imgWidth*RelativePos)
    
    def TurnToWad(self, RelativePos): #returns angle required to turn
        return (RelativePos - 0.5) * 110 #the fov of the cam is 120 

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
    
    def VisualizeFound(self, results, img):
        for r in results:
            boxes = r.boxes

            for box in boxes:
                # bounding box
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values
                # put box in cam
                cv.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
                # confidence
                confidence = math.ceil((box.conf[0]*100))/100
                #print("Confidence --->",confidence)
                # class name
                cls = int(box.cls[0])
                # object details
                org = [x1, y1]
                font = cv.FONT_HERSHEY_SIMPLEX
                fontScale = 0.6
                color = (255, 0, 0)
                thickness = 2
                cv.putText(img, f'{self.classNames[cls]}, Conf:{confidence}', org, font, fontScale, color, thickness)
        cv.imshow('Webcam', img)
        cv.waitKey(1)
        
    def AiMain(self):
        print('Observer Wake up')
        self.Interface(ControllCMDs.SetArmPos, [180,0], WaitForDone=True) #always start with move command
        self.Interface(ControllCMDs.SetArmPos, [120,40], WaitForDone=True)
        
        self.Interface(ControllCMDs.SensorIR, ['on'], WaitForDone=True)
        #temp testing things
        time.sleep(4)
        print('IrDistance')
        while self.runState.is_set():
            #self.Interface(ControllCMDs.GetIRDistance, [1], WaitForDone=True)
            print("start req")
            success, result = self.DataInterface(GetValueCMDs.GetIRDistance([1], int))
            if success:
                print(f'Observer result: {result}')
            time.sleep(3)
        #time.sleep(4)
        #print('clapping')
        #self.Interface(ControllCMDs.EveryNonLiveComedyShowEver, [10], WaitForDone=True)
        
        #time.sleep(4)
        #end test
        #print('moving arm')
        
        
        self.Interface(ControllCMDs.CamExposure, [CamExposure.high])
        while self.runState.isSet():
            try:
                #print("Ai Vision")
                InputImg = self.ImgStream.popleft()
                InputImg = InputImg[0:720, 160:1120] #sizing to a dataset of 640 so W:640 H:480 coming model will not need conversion because it has been trained on ep core res
                #print(f'Img size: {InputImg.shape}')
                #                   Y(120-600) X(320-960)
                #for wad angle 120/2=60 320/2=160
                #Dataset collection
                if self.MainSettings.DataCollector: #merge recovery branch with main
                    if random.randint(0,1):
                        print("captured frame")
                        cv.imwrite(f'./DataSet/{time.time()}_{datetime.datetime.now().day}_{datetime.datetime.now().month}.jpg', InputImg)
                        time.sleep(0.5)
                    continue
                results = self.model(InputImg, stream=False, conf=0.6, iou=0.5, verbose=False)
                if self.Visualize:
                    self.VisualizeFound(results, InputImg)
                
                #actual observer
                if self.mode == AiMode.Searching:
                    if not self.ArmState == ArmStates.middle:
                        self.Interface(ControllCMDs.SetArmPos, [180,0], WaitForDone=True)
                        self.Interface(ControllCMDs.SetArmPos, [120,40], WaitForDone=True)
                        self.ArmState = ArmStates.middle
                    if results[0]:
                        self.AllowedLostFrames = 0
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
                        continue
                        #print("Turn")
                        #self.Interface(ControllCMDs.Rotate, [45], WaitForDone=True)
                
                elif self.mode == AiMode.EnRoute:
                    if results[0]:
                        self.AllowedLostFrames = 0
                        XRelPos = self.GetHorizontalBox(results)
                        YRelPos = self.GetVerticalBox(results)

                        print(f'Y_Pos: {YRelPos}') #tweak value once arm has been set
                        if YRelPos > 0.65:  #horizontal location under 40%~
                            state = False
                            while state == False and self.runState.is_set():
                                state = self.Interface(ControllCMDs.StopWheels, WaitForDone=True)
                                time.sleep(0.01)
                                print(f'SWITCHING TO "EnRoute" FROM {self.mode}')
                                self.mode = AiMode.ArmDown
                            time.sleep(0.1)
                            continue
                        
                        self.Interface(ControllCMDs.MoveWheels, [20], WaitForDone=False)
                    else:
                        self.AllowedLostFrames += 1
                        if self.AllowedLostFrames >= self.MainSettings.AllowedLostFrames:
                            print("LOST PAPER RETURNING TO SEARCH")
                            #self.mode = AiMode.Searching
                        else:
                            self.Interface(ControllCMDs.MoveWheels, [-10], WaitForDone=False)
                    time.sleep(0.1)
                    
                elif self.mode == AiMode.ArmDown:
                    if self.driving:
                        while state == False and self.runState.is_set(): 
                            state = self.Interface(ControllCMDs.StopWheels, WaitForDone=True)
                            time.sleep(0.01)
                    if not self.ArmState == ArmStates.down:
                        self.Interface(ControllCMDs.SetArmPos, [180,0], WaitForDone=True)
                        self.Interface(ControllCMDs.SetArmPos, [180,-90], WaitForDone=True)
                        self.ArmState = ArmStates.down
                    if results[0]:
                        self.AllowedLostFrames = 0
                        XRelPos = self.GetHorizontalBox(results)
                        TurnAngle = self.TurnToWad(XRelPos)/1.1
                        if abs(TurnAngle) > 3:
                            self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForDone=True)
                            continue
                        print("check distance")
                    else:
                        self.AllowedLostFrames += 1
                        if self.AllowedLostFrames >= self.MainSettings.AllowedLostFrames:
                            print("LOST PAPER RETURNING TO SEARCH")
                            #self.mode = AiMode.Searching
                        else:
                            self.driving = True
                            self.Interface(ControllCMDs.MoveWheels, [-8], WaitForDone=False)
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