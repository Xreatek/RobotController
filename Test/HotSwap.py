import robomaster as rm
from robomaster import robot as IntrRobot
import traceback

from robomaster import robot as IntrRobot
from robomaster import camera as IntrCam
from robomaster import led as IntrLed

import time

if __name__ == '__main__':
        
    #if RouterConn:
    IntrRobot.config.LOCAL_IP_STR = "10.249.48.12" #pc local ip
    IntrRobot.config.ROBOT_IP_STR = "10.249.48.13" #robots local ip ([10.249.48.13]:3JKCK5C00308CM serial), 
    #IntrRobot.config.DEFAULT_PROTO_TYPE = 'UDP'
    
    RoConn = IntrRobot.Robot()
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
        
        #during hotswap
        print("Hot Swaping...")
        
        RoConn.close()
        print("Closed robot")
        Reconning = True
        while Reconning:
            try:
                #time.sleep(0.01)
                
                IntrRobot.config.LOCAL_IP_STR = "10.249.48.12" #pc local ip
                IntrRobot.config.ROBOT_IP_STR = "10.249.48.13" #robots local ip ([10.249.48.13]:3JKCK5C00308CM serial), 
                #IntrRobot.config.DEFAULT_PROTO_TYPE = 'UDP'

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
        ep_led.set_led(comp=rm.led.COMP_ALL, r=5, g=240, b=20, effect=rm.led.EFFECT_ON)
            

    except KeyboardInterrupt:
        print('Stopping')
    
    except Exception as e:
        print(traceback.format_exc())
        print("Error :", e)
    #End connection
    print("Exiting End")
    RoConn.close()
    
    