import traceback
import queue
import socket
import libmedia_codec
import numpy

class Stream:
    def __init__(self, RawStream, MainSettings, GlobVars) -> None:
        self.MainSettings = MainSettings
        self.GlobVars = GlobVars
        
        self.runState = self.GlobVars.runState
        self.ConnState = self.GlobVars.ConnState
        
        self.ImgStream = self.GlobVars.ImgStream
        self.RawStream = RawStream
            
        
        self.MediaStream()
    
    def MediaStream(self):
        CamAddr = (self.MainSettings.RobotIp, int (40921))
        CamStream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        CamStream.connect(CamAddr)
        CamStream.settimeout(10)

        decoder = libmedia_codec.H264Decoder()
        while self.ConnState.is_set():
            try:
                buf = CamStream.recv(2048) #gets buf
                Frames = decoder.decode(buf)#decodes buffer
                availFrames = len(Frames)
                if availFrames > 0:
                    Frame_Data = Frames[0]
                    (frame, width, height, ls) = Frame_Data
                    if frame:
                        frame = numpy.fromstring(frame, dtype=numpy.ubyte, count=len(frame), sep='')
                        frame = (frame.reshape((height, width, 3)))
                        self.RawStream.append(frame)

            except socket.error as e:
                print(f'Socket Error :{e} Traceback: {traceback.format_exc()}')
                self.GlobVars.ConnState.clear()
            except Exception as e:
                print(f'Stream Exectption {e}, Trace:{traceback.format_exc()}')
                self.runState.clear()
        CamStream.close()
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()
            