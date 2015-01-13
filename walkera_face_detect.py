import cv2
import numpy as np
import urllib, base64

# opens the video stream and tracks 

stream=urllib.urlopen('http://admin:admin123@192.168.10.1:8080/?action=stream')
bytes=''
# face detection classifiers
frontalclassifier = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")     # frontal face pattern detection
DOWNSCALE = 4
bytes2 = ''
while 1:
    bytes+=stream.read(1080)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:
        jpg = bytes[a:b+2]
        bytes[a-1] = "Q"
        bytes[b+2] = "Q"
        print bytes
        bytes= bytes[b+2:]
        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
        if frame!= None:
            # detect faces
            minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
            miniframe = cv2.resize(frame, minisize)
            frontalfaces = frontalclassifier.detectMultiScale(miniframe)
            for f in frontalfaces:
                x, y, w, h = [ v*DOWNSCALE for v in f ]
                # draws bounding box
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
            if len(frontalfaces) >= 1:
                x, y, w, h = [ v*DOWNSCALE for v in frontalfaces[0] ]
                if frame.shape[1]*(2/3.) < x+w/2:# too far right
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
                    print "turn counterclockwise"
                elif frame.shape[1]*(1/3.) > x+w/2: # too far left
                    print "turn clockwise"
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0))
                else: # centered
                    print "centered"
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0))
            cv2.imshow('authenticated cam',frame)
            if cv2.waitKey(1) ==27:
                video.release()
# print f.read(1080)
exit(0)   