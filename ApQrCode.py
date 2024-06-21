import time
import robomaster
from robomaster import conn
from MyQR import myqr
from PIL import Image


QRCODE_NAME = "qrcode.png"

if __name__ == '__main__':
    
    helper = conn.ConnectionHelper()
    info = helper.build_qrcode_string(ssid="", password="") #Will say failed but that isnt true if you are on a IoT network from school. You need the IP the robots got to connect.
    myqr.run(words=info)
    time.sleep(1)
    img = Image.open(QRCODE_NAME)
    img.show()