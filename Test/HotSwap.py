import robomaster as rm
from robomaster import robot as IntrRobot
import traceback
import cv2 as cv

from robomaster import robot as IntrRobot
from robomaster import camera as IntrCam
from robomaster import led as IntrLed

import psutil
import time

def close_port(port):
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port:
            print(f"Closing port {port} by terminating PID {conn.pid}")
            process = psutil.Process(conn.pid)
            process.terminate()

if __name__ == '__main__':
    RoConn = IntrRobot.Robot()    
    
    
    #if RouterConn:
    IntrRobot.config.LOCAL_IP_STR = "10.249.48.12" #pc local ip
    IntrRobot.config.ROBOT_IP_STR = "10.249.48.13" #robots local ip ([10.249.48.13]:3JKCK5C00308CM serial), 
    #IntrRobot.config.DEFAULT_PROTO_TYPE = 'UDP'
    
    
    RoConn.initialize(conn_type='sta')

    version = RoConn.get_version()
    print("Robot version: {0}".format(version))
    print("ConnectionMade")
    try:
        #setup
        ep_ip = RoConn.ip
        ep_led = RoConn.led
        if ep_led:
            ep_led.set_led(comp=rm.led.COMP_ALL, r=0, g=0, b=0, effect=rm.led.EFFECT_OFF)
        
        #before hotswap
        ep_led.set_led(comp=rm.led.COMP_ALL, r=255, g=0, b=0, effect=rm.led.EFFECT_ON)
        
        
        #IntrRobot.config.ep_conf.video_stream_proto = IntrCam.protocol.DUSS_MB_TYPE_PUSH
        
        cam = RoConn.camera
        cam.start_video_stream(display=True, resolution=IntrCam.STREAM_360P)
        
        
        #IntrCam.Camera.read_cv2_image()
        #image = cam.read_cv2_image()
        #cv.imshow("Frame", image)
        #cv.waitKey(1)
        #cv.destroyAllWindows()
        
        #during hotswap
        print("Hot Swaping...")
        
        #cam.stop_video_stream()
        
        RoConn.close()
        
        #camera close
        #(CamIp, CamPort) = RoConn.camera.video_stream_addr
        #print(f"{CamIp}")
        #camport = close_port(CamPort)
        #
        #IntrCam.conn.queue.Empty() #emptying frame queue
        
        print("Closed robot")
        Reconning = True
        while Reconning:
            try:
                #time.sleep(0.01)
                
                IntrRobot.config.LOCAL_IP_STR = "10.249.48.12" #pc local ip
                IntrRobot.config.ROBOT_IP_STR = "10.249.48.13" #robots local ip ([10.249.48.13]:3JKCK5C00308CM serial), 
                #IntrRobot.config.DEFAULT_PROTO_TYPE = 'UDP'
                
                RoConn = None
                RoConn = IntrRobot.Robot()
                RoConn.initialize(conn_type='sta')
                
                ep_ip = RoConn.ip
                ep_led = RoConn.led
                
                Reconning = False
            except Exception as e:
                ep_led.set_led(comp=rm.led.COMP_ALL, r=255, g=0, b=0, effect=rm.led.EFFECT_ON)
                print("Exception: ",e)
                exit()
        
        print("Hot Swapping Done")
        #after hotswap test
        cam = RoConn.camera
        stream = cam.start_video_stream(display=True, resolution=IntrCam.STREAM_360P)
        #image = cam.read_cv2_image()
        #cv.imshow("Frame2", image)
        #cv.waitKey(0)
        
        
        print("CamGet Done")
        ep_led.set_led(comp=rm.led.COMP_ALL, r=5, g=240, b=20, effect=rm.led.EFFECT_ON)
        print("LedChange Done")
            

    except KeyboardInterrupt:
        print('Stopping')
    
    except Exception as e:
        print(traceback.format_exc())
        print("Error :", e)
    #End connection
    print("Exiting End")
    RoConn.close()
    
    