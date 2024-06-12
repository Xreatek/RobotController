import time
import robomaster
from robomaster import conn
from MyQR import myqr
from PIL import Image


QRCODE_NAME = "qrcode.png"

if __name__ == '__main__':
    
    helper = conn.ConnectionHelper()
    info = helper.build_qrcode_string(ssid="iotroam", password="Zo7rXu4dJI") #Zo7rXu4dJI
    myqr.run(words=info)
    time.sleep(1)
    img = Image.open(QRCODE_NAME)
    img.show()