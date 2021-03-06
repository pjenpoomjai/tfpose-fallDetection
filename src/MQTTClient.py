import paho.mqtt.client as mqtt  # import the client1
import time
import argparse
import cv2
# broker.mqttdashboard.com
parser = argparse.ArgumentParser(description='Sent Image to cloud')
parser.add_argument('--room', default='somewhere', help='name room')
parser.add_argument('--camera', default='0', help='camera in or out  [1, 0]')
parser.add_argument('--show', default='0', help='show what camera see [1, 0]')
args = parser.parse_args()
broker_address = "broker.mqttdashboard.com"
#broker_address = "iot.eclipse.org"
print("creating new instance")
client = mqtt.Client('camera_z_'+args.room)  # create new instance
# client.on_message = on_message  # attach function to callback
print("connecting to broker")
client.connect(broker_address)  # connect to broker
#print("Publishing message to topic", "if/test")
message = 'end'
camera = int(args.camera)
recordTime =0
f = cv2.VideoCapture(camera)
f.set(cv2.CAP_PROP_AUTOFOCUS, 0) # turn the autofocus off
numberCount = 0
listNameImage = range(100) #when save a image from camera
round = 1
# client.publish(topic="nonine", payload= "FALL" ,qos=0)
while True:
    ret_int,img = f.read()
    if int(args.show):
        cv2.imshow('came',img)
    #if recordTime!=int(time.time()):    3 picture / sec
    if time.time() - recordTime >= 0.25:
        # print(time.time() - recordTime)
        pathName = './images/'
        picName = pathName+str(listNameImage[numberCount])+'.jpg'
        numberCount = numberCount + 1
        if numberCount >= len(listNameImage):
            numberCount = 0
        print(picName)
        cv2.imwrite(picName, img)
        recordTime = time.time()
        fileImage = open(picName,'rb')
        fileImage = fileImage.read()
        byteArr = bytearray(fileImage)
        for letter in args.room:
            byteArr.append(ord(letter))
        byteArr.append(len(args.room))
        print(time.time())
        print("Publishing message to topic", "zenbo/image")
        client.publish(topic="zenbo/image", payload= byteArr ,qos=0)
        print(args.room,',Complete : ',round)
        round = round + 1
    if cv2.waitKey(1)==ord('q'):
        f.release()
        cv2.destroyAllWindows()
        break
