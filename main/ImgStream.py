import traceback
import queue
import socket
import libmedia_codec
import numpy

class Stream:
    def __init__(self, RawStream, stoppedStream, MainSettings, GlobVars) -> None:
        self.MainSettings = MainSettings
        self.GlobVars = GlobVars
        
        self.runState = self.GlobVars.runState
        self.ConnState = self.GlobVars.ConnState
        
        self.streamStopped = stoppedStream
        
        self.ImgStream = self.GlobVars.ImgStream
        self.RawStream = RawStream
            
        
        self.MediaStream()
    
    def MediaStream(self):
        CamAddr = (self.MainSettings.RobotIp, int (40921))
        CamStream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        CamStream.connect(CamAddr)
        CamStream.settimeout(10)

        self.streamStopped.clear() #starting stream
        try:
            decoder = libmedia_codec.H264Decoder()
            while self.ConnState.isSet() and self.runState.isSet():
                try:
                    buf = CamStream.recv(1024) #gets buf
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
        except Exception as e:
            print(f'Error in decoding stream: {e}, {traceback.format_exc()}')
        print("STREAM CLOSING")
        CamStream.close()
        self.streamStopped.set()
                
if __name__ == '__main__':
    import RuntimeOverseer
    RuntimeOverseer.ThreadMasterClass()
            