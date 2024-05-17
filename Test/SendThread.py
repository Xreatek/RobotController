import traceback
import time

def sendfunc(running, ContinueEvent, MessageQueue, String): #this is a test of threading and how it works
    i=0
    while running.is_set():
        
        ContinueEvent.wait() #waits untill true
        print("Balls", str(String))
        try:
            if (MessageQueue.qsize() < 2): #if queue is bellow 2 (acceptable fullness)
                MessageQueue.put_nowait(i)
                i+=1
            else:
                try:
                    MessageQueue.get_nowait()
                    MessageQueue.put_nowait(i)
                    i+=1
                except:
                    MessageQueue.put_nowait(i)
                    print("Queue read in time it took too empty an entry")
                    
        except Exception as e:
            print(traceback.format_exc())
            print("Sendfunc ran into error :", e)
            running.running.clear()
         
        time.sleep(0.5) #disable continue event and enable sleep too make simulate a function that recives data seperate from the main thread 
        #ContinueEvent.clear() #Resets the Continue event to false