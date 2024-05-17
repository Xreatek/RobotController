import threading
import queue
import time
import traceback

import SendThread

running = threading.Event() #as an event its easier to disable all threads check performance of this at later date
running.set()

MessageQueue = queue.Queue(2) #alternate so that there always will be one in the queue
ContinueEvent = threading.Event()
String = "Lightness"

#ThreadName = thread.Thread(target=FUNCTION, args=(VARS))
rt = threading.Thread(target=SendThread.sendfunc, args=(running, ContinueEvent, MessageQueue, String))
rt.start()

#make basic queue for sending data
#https://pythonforthelab.com/blog/handling-and-sharing-data-between-threads/

while running.is_set():
    try:
        time.sleep(3)
        print("MainLoop")
        
        ContinueEvent.set() #sets event to true

        try: #see if a new message/frame is present for proccesing
            MessageTooHandle = MessageQueue.get_nowait()
            print("msg num :",str(MessageTooHandle)) #gets an item if there is none it will wait (get_nowait) will not it will raise an error instead
        except Exception as e:
            print("No message num in queue")
        
        
    except KeyboardInterrupt:
        running.clear()
    
    except Exception as e:
        print(traceback.format_exc())
        print("error :", e)
        running.clear()
    