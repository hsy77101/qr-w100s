import urllib2
import time
import cv2
import numpy as np
import threading
import Tkinter as tk
from PIL import Image, ImageTk
class Video:
    def __init__(self):
        self.onkeypress = False
        self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        self.detectFaces = False
        self.DOWNSCALE = 4
        self.frontalclassifier = False
        
        self.top_level_url = "http://192.168.10.1:8080"
        self.password_mgr.add_password(None, self.top_level_url, 'admin', 'admin123')

        self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
        self.opener = urllib2.build_opener(self.handler)
        self.opener.open("http://192.168.10.1:8080/?action=stream")
        urllib2.install_opener(self.opener)
        print 'opening url'
        
    def setClassifier(self, classifierxml):
        self.frontalclassifier = cv2.CascadeClassifier(classifierxml)
    
    def readframes(self, recv_buffer=4096, delim='\n'):
        buffer = ''
        data = True
        self.reading = True
        self.state = 0
        ts = 0
        print ' in readframes'
        while data and self.reading:
            data = self.resp.read(recv_buffer)
            buffer += data

            while buffer.find(delim) != -1:
                line, buffer = buffer.split("\n", 1)
                if self.state==0:
                    if line[0:20] == "--boundarydonotcross":
                        self.state = 1
                elif self.state==1:
                    #print line.split(":")
                    self.state = 2
                elif self.state==2:
                    #print line
                    datalength = int(line.split(":")[1][1:-1])
                    self.state = 3
                    #print "datalen", datalength
                    #print buffer
                elif self.state==3:
                    self.state = 4
                    
                    timestamp = float(line.split(":")[1][1:-1])
                    #print "timestamp:", timestamp
                    #print "lag", timestamp - ts, 1/( timestamp - ts)
                    ts = timestamp
                else:
                    while(len(buffer) < datalength):
                        bytes_remaining = datalength - len(buffer)
                        data = self.resp.read(bytes_remaining)
                        buffer += data
                    self.state = 0
                    yield buffer
        return


    def loop(self):
        self.resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")
        #print resp.read(10)
        size = 0
        a = time.time()
        n = 1
        avg = 0
        x = 0

        for frame in self.readframes():
          
            #dump = open('dump/dumpframe'+str(x),'w')
            #x = x+1
            #dump.write(frame)
            #t = time.time()
            #fps = 1/(t-a)
            #print "frame len: ", len(frame)
            #print "FPS: ", fps
            #a = t

            #a = frame.find('\xff\xd8')
            #b = frame[-20:].find('\xff\xd9')
            #if b != -1:
            #    frame = frame[0:-20+b]
            #print a, b
            try:
                i = cv2.imdecode(np.fromstring(frame+'\xff\xd9', dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                # i = cv2.imdecode(np.fromstring(frame, dtype=np.uint8),cv2.IMREAD_COLOR)
                
                if (self.detectFaces and self.frontalclassifier):
                # detect faces
                    minisize = (i.shape[1]/self.DOWNSCALE,i.shape[0]/self.DOWNSCALE)
                    miniframe = cv2.resize(i, minisize)
                    frontalfaces = self.frontalclassifier.detectMultiScale(miniframe)
                    for f in frontalfaces:
                        x, y, w, h = [ v*self.DOWNSCALE for v in f ]
                    #     # draws bounding box
                        cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255))
                    if len(frontalfaces) >= 1:
                        x, y, w, h = [ v*self.DOWNSCALE for v in frontalfaces[0] ]
                        if i.shape[1]*(2/3.) < x+w/2:# too far right
                            cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255))
                    #         # print "turn counterclockwise"
                        elif i.shape[1]*(1/3.) > x+w/2: # too far left
                    #         # print "turn clockwise"
                            cv2.rectangle(i, (x,y), (x+w,y+h), (0,255,0))
                        else: # centered
                    #         # print "centered"
                            cv2.rectangle(i, (x,y), (x+w,y+h), (255,0,0))
                    #     print (x+w/2.),(y+h/2.),(w**2+h**2)**0.5
                    # cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = PIL.Image.fromarray(cv_image)
                    tk_image = PIL.ImageTk.PhotoImage(image=pil_image)
                    image_label.configure(image=tk_image)
                    image_label._image_cache = tk_image  # avoid garbage collection
                    root.update()

                # cv2.imshow('i',i)


                # if (self.onkeypress):
                #     key = cv2.waitKey(1)
                #     if (key != -1):
                #         self.onkeypress(key)
                # if cv2.waitKey(1) ==27:
                #     self.reading = False
                #     del self.myThread
                #     exit(0)
                
            except Exception, e:
                # print "EXCEPTION:", e   
                pass
            #if b==-1:
            #    print "HAS -1 b", x
            #if a!=-1 and b!=-1:
            #    jpg = frame[a:b+2]
            #    bytes= frame[b+2:]
            
            #x = x+1
            #if (x==120):           
            #    x = 0
            #    print frame
 
    def setKeypress(self, func):
        self.onkeypress = func
        
    def startThread(self):
        self.myThread = threading.Thread(target=self.loop)
        self.myThread.start()

def update_all(root, image_label):
    if root.quit_flag:
        root.destroy()  # this avoids the update event being in limbo
    else:
        # update_image(image_label)
        root.after(1, func=lambda: update_all(root, image_label))

if __name__ == '__main__':
    root = tk.Tk()
    setattr(root, 'quit_flag', False)
    def set_quit_flag():
        root.quit_flag = True
    root.protocol('WM_DELETE_WINDOW', set_quit_flag)
    global image_label
    image_label = tk.Label(master=root)  # label for the video frame
    image_label.pack()
    v = Video()
    v.setClassifier("haarcascade_frontalface_alt2.xml")
    v.startThread()
    root.after(0, func=lambda: update_all(root, image_label))
    root.mainloop()