import threading


#-runtime observer
#starts components
#sets robot controlls in a loop to see if it stopped and if true then
#   it will reinstate the robot controlls(observer should not be effected since it will just have to wait a bit longer on its image but no variables should be lost.)
#(if needed same could be done for observer)

#-robot controlls
#make connection then return
#main robot controller sets up subscribers video stream etc
#robot controller in loop waiting for commands and updating current image when ai isnt busy

#-ai observer
#waits untill connection is made
#if in search mode (optional: wandering)
#   waits for new camera frame
#   then if something is found it calculates the rotation angle and sends that as a command to the robot as angle to turn (mean while no updates to camera(maybe))
#   !once rotated as calculated mode is set to confirm mode 

#elif in confirm mode 
#   crop to only see directly infront of robot if something
#   if paper is detected then: slowly move forward
#       When paper is lost set arm into grabbing mode
#       !then mode is set to preGrabConfirmMode
#   else (if no paper is detected in crop mode)
#       !mode is set to search mode

#elif in preGrabConfirmMode
#   check if paper is still detected and right infront of the robot
#   if not^ then correct rotation until paper is right infront of the camera
#   !when succeeded go into grabbing mode  

#elif in grabbingMode
#   drive towards paper checking each time if angle is still in acceptable margin of error 
#   if inside margin of error
#       continue forwards untill distance sensor output is close enough or ai camera detects paper inside claw area
#       !then close claw and go to objectRetrival
#   else when outside of margin of error
#       Correct papers angle offset compared to the robots

#elif objectRetrival
#   Set arm into carry mode and move towards paper container
#   if at container align robot with box so it can drop inside
#       when aligned robot will drop held paper
#       then robot rotates 180 degrees
#       !Then robot is set back to search mode


    