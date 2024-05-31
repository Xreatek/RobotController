import robomaster as rm
import traceback
from robomaster import robot

import time

if __name__ == '__main__':
    
    RouterConn = True #connected via routed:True, Direct Connection:False
    
    if RouterConn: #Note: school network isnt supported (use hotspot)
        robot.config.LOCAL_IP_STR = "10.249.48.12" #pc local ip
        robot.config.ROBOT_IP_STR = "10.249.48.13" #robots local ip ([10.249.48.13]:3JKCK5C00308CM serial), 
        
        ep_robot = robot.Robot()
        ep_robot.initialize(conn_type='sta', proto_type='UDP')
    else:
        ep_robot = robot.Robot()
        ep_robot.initialize(conn_type='ap') 

    version = ep_robot.get_version()
    print("Robot version: {0}".format(version))
    print("ConnectionMade?")
    try:
        
        ep_ip = ep_robot.ip
        print(ep_ip)
        
        ep_led = ep_robot.led
        for i in range(2):
            ep_led.set_led(comp=rm.led.COMP_ALL, r=255, g=255, b=255, effect=rm.led.EFFECT_ON)
            time.sleep(1)
            ep_led.set_led(comp=rm.led.COMP_ALL, r=5, g=240, b=20, effect=rm.led.EFFECT_ON)
            time.sleep(1)
            

    except KeyboardInterrupt:
        print('Stopping')
    
    except Exception as e:
        print(traceback.format_exc())
        print("Error :", e)
    if ep_led:
        ep_led.set_led(comp=rm.led.COMP_ALL, r=0, g=0, b=0, effect=rm.led.EFFECT_OFF)
    #End connection
    ep_robot.close()
    
    