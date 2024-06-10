def GetPerc(procent, s):
        s.procent = procent
        
def GetPos(ChasisC, s):
    s.CY_pos = ChasisC[0]
    s.CX_pos = ChasisC[1]
    #print(f'Y_pos: {str(ChasisC[0])}, X_pos: {str(ChasisC[1])}')
    
def GetArmPos(ArmC, s):
    NegGlitchZero = 4294967297 #this is because of a glitch cuz the moron developers of this 💩 sdk are using a unsigned int for coordinates
    NegDetect = 2147483648 #2^31 so it will catch negative numbers
    if ArmC[0] > NegDetect: 
        s.AX_pos = ArmC[0] - NegGlitchZero
    else:
        s.AX_pos = ArmC[0]
        
    if ArmC[1] > NegDetect:
        s.AY_pos =  ArmC[1] - NegGlitchZero
    else:
        s.AY_pos = ArmC[1]
    #print(f'Arm_Y:{s.AY_pos}, Arm_X:{s.AX_pos}')