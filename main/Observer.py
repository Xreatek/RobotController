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
            self.model = YOLO("./Model/MXM6V9.pt") #best for now: MXM5V9
            self.model.cuda(0)
            self.model.info()
            self.classNames = ["paper"]
        
        #variables
        self.runState = self.GlobeVars.runState
        self.ImgStream = self.GlobeVars.ImgStream
        self.WaitForRoStatic = self.GlobeVars.WaitForRoStatic
        
        self.irFloorDistance = self.MainSettings.IrFloorDistance
        
        self.DataReq = self.GlobeVars.ExpcData
        self.DataQueue = self.GlobeVars.InterfaceData
        
        self.mode = AiMode.Searching
        
        #default set
        self.cordGoal = list()
        self.curIrDistance = -1
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
    
    def Interface(self, command, args=None, WaitForStatic=False):
        #self.InterfaceDone.wait(timeout=10)
        try:
            time.sleep(0.001)
            if self.InterfaceDone.is_set():
                if args != None:
                    self.GlobeVars.RoCmdArgs.append(args)
                if WaitForStatic: #always start with a command that moves any part on the robot otherwise "static robot" will never be true. and by proxy WaitForStatic also wont.
                    self.WaitForRoStatic.set()
                    self.GlobeVars.RoCmd.append(command)
                    time.sleep(0.05)#give controller time to start command !! INCREASE INCASE OF WIFI LATENCY !!
                    self.InterfaceDone.wait(timeout=30)
                else:
                    self.GlobeVars.RoCmd.append(command)
                    time.sleep(0.05)#give controller time to start command !! INCREASE INCASE OF WIFI LATENCY !!

                print("Interface_Completed")
                return True
            else:
                #print(f"Interfaced before Cmd was done! cmd:{command}, args:{args}")
                return False
        except Exception as e:
            print(f'Command interface error {e}, Trace:{traceback.format_exc()}')
            print('Are you sure you are starting with a command that makes the robot move? Before setting WaitForStatic to True?') #read "if WaitForStatic" line for explanation
            self.runState.clear()
    
    def DataInterface(self, InList=None, WaitForStatic=False): #InList 0:Command, 1:Args, 2:Type return data should be in
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
            success = self.Interface(Command, Args, WaitForStatic)
            
            #print('Wait for data')
            Data = self.DataQueue.get(timeout=30)
            Data = str(Data)
            if Data == "ok;": #sometimes it gets mixed up this should'nt happen but in rare cases it does and this atleast catches it.
                print('recieved data mismatch this probably isnt your fault. The data the robot sent got mixed up and now it is your problem. \n(use a state check or a none check for your data.)')
                return False, None
            Data = Data[:-2] #removes " ;" (incl the space)
            if type(Data) != ReturnType.value:
                if type(ReturnType.value) == list:#lists will always return strings
                    
                    RetList = Data.split() #splits up the recieved data into a list
                    
                    if ReturnType.value[0] == int:
                        for i in RetList:
                            v = RetList.index(i)
                            i = float(i) #otherwise int transformation will error
                            RetList[v] = int(i)
                    else:
                        for i in RetList:
                            v = RetList.index(i)
                            RetList[v] = ReturnType.value[0](i) #transforms data in list to given type via enum
                            
                    return True, RetList
                else:
                    FloatData = round(float(Data), 5) #intermediary, rounding to save frame time
                    #print(f'string: {Data} type:{type(Data)}')
                    Data = ReturnType.value(FloatData)
            
        except Exception as e:
            print(f'Observer datainterface error {e}, Trace: {traceback.format_exc()}')
            self.runState.clear()
            return False, None
        return success, Data
        
        
    def RelToScreenSize(self, RelativePos):
        return int(self.imgWidth*RelativePos)
    
    def TurnToWad(self, RelativePos): #returns angle required to turn
        return (RelativePos - 0.5) * 75 #the fov of the cam is 120

    def GetHorizontalBox(self, box):
        XNormWidthStrt = round(float(box.xyxyn[0,0].cpu()), 3)
        XNormWidthEnd = round(float(box.xyxyn[0,2].cpu()), 3)
        return XNormWidthStrt+((XNormWidthEnd - XNormWidthStrt)/2) #gets middle of box relative its place on screen
    
    def GetVerticalBox(self, box): #from center
        YNormWidthStrt = round(float(box.xyxyn[0,1].cpu()), 3)
        YNormWidthEnd = round(float(box.xyxyn[0,3].cpu()), 3)
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
                cv.putText(img, f'{self.classNames[cls]}, {confidence}', org, font, fontScale, color, thickness)
        cv.imshow('Webcam', img)
        cv.waitKey(1)
        
    def GetNewFrame(self):
        while self.runState.is_set():
            try:
                InputImg = self.ImgStream.popleft()
                InputImg = InputImg[40:680, 160:1120]#sizing to a dataset of 640 so W:640 H:480 coming model will not need conversion because it has been trained on ep core res
                #print(f'Img size: {InputImg.shape}')

                results = self.model(InputImg, stream=False, conf=0.6, iou=0.70, verbose=False)
                #results2 = self.model(InputImg, stream=False, conf=0.01, iou=0.6, verbose=False) #this suprisingly works
                #results = results1 + results2

                if self.Visualize:
                    self.VisualizeFound(results, InputImg)
                
                return InputImg, results
            
            except IndexError:
                print('Failed getting frame')
                time.sleep(0.01)# to prevent freq errors

            except Exception as e:
                print(f'GetNewFrame Error: {e}, {traceback.format_exc()}')
                self.runState.clear()
                return None, None
    
    def GetTracked(self, results): #gets paper it has to rotate as little as possible for
        SellectedResult = None
        if results[0]:
            TurnAngle = 360
            LowestY = 0 #1 is highest 0 is lowest on screen
            num = 0
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    
                    x1, x2, y1, y2 = box.xyxyn[0].cpu()
                    XNormWidthStrt, YNormStart, XNormWidthEnd, YNormEnd = round(float(x1), 3), round(float(x2), 3), round(float(y1), 3), round(float(y2),3)
                    #print(f'Y Results start:{YNormStart}, end:{YNormEnd}')

                    #gets middle of box relative its place on screen
                    relBoxSizeX = (XNormWidthEnd - XNormWidthStrt)
                    XRelPos = XNormWidthStrt+(relBoxSizeX/2)
                    TempAngle = abs(self.TurnToWad(XRelPos))#if arm self.ArmOffset low or high
                    #if TempAngle < 5 and relBoxSizeX < 0.85: #if nearby center

                    if relBoxSizeX < 0.85:#85% of scren to prevent it from seleceting whole screen.
                        if TempAngle < TurnAngle and TempAngle > 5 and LowestY == 0:
                            SellectedResult = box
                            TurnAngle = TempAngle
                        elif TempAngle <= 5 and YNormEnd > LowestY:
                            #print(f'found better Y{YNormEnd}')
                            LowestY = YNormEnd
                            SellectedResult = box
                    #num += 1
                    #print(f'Result Num: {num}')
                    
        return SellectedResult
        
            
    def AiMain(self):
        cmdSuccess = self.Interface(ControllCMDs.RESET_Arm, [None], WaitForStatic=False)
        cmdSuccess, retData = self.DataInterface(GetValueCMDs.ArmPos(None, ReturnTypes.list_int))
        if cmdSuccess:
            print(f'ArmPos data: {retData} , Type:{type(retData[0])}')
        time.sleep(3) #give time to repos
        print('Observer Wake up')
        self.Interface(ControllCMDs.SetArmPos, [200,40], WaitForStatic=True) #always first set a move command before setting WaitForStatic to true (at start of connection)
        self.Interface(ControllCMDs.SetArmPos, [75,50], WaitForStatic=True)
       
        self.Interface(ControllCMDs.OpenGrip, [4], WaitForStatic=True) 
        self.Interface(ControllCMDs.CloseGrip, [2], WaitForStatic=False)
        
        self.Interface(ControllCMDs.SensorIR, ['on'], WaitForStatic=True)
        
        print('Observer woke up')
        #success, result = self.DataInterface(GetValueCMDs.GetIRDistance([1], ReturnTypes.int))
        #if success:
        #   print(f'Observer result: {result}')
        
        cmdSuccess = False
        while not cmdSuccess and self.runState.is_set():
            cmdSuccess, retData = self.DataInterface(GetValueCMDs.ChassisPos(None, ReturnTypes.list_float)) #no args
            if cmdSuccess:
                self.cordGoal = retData
                print(f'Possitional data: {retData} , Type:{type(retData[0])}')
                break
            time.sleep(0.001)
        
        #print('clapping')
        #self.Interface(ControllCMDs.EveryNonLiveComedyShowEver, [10], WaitForStatic=True) sadly not working for some reason
        #end test
        
        self.Interface(ControllCMDs.CamExposure, [CamExposure.default])
        while self.runState.isSet():
            try:
                #print("Ai Vision")
                InputImg, results = self.GetNewFrame()
                #                   Y(120-600) X(320-960)
                #for wad angle 120/2=60 320/2=160
                #Dataset collection
                if self.MainSettings.DataCollector: #merge recovery branch with main
                    if random.randint(0,1):
                        print("captured frame")
                        cv.imwrite(f'./DataSet/{time.time()}_{datetime.datetime.now().day}_{datetime.datetime.now().month}.jpg', InputImg)
                        time.sleep(0.5)#not in main run time
                    continue
                
                trackedPaper = self.GetTracked(results)
                if trackedPaper == None:
                    print("LOST PAPER")
                    
                #actual observer
                if self.mode == AiMode.Searching:
                    self.Interface(ControllCMDs.ColorChange, [150,75,0,'solid'])
                    if self.driving:
                        cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                        if not cmdSuccess: continue
                        self.driving = False
                        time.sleep(0.001)
                    if not self.ArmState == ArmStates.middle:
                        self.Interface(ControllCMDs.CloseGrip, [2])
                        self.Interface(ControllCMDs.SetArmPos, [200,40], WaitForStatic=True)
                        self.Interface(ControllCMDs.SetArmPos, [75,50], WaitForStatic=True)
                        self.ArmState = ArmStates.middle
                    if trackedPaper != None:
                        self.AllowedLostFrames = 0
                        XRelPos = self.GetHorizontalBox(trackedPaper)

                        TurnAngle = self.TurnToWad(XRelPos)
                        #print(TurnAngle)
                        if abs(TurnAngle) > 3:
                            self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForStatic=True)
                        else:
                            print(f'SWITCHING TO "EnRoute" FROM {self.mode}')
                            self.Interface(ControllCMDs.ColorChange, [25,100,25,'solid'])
                            
                            self.mode = AiMode.EnRoute
                    else:
                        #continue
                        print("Turn")
                        self.Interface(ControllCMDs.Rotate, [30], WaitForStatic=True)
                
                
                elif self.mode == AiMode.EnRoute:
                    
                    if not self.ArmState == ArmStates.middle:
                        CmdResult = self.Interface(ControllCMDs.CloseGrip, [2], WaitForStatic=False)
                        if not CmdResult: #looks wierd if still open
                            continue
                        self.Interface(ControllCMDs.SetArmPos, [200,40], WaitForStatic=True)
                        self.Interface(ControllCMDs.SetArmPos, [75,50], WaitForStatic=True)
                        self.ArmState = ArmStates.middle
                        
                    if trackedPaper != None:
                        self.AllowedLostFrames = 0
                        XRelPos = self.GetHorizontalBox(trackedPaper)
                        YEndPos = trackedPaper.xyxyn[0,3]
                        YRelPos = self.GetVerticalBox(trackedPaper)
                    
                        TurnAngle = self.TurnToWad(XRelPos)
                        if abs(TurnAngle) > 5:
                            if self.driving:
                                cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                                if not cmdSuccess: continue
                                time.sleep(0.001)
                                self.driving = False
                                continue
                            else: #standing still
                                self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForStatic=True)
                              
                        print(f'Y_Pos: {YEndPos}') #tweak value once arm has been set
                        if YEndPos > 0.8:  #horizontal location under 40%~
                            cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                            if not cmdSuccess:
                                continue
                            time.sleep(0.001)
                            self.driving = False
                            print(f'SWITCHING TO "ArmDown" FROM {self.mode}')
                            self.mode = AiMode.ArmDown
                            time.sleep(0.001)
                            continue
                        
                        CmdResult = self.Interface(ControllCMDs.MoveWheels, [20], WaitForStatic=False)
                        if CmdResult:
                            self.driving = True
                    else:
                        self.AllowedLostFrames += 1
                        if self.AllowedLostFrames >= self.MainSettings.AllowedLostFrames:
                            print("LOST PAPER RETURNING TO SEARCH")
                            print(f'SWITCHING TO "Searching" FROM {self.mode}')
                            self.mode = AiMode.Searching
                        else:
                            print('EnRoute: Setting wheels speed to -15')
                            cmdResult = self.Interface(ControllCMDs.MoveWheels, [-15], WaitForStatic=False)
                            if cmdResult:
                                self.driving = True
                    #time.sleep(0.001)
                    
                    
                elif self.mode == AiMode.ArmDown:
                    if self.ArmState != ArmStates.downOpen:
                        CmdResult = self.Interface(ControllCMDs.OpenGrip, [4], WaitForStatic=True)
                        if not CmdResult: continue;#cant pick up stuff with a closed hand
                        
                        #self.Interface(ControllCMDs.SetArmPos, [200,40], WaitForStatic=True)
                        #self.Interface(ControllCMDs.SetArmPos, [175,-95],  ic=True) #SET TO -100 ONCE CONTROLLER SCREWED
                        
                        self.Interface(ControllCMDs.SetArmPos, [190,-50], WaitForStatic=True)
                        self.Interface(ControllCMDs.SetArmPos, [183,-75], WaitForStatic=True) #SET TO -100 ONCE CONTROLLER SCREWED
                        self.Interface(ControllCMDs.SetArmPos, [183,-90], WaitForStatic=True) #the last part is always the hardest just like this.. for some fking reason
                        self.ArmState = ArmStates.downOpen
                        
                    #success, result = self.DataInterface(GetValueCMDs.GetIRDistance([1], int))
                    #if success:
                    #   print(f'Observer result: {result}')
                       
                    if trackedPaper != None:
                        if self.driving:
                            cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                            if not cmdSuccess: continue
                            self.driving = False;
                            time.sleep(0.001)
                        
                        self.AllowedLostFrames = 0
                        XRelPos = self.GetHorizontalBox(trackedPaper)
                        TurnAngle = self.TurnToWad(XRelPos)
                        if abs(TurnAngle) > 1.6:
                            self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForStatic=True)
                            continue
                        
                        #now posibly center to prop
                        if abs(TurnAngle) > 1:
                            print('TURNING FOR CORRECTION')
                            self.Interface(ControllCMDs.Rotate, [TurnAngle], WaitForStatic=True)
                            
                        cmdSuccess, returnedIRData = self.DataInterface(GetValueCMDs.GetIRDistance([1], ReturnTypes.int))
                        if not cmdSuccess or returnedIRData > self.irFloorDistance:
                            print(f"after turning paper was lost.. IRDistance:{returnedIRData} (or get ir failed:{cmdSuccess})")
                            continue
                        
                        self.curIrDistance = returnedIRData+1 #to account for errors
                        print(f'Should prop Observer result: {returnedIRData}')
                        print(f'SWITCHING TO "PickingUp" FROM {self.mode}')
                        self.mode = AiMode.PickingUp
                            
                    else:
                        self.AllowedLostFrames += 1
                        if self.AllowedLostFrames >= self.MainSettings.AllowedLostFrames:
                            print("LOST PAPER RETURNING TO SEARCH")
                            print(f'SWITCHING TO "EnRoute" FROM {self.mode}')
                            self.mode = AiMode.Searching
                        else:
                            cmdResult = self.Interface(ControllCMDs.MoveWheels, [-15], WaitForStatic=False)
                            if cmdResult:
                                self.driving = True
                                print("BACKING UP!")
                                time.sleep(0.001)
                
                
                elif self.mode == AiMode.PickingUp:
                    success, irDist = self.DataInterface(GetValueCMDs.GetIRDistance([1], ReturnTypes.int))
                    if not success or irDist > self.curIrDistance: #checking if IR didnt loose paper.
                        print(f"IR lost paper. IRDistance:{irDist}, Cur Distance:{self.curIrDistance}, ir get state:{success})")
                        if self.driving:
                            cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                            if not cmdSuccess: continue
                            self.driving = False
                            continue #otherwise rotate would be off
                        
                        if trackedPaper != None:
                            print('track paper recovery')
                            RelXPos = self.GetHorizontalBox(trackedPaper) #middle of x on box
                            TurnAngle = self.TurnToWad(RelXPos)/2 #way to close?
                            print(f'Turning angle: {abs(TurnAngle)}')
                            if abs(TurnAngle) < 3:
                                print('check if missing ir is missing')
                                #check y pos of paper if > 0.85 then close arm and move on
                                RelYPos = self.GetVerticalBox(trackedPaper)
                                print(f'RelYPos: {RelYPos}')
                                if RelYPos >= 0.7:
                                    print('bingo missing it with ir')
                                
                                continue
                            print('not in right spot sadge')
                        
                        print('CATASTOPIC FAILURE: Ir Sensor lost paper now returing to searching..')
                        print(f'SWITCHING TO "Searching" FROM {self.mode}')
                        self.mode = AiMode.Searching
                        continue
                    else: #if still on track to paper
                        print(f'IR Distance: {irDist}')
                        if irDist <= 10: #make sure paper wads are big ig change per robot
                            while self.runState.is_set():
                                if self.ArmState != ArmStates.downClosed:
                                    print("closing hand..")
                                    cmdSuccess = self.Interface(ControllCMDs.CloseGrip, [1], WaitForStatic=False)
                                    if not cmdSuccess: continue;
                                    print('hand closed')
                                    self.ArmState = ArmStates.downClosed

                                if self.driving:
                                    cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                                    if not cmdSuccess: continue
                                    self.driving = False

                                print(f'SWITCHING TO "HoldCheck" FROM {self.mode}')
                                self.mode = AiMode.HoldCheck
                                break
                        else:
                            print(f'On track too paper IrDistance:{irDist}, driving state: {self.driving}')
                            if not self.driving:
                                cmdSuccess = self.Interface(ControllCMDs.MoveWheels, [20], WaitForStatic=False)
                                if cmdSuccess:
                                    self.driving = True
                
                
                elif self.mode == AiMode.HoldCheck:
                    if self.ArmState != ArmStates.carrying:
                        self.Interface(ControllCMDs.SetArmPos, [200,40], WaitForStatic=True) 
                        CmdState = self.Interface(ControllCMDs.SetArmPos, [75,50], WaitForStatic=True)
                        if CmdState:
                            self.ArmState = ArmStates.carrying
                            continue
                        
                    print('check if holding')
                    cmdSuccess, returnedIRData = self.DataInterface(GetValueCMDs.GetIRDistance([1], ReturnTypes.int))
                    if not cmdSuccess or returnedIRData > 8:
                        #if trackedPaper != None:
                            #self.GetHorizontalBox(trackedPaper)
                            #self.GetVerticalBox(trackedPaper)
                            #if 
                        print(f"After moving arm up paper was lost.. IRDistance:{returnedIRData} (getIr success state:{cmdSuccess})")
                        print(f'SWITCHING TO "Searching" FROM {self.mode}')
                        self.mode = AiMode.Searching
                    print(f'IR distance: {returnedIRData}')
                    print(f'SWITCHING TO "ReturnCarry" FROM {self.mode}')
                    self.mode = AiMode.ReturnCarry
                
                
                elif self.mode == AiMode.ReturnCarry:
                    cmdSuccess, retCord = self.DataInterface(GetValueCMDs.ChassisPos(None, ReturnTypes.list_float)) #no args
                    if not cmdSuccess: 
                        print("problem getting cord.")
                        continue
                    
                    print(f'current possitional cord {retCord}')
                    
                    cordGoal = self.cordGoal #[0,0,180] #x,y,z
                    
                    mx = (cordGoal[0] - retCord[0])
                    my = (cordGoal[1] - retCord[1])
                    mz = (cordGoal[2] - retCord[2])

                    if (abs(cordGoal[0] - retCord[0])) > 0.5 or (abs(cordGoal[1] - retCord[1])) > 0.03:
                        #cmdSuccess = self.Interface(ControllCMDs.MoveOnCord, [mx,my,mz], WaitForStatic=True)
                        cmdSuccess = self.Interface(ControllCMDs.MoveOnCord, [mx,0,0], WaitForStatic=True)
                        cmdSuccess = self.Interface(ControllCMDs.MoveOnCord, [0,my,0], WaitForStatic=True)
                        cmdSuccess = self.Interface(ControllCMDs.MoveOnCord, [0,0,mz], WaitForStatic=True)
                    if cmdSuccess: self.driving = False
                    print('Back at storage!')
                    cmdSuccess = self.Interface(ControllCMDs.StopWheels, WaitForStatic=True)
                    if not cmdSuccess: continue
                    self.driving = False
                    self.Interface(ControllCMDs.OpenGrip, [2], WaitForStatic=True)
                    
                    time.sleep(5)
                    self.Interface(ControllCMDs.Rotate, [180], WaitForStatic=True)
                    self.ArmState = ArmStates.top
                    print('done!')
                    self.mode = AiMode.Searching
                    #self.runState.clear()
                      
                    
                    
            except IndexError:
                time.sleep(0.01)
                continue
            except Exception as e:
                print(f'Error in Ai runtime {e},  Trace:{traceback.format_exc()}')
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()