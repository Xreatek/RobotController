import traceback
import queue
import socket
import libmedia_codec
import numpy

import time
import cv2

class Stream:
    def __init__(self, RawStream, MainSettings, GlobVars) -> None:
        self.MainSettings = MainSettings
        self.GlobVars = GlobVars
        
        self.runState = self.GlobVars.runState
        
        self.ImgStream = self.GlobVars.ImgStream
        self.RawStream = RawStream
            
        
        self.MediaStream()
    
    def MediaStream(self):
        CamAddr = (self.MainSettings.RobotIp, int (40921))
        CamStream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        CamStream.connect(CamAddr)

        decoder = libmedia_codec.H264Decoder()
        RecvBuf = b''
        while self.runState.is_set():
            try:
                buf = CamStream.recv(2**16) #gets buf
                RecvBuf += buf #adds on buffer
                Frames = decoder.decode(RecvBuf)#decodes buffer
                availFrames = len(Frames)
                if availFrames > 0:
                    Frame_Data = Frames[availFrames-1]
                    (frame, width, height, ls) = Frame_Data
                    if frame:
                        frame = numpy.fromstring(frame, dtype=numpy.ubyte, count=len(frame), sep='')
                        frame = (frame.reshape((height, width, 3))) 
                        self.RawStream.append(frame)
                        RecvBuf = b''

            except queue.Full:
                print(f"ImageCamera queue got filled up that isnt supposed to happen.. Exiting...")# Trace:{traceback.format_exc()}") #unnecessary
                self.runState.clear()
            except socket.error as e:
                print(f'Socket Error :{e} Traceback: {traceback.print_exc()}')
                self.runState.clear()
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()
            