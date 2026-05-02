import argparse, logging
import ffmpeg
import sys
import pytesseract

import sys
import distance
import time
from imutils.video import VideoStream
import ffmpeg
import cv2
import numpy as np
import os
import re
import fnmatch
import datetime
import imutils
import time
import argparse
import glob
import pprint

import subprocess
import zipfile
from tensorflow.keras.preprocessing.image  import load_img, save_img, img_to_array
import scipy
from PIL import Image
import imagehash
import tempfile
from contures import *
from PIL import ImageEnhance

from keras import backend as K
from os.path import isfile, join, basename

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def natural_sort(l):
  convert = lambda text: int(text) if text.isdigit() else text.lower()
  alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
  return sorted(l, key = alphanum_key)
def recursive_glob(rootdir='.', pattern='jpg'):
  frame_list = [os.path.join(looproot, filename)
    for looproot, _, filenames in os.walk(rootdir)
      for filename in filenames
        if fnmatch.fnmatch(filename, pattern)]

  reture = []
  for frame in frame_list:
    reture.append(os.path.dirname(frame))

  return np.unique(reture)


def sharpen(image):
    kernel = np.array([[-1,-1,-1],
                           [-1, 10.7,-1],
                           [-1,-1,-1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened

def missing_indexes(seq):
  seq.append(0)
  res = [ele for ele in range(max(seq)+1) if ele not in seq]
  return res

def fs_sort(files):
  files = natural_sort(files)
  return files
def search_frames(path):
  files = []
  for r, d, f in os.walk(path):
    print(r)
    return recursive_glob(r,'jpg')


def extract_from_img(file_name):
        image=cv2.imread(file_name)
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        return gray
def resize_img(img, scale):
    return scipy.ndimage.zoom(img, scale, order=1)

def add_corners(image):
  imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  ret, thresh = cv2.threshold(imgray, 0, 25, 0)
  contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
  cnt = contours
  cv2.drawContours(image, [cnt], 0, (0,255,0), 3)

  #cv2.drawContours(image, cnt, -1, (0,255,0), 1)
  return image

def storeClipp(image,path, name, c,date):

  (x, y, w, h) = cv2.boundingRect(c)
  ROI = image[y:y+h, x:x+w]
  go = h * w
  check = y+h



  im = '{}/{}'.format(path,name)
  cv2.imwrite(im, ROI)
  hash = imagehash.average_hash(Image.open(im))
  os.remove(im)
  im2 = '{}/{}_{}'.format(path,hash,name)
  cv2.imwrite(im2,ROI)
  #os.remove(im2)

  return "{}".format(hash)


def write_frame(process2, frame):
    logger.debug('Writing frame')
    process2.stdin.write(
        frame
        .astype(np.uint8)
        .tobytes()
    )



def extract_corners(image , file_name,ROI_number):
    frame = image
    base_dir,base_name = os.path.split(file_name)#.replace(".jpg","")

    #frame = resize_img(image, 0.5)
    imgray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(imgray, 127, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    cnts = contours
#    ROI_number = 0
    clipps = args.get('clipps')
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ROI = frame[y:y+h, x:x+w]
        go = h * w
        check = y+h
        # if the contour is too small, ignore it
        if go < 500:
            continue


        # if the contour is too small, ignore it
        if check > 40900:
            continue

        # compute the bounding box for the contour, draw it on the frame,
        # and update the text

        cv2.imwrite('{}/{}_{}_{}_{}_{}.png'.format(clipps,base_name,x,y,w,h), ROI)
        ROI_number += 1

        #cv2.drawContours(image, [cnt], 0, (0,255,0), 3)
        cv2.drawContours(image, cnts, -1, (0,255,0), 1)

        image = resize_img(image,2)

    return image
# Resizes a image and maintains aspect ratio
def maintain_aspect_ratio_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    try:
        # Grab the image size and initialize dimensions
        dim = None
        (h, w) = image.shape[:2]
        # Return original image if no need to resize
        if width is None and height is None:
            return image
        # We are resizing height if width is none
        if width is None:
            # Calculate the ratio of the height and construct the dimensions
            r = height / float(h)
            dim = (int(w * r), height)
        # We are resizing width if height is none
        else:
            # Calculate the ratio of the width and construct the dimensions
            r = width / float(w)
            dim = (width, int(h * r))
        # Return the resized image
        image = cv2.resize(image, dim, interpolation=inter)
    except:
       pass

    return image
def centroid_histogram(clt):
    # grab the number of different clusters and create a histogram
    # based on the number of pixels assigned to each cluster
    #numLabels = np.arange(0, len(np.unique(clt.labels_)) + 1)
    #(hist, _) = np.histogram(clt.labels_, bins = numLabels)

    # normalize the histogram, such that it sums to one
    #hist = hist.astype("float")
    #hist /= hist.sum()

    # return the histogram
    return clt


def plot_histogram(image, title, mask=None):
    # split the image into its respective channels, then initialize
    # the tuple of channel names along with our figure for plotting
    chans = cv2.split(image)
    colors = ("b", "g", "r")
    plt.figure()
    plt.title(title)
    plt.xlabel("Bins")
    plt.ylabel("# of Pixels")
    # loop over the image channels
    for (chan, color) in zip(chans, colors):
        # create a histogram for the current channel and plot it
        hist = cv2.calcHist([chan], [0], mask, [256], [0, 256])
        plt.plot(hist, color=color)
        plt.xlim([0, 256])

    return hist
        
def drawHistogram(img,color=True,windowName='drawHistogram'):
    h = numpy.zeros((300,256,30))

    bins = numpy.arange(256).reshape(256,1)

    if color:
            channels =[ (255,0,0),(0,255,0),(0,0,255) ];
    else:
            channels = [(255,255,255)];

    for ch, col in enumerate(channels):
            hist_item = cv2.calcHist([img],[ch],None,[256],[0,255])
            cv2.normalize(hist_item,hist_item,0,255,cv2.NORM_MINMAX)
            hist=numpy.int32(numpy.around(hist_item))
            pts = numpy.column_stack((bins,hist))
            #if ch is 0:
            cv2.polylines(img,[pts],True,col,50)

    h=numpy.flipud(h)

    return h #cv2.imshow(windowName,h);
def plot_colors(hist, centroids):
    # initialize the bar chart representing the relative frequency
    # of each of the colors
    bar = np.zeros((50, 300, 3), dtype = "uint8")
    startX = 0

    # loop over the percentage of each cluster and the color of
    # each cluster
    for (percent, color) in zip(hist, centroids):
        # plot the relative percentage of each cluster
        endX = startX + (percent * 300)
        cv2.rectangle(bar, (int(startX), 0), (int(endX), 50),
            color.astype("uint8").tolist(), -1)
        startX = endX

    # return the bar chart
    return bar
def rescale_by_height(image, target_height, method=cv2.INTER_LANCZOS4):
    """Rescale `image` to `target_height` (preserving aspect ratio)."""
    w = int(round(target_height * image.shape[1] / image.shape[0]))
    return cv2.resize(image, (w, target_height), interpolation=method)
def rescale_by_width(image, target_width, method=cv2.INTER_LANCZOS4):
    """Rescale `image` to `target_width` (preserving aspect ratio)."""
    h = int(round(target_width * image.shape[0] / image.shape[1]))
    return cv2.resize(image, (target_width, h), interpolation=method)

def count_colours(src):
    unique, counts = np.unique(src, return_counts=True)
    print(counts.size)
    return counts.size

def getKeysByValues(dictOfElements, listOfValues):
    listOfKeys = list()
    listOfItems = dictOfElements.items()
    for item  in listOfItems:
        if item[1] in listOfValues:
            listOfKeys.append(item[0])
    return  listOfKeys

def searchSub(myDict,search):
    listOfKeys = list()
    listOfItems = myDict.values()
    key_list = myDict.keys()
    for item  in listOfItems:
        match=re.search(r''+search+'', item)
        if match:
            print("item:{} key:{}".format(item,get_key(myDict,item)))
            return get_key(myDict,item)

def get_key(myDict,val):
    for key, value in myDict.items():
         if val == value:
             return key
         else:
            return  [[0,240,0],100]

def closest_item(sdict, key):
    if len(sdict) == 0:
        raise KeyError('No items in {sdict.__class__.__name__}')

    if len(sdict) == 1:
        return next(iter(sdict.items()))

    idx_before = next(sdict.irange(minimum=key), None)
    idx_after = next(sdict.irange(maximum=key, reverse=True), None)

    if idx_before is None:
        idx = idx_after

    elif idx_after is None:
        idx = idx_before
    else:
        idx = min(idx_before, idx_after, key=lambda x: abs(x - key))

    return idx, sdict[idx]
def get_indexes_min_value(l):
    min_value = min(l)
    if l.count(min_value) > 1:
        return [i for i, x in enumerate(l) if x == min(l)]
    else:
        return l.index(min(l))


def supperEnhance(image):


  new_image = np.zeros(image.shape, image.dtype)
  alpha = 1.0 # Simple contrast control
  beta = 0    # Simple brightness control
  # Initialize values
  print(' Basic Linear Transforms ')
  print('-------------------------')
  try:
      alpha = float(1.9)
      beta = int(20)
  except ValueError:
      print('Error, not a number')
  # Do the operation new_image(i,j) = alpha*image(i,j) + beta
  # Instead of these 'for' loops we could have used simply:
  # new_image = cv.convertScaleAbs(image, alpha=alpha, beta=beta)
  # but we wanted to show you how to access the pixels :)
  for y in range(image.shape[0]):
      for x in range(image.shape[1]):
          for c in range(image.shape[2]):
              new_image[y,x,c] = np.clip(alpha*image[y,x,c] + beta, 0, 255)

  return new_image


def cSat2(count):

    return slotmap

def cSat(c , frame, file_name,ROI_number,messure,bg,slots,n,hcontainer,org_image,cx,path,i,slotmap,gdate):
    (x, y, w, h) = cv2.boundingRect(c)
    image_width = image.shape[0]
    image_height = image.shape[1]
    base_dir,base_name = os.path.split(file_name)#.replace(".jpg","")

    sat=None
    try:
        if len(base_name) == 3:
            date = base_name.split("_")[0]
            time = base_name.split("_")[1]
            sat  = base_name.split("_")[2].replace('.jpg','')
        else:
            date = base_name.split("_")[0]
            time = base_name.split("_")[1]
            res  = base_name.split("_")[2]
            sat  = base_name.split("_")[3].replace('.jpg','')
    except:
        pass


    clipps = args.get('clipps')
    ROI = frame[y:y+h, x:x+w]
    go = h * w
    check = y+h
    check2 = x
    n_red_pix = np.sum(ROI == 180)
    n_white_pix = np.sum(ROI == 255)
    itr = 0
    wp = go / 100
    wp = n_white_pix / wp
    if (y < 940):
        ROIgray = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)



        if ((w / 1.02> h) or (h / 1.02> w) and (x>0 and y>0)):

                #



            if w>h:
                pc = int(w/3)
            else:
                pc = int(h/3)




            x=x-(16*pc)
            y=y-(16*pc)
            w=w+(22*pc)
            h=h+(22*pc)
            ROIz=ROI

            datex = image[1040:1040+40, 220:220+320]
            #cv2.namedWindow(date)
            #äcv2.resizeWindow(date, 500, 500)
            #cv2.imshow("x",date)

            if sat=="c3" or sat == "c2":
                ROIx = org_image[(y*1):(y*1)+(h*1), (x*1):(x*1)+(w*1)]
            elif sat == "0131":
                ROIx = org_image[(y*2):(y*2)+(h*2), (x*2):(x*2)+(w*2)]
            else:
                ROIx = org_image[(y*4):(y*4)+(h*4), (x*4):(x*4)+(w*4)]



            """
            path = os.path.join(args.get('clipps'),date)

            try:
              os.makedirs(path, exist_ok = True)
            except:
              pass
            #
            """
            dd=base_name.split("_")[0]
            im = '{}/{}/{}_{}_{}_{}_{}.jpg'.format(clipps,dd,base_name,x,y,w,h)

            cv2.imwrite(im, ROIx)
            hashx = imagehash.average_hash(Image.open(im))
            hashstr = str(hashx)
            file_size_clipp = os.path.getsize(im)
            file_size_clipp = int(file_size_clipp / 1000)
            os.remove(im)





            if ROIx is not None:

                try:
                    ROI = cv2.resize(ROIx, (540,520))
                    ROI  = cv2.rotate(ROI, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    #print(n)
                except:
                    pass




           # ROI = maintain_aspect_ratio_resize(ROIx,390,320)
            try:
                ROI = cv2.resize(ROIx, (550,440))
            except:
                ROI = cv2.resize(ROI, (550,440))

            #ROI= rescale_by_width(ROIx,480)
    #        bg = image_info(i,hist, bg,image.shape[0]+60,25)


            datey = frame[frame.shape[1]-40:frame.shape[1]-40,frame.shape[0]-40:frame.shape[0]-40]


                    #datesat = org_image[int(org_image.shape[0]-40):int(org_image.shape[0]-40)+20, int(org_image.shape[1]-40):int(org_image.shape[0]-40)]



            unique, counts = np.unique(ROIx, return_counts=True)
            mapColorCounts = len(dict(zip(unique, counts)))

            nn=0

            if mapColorCounts >=0:


                inp=None
                try:

                  pt = [x,y]
                  
                  inp = solve(slotmap, pt , hashx)
                except:
                  pass

                slotmap["slot-{}".format(n)] = {"point":[x,y],"hash":str(hashx)}
                #pprint.pprint(slotmap)
                if file_size_clipp > 1000:
                    print("to-large")
                    
                elif file_size_clipp < 6:

                    ROI  = cv2.rotate(ROI, cv2.ROTATE_90_CLOCKWISE)
                    ROI = cv2.resize(ROIx, (750,350))
                    cv2.putText(ROI, "{}".format(" ".join([gdate[2],gdate[3]])), (6,25),1, 1.5, ( 255,  255, 255), 2)
                    im2 = '{}/{}/{}_{}_{}_{}_{}_{}_{}.jpg'.format(clipps,dd,"_".join([gdate[2],gdate[3],gdate[1]]),time,hashstr,x,y,w,h)

                    #cv2.putText(ROI, "{}".format(" ".join([gdate[2],gdate[3]])), (6,25),1, 1.5, ( 255,  255, 255), 2)
                    cv2.imwrite(im2,ROI)
                  

                    
                    if int(n) > 10:
                      nxa = 1
                      n=0
                      

                      bob = (image.shape[0]+1420)+(1*150)
                      bg = image_info(n,ROI,bg,2960,-765+((27*nxa)*53+25))
                    else:
                      bob = 1590
                      bg = image_info(n,ROI,bg,2640,200+((19*n)*20+25))

                    
                else:
                    im2 = '{}/{}/{}_{}_{}_{}_{}_{}_{}.jpg'.format(clipps,dd,"_".join([gdate[2],gdate[3],gdate[1]]),time,hashstr,x,y,w,h)
                    #cv2.putText(ROIx, "{}".format(" ".join([gdate[2],gdate[3]])), (6,25),1, 1.5, ( 255,  255, 255), 2)
                    
                    cv2.rectangle(frame, (x, y),(x + w, y + h), (0, 255, 0), 1)
                    #cv2.putText(ROI, "{}".format(" ".join([gdate[2],gdate[3]])), (6,25),1, 1.5, ( 255,  255, 255), 2)
                    ROI_number=ROI_number+1
                    hist=drawHistogram(ROI)
                    hist = cv2.resize(hist, (750,180))
                    #cv2.putText(hist, "f:{} {}".format(i," ".join([gdate[2],gdate[3]])), (30,20),1, 1.5, ( 255,  255, 255), 2)
                    bg = image_info(n,hist,bg,(image.shape[0]+1560),25)

                
                    if inp == "slot-0":
                      nx=0
                    elif inp == "slot-1":
                      nx=1
                    elif inp == "slot-2":
                      nx=2
                    elif inp == "slot-3":
                      nx=3
                    elif inp == "slot-4":
                      nx=4
                    elif inp == "slot-5":
                      nx=5
                    else:
                      nx=n
                      #print(n)


                    ROI = cv2.resize(ROIx, (405,880))
                    ROI  = cv2.rotate(ROI, cv2.ROTATE_90_CLOCKWISE)
                    cv2.putText(ROIx, "{}".format(" ".join([gdate[2],gdate[3]])), (6,25),1, 1.5, ( 255,  255, 255), 2)
                    
                    cv2.putText(ROI, "{}".format(" ".join([gdate[2],gdate[3]])), (6,25),1, 1.5, ( 255,  255, 255), 2)
                    cv2.imwrite(im2,ROIx)
                    bg = image_info(n,ROI,bg,image.shape[0]+660+(0*370),((16*nx)*27+25))
                    cv2.rectangle(frame, (x, y),(x + w, y + h), (0, 255, 0), 1)

                    if int(n) > 4:
                      n=0
                        
                    if nx >4:
                      nx=0

                    messure=go
        #                    slot[n]=0
        #                    slot[n+1]=1
        #                    h=0


                itr=itr+1
                n=n+1


            #  ROI = rescale_by_width(ROI,480)
            ##ROI = rescale_by_width( ROI,200)



    #
                #cv2.rectangle(frame, (image_width+130,90),(image_width+470,390), (255, 255, 255), 0,1)


    return frame,bg,slot,n,cx,ROI_number,slotmap

def between(n,fr ,to):
    if n > fr and n < to:
        return [[0,255,0],100]
    else:
        return  [[0,240,0],100]

def gradient_ascentx(image, file_name,ROI_number,bg,slot,hcontainer,org_image,n,cx,i ,slotmap,gdate):


#        n = 0
#        imagse = maintain_aspect_ratio_resize(image,1050,1050)
        #image = rescale_by_width(image,1340)
        frame = image
        base_dir,base_name = os.path.split(file_name)#.replace(".jpg","")
        sat=None
        try:
            if len(base_name) == 3:
                date = base_name.split("_")[0]
                time = base_name.split("_")[1]
                sat  = base_name.split("_")[2].replace('.jpg','')
            else:
                date = base_name.split("_")[0]
                time = base_name.split("_")[1]
                res  = base_name.split("_")[2]
                sat  = base_name.split("_")[3].replace('.jpg','')
        except:
            pass
        #sat  = args.get('sat')

        #res  = base_name.split("_")[2]
        #sat  = base_name.split("_")[3].replace('.jpg','')

        if sat is not None:
#            cnts=
            path = os.path.join(args.get('clipps'),date)
            #print(sat)
            try:

                col = get_category_numeric_id(sat)


                #imutils.resize(image, width=1050, height=1050)
                imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                #ret, thresh = cv2.threshold(imgray, 125, 255, 0)
                ret, thresh = cv2.threshold(imgray,col[0][0],col[0][1],col[0][2])
                tersehold = col[1]


                # dilate the thresholded image to fill in holes, then find contours
                # on thresholded image
                thresh = cv2.dilate(thresh, None, iterations=1)
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                os.makedirs(path, exist_ok = True)


                o = 0
                #print(tersehold)
                for c in sort_by_area(cnts):
                    epsilon = 0.01*cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, epsilon, True)
                    # Position for writing text
                    (x, y, w, h) = cv2.boundingRect(c)

                    go=w*h


                    if type(frame) == 'int' or int(go) < tersehold and 0:
                            continue
                    else:
                        o = o + 1
                        #if o < 100:
                        frame,bg,slot,n,cx,ROI_number,slotmap = cSat(c, frame,file_name,ROI_number,messure,bg,slot,n,hcontainer,org_image,cx,path,i,slotmap,gdate)
                        cv2.putText(frame, "main feed: {} / f={}".format(sat,i), (6,30),1, 1.5, ( 255,  255, 255), 2)







                            #n=n+1


            except:
                pass




        return frame,ROI_number,bg,slot,n,cx,slotmap
                 #   cv2.putText(bg, " {}".format(n), (int(frame.shape[0]/4)-100,frame.shape[1]+60),1, 1, (0, 0, 255), 2)






def gradient_ascentxy(image, file_name,ROI_number,bg,slot,hcontainer,org_image,n,cx,i,o, gdate):


#        n = 0
#        imagse = maintain_aspect_ratio_resize(image,1050,1050)
        #image = rescale_by_width(image,1340)
        frame = image
        base_dir,base_name = os.path.split(file_name)#.replace(".jpg","")
        sat=None
        try:
            if len(base_name) == 3:
                date = base_name.split("_")[0]
                time = base_name.split("_")[1]
                sat  = base_name.split("_")[2].replace('.jpg','')
            else:
                date = base_name.split("_")[0]
                time = base_name.split("_")[1]
                res  = base_name.split("_")[2]
                sat  = base_name.split("_")[3].replace('.jpg','')
        except:
            pass
        sat  = "c3"
        #res  = base_name.split("_")[2]
        #sat  = base_name.split("_")[3].replace('.jpg','')

        if sat is not None:
#            cnts=

            #root = os.path.dirname(os.path.realpath("."))
            path = "clipps"
            #os.path.join(root,args.get('out_filename'),args.get('sat'),date)
            #print(path)

            #print(sat)


            col = get_category_numeric_id(sat)


            #imutils.resize(image, width=1050, height=1050)
            imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #ret, thresh = cv2.threshold(imgray, 125, 255, 0)
            ret, thresh = cv2.threshold(imgray,col[0][0],col[0][1],col[0][2])
            tersehold = col[0][1]


            # dilate the thresholded image to fill in holes, then find contours
            # on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            os.makedirs(path, exist_ok = True)
            clipps = args.get('clipps')

            avg = []
            for on, c in enumerate(sort_by_area(cnts)[1:25]):
                #epsilon = 0.01*cv2.arcLength(c, True)
                #approx = cv2.approxPolyDP(c, epsilon, True)
                # Position for writing text
                (x, y, w, h) = cv2.boundingRect(c)
                go=int(w) * int(h)
                avg.append(go)


            avg.sort(reverse=True)

            #print(avg)
            n=0
            for on, c in enumerate(sort_by_area(cnts)[1:25]):
                #epsilon = 0.01*cv2.arcLength(c, True)
                #approx = cv2.approxPolyDP(c, epsilon, True)
                # Position for writing text
                (x, y, w, h) = cv2.boundingRect(c)
                go=w*h
                rawy=frame.shape[1]
                maxy=frame.shape[1] * 0.9
                ROI = org_image[y:y+h, x:x+w]
                ROIx=ROI



                if 1 and ((int(w / 1.3)> h) or (int(h / 1.3)  > w) and (x>0 and y>0) and go > col[1]):
                  print("ok")
                else:
                  continue

                if 0 and (y<=5 or x <=5 or x >=1000 or y > 1000 or y < 20 or go < col[1]  or between(y,50,50) or between(x,50,50)):
                  continue






                if w>h:
                    pc = int(w/20)
                else:
                    pc = int(h/20)

                xorg=x
                yorg=y
                x=x-(6*pc)
                y=y-(6*pc)
                w=w+(12*pc)
                h=h+(12*pc)


                if sat=="c3" or sat == "c2":
                    print()
                    #ROIx = org_image[(y*2):(y*2)+(h*2), (x*2):(x*2)+(w*2)]
                elif sat == "0131":
                    ROIx = org_image[(y*2):(y*2)+(h*2), (x*2):(x*2)+(w*2)]
                else:
                    ROIx = org_image[(y*4):(y*4)+(h*4), (x*4):(x*4)+(w*4)]



                hashid=storeClipp(org_image,path,base_name, c,date)

                try:

                  """
                  hist=drawHistogram(ROI)
                  hist = cv2.resize(hist, (int(300),int(100)+1750))


                  bg  = image_info(bg,hist,4440,40)
                  """


                  n=1

                  #print([base_name,go,w,h,hashid,y,x])

                  if hashid in count and "count" in count[hashid]:
                    count[hashid]['count'] = count[hashid]['count']+1
                    count[hashid]['xy'] = {'x':x,'y':y}
                  else:
                    count[hashid] = {}
                    count[hashid]['count'] = 1
                    count[hashid]['xy'] = {'x':x,'y':y}


                  #print([base_name,go,w,h,hashid,y,x,count])
                  #inverse = [(value, key) for key, value in count]
                  #print(max(inverse)[1])

                  xcount[hashid]=count[hashid]['count']

                  if n>2:
                    n=0


                  if xcount[hashid]==1 and go > 2*col[1]:
                    ROIx = cv2.resize(ROI, (400,390))
                    bg  = image_info(bg,ROIx,100+int(bg.shape[1]/2)+int(400 * o),int(50+n*430))


                  cv2.rectangle(frame, (x, y),(x + w, y + h), (0, 255, 0), 4)
                  o = 1 + o



                  if o % 4:
                    n=n+1
                    o=0

                  if o >= 20:
                    o=0
                    n=0



                  if n <= 1:
                    ROIx = cv2.resize(ROIx, (1550,950))
                    bg  = image_info(bg,ROIx,550+int(bg.shape[1]/2),50)
                    cv2.rectangle(frame, (x, y),(x + w, y + h), (0, 255, 0), 1)

                  xmax.append(go)

                  if go == max(xmax):
                    ROIx = cv2.resize(ROIx, (1550,950))
                    bg  = image_info(bg,ROIx,550+int(bg.shape[1]/2),int(bg.shape[0]/2)+240)
                    cv2.rectangle(frame, (x, y),(x + w, y + h), (0, 255, 0), 1)

                except:
                  pass

        return frame,ROI_number,bg,slot,n,cx,o


def find(path, expr):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.jpg' in file and fnmatch.fnmatch(file,expr):
                files.append(os.path.join(r, file))
    for f in files:
        print(f)
    return np.sort(files)

def process(files):
    for i,file_name in enumerate(files):
        image=cv2.imread(file_name)
        image = gradient_ascent(image, file_name)
        #image = add_corners(image)
    #    process.stdin.write(cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.uint8).tobytes())

        #time.sleep(0.1)


        cv2.namedWindow(sat)
        cv2.resizeWindow(sat, 1600, 1600)
        cv2.imshow(sat,image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break



def gradient_ascent(image, file_name,ROI_number,bg,slot,hcontainer,org_image,gdate):
    frame = image
    base_dir,base_name = os.path.split(file_name)#.replace(".jpg","")
    
    
    if len(base_name) == 3:
        date = base_name.split("_")[0]
        time = base_name.split("_")[1]
        sat  = base_name.split("_")[2].replace('.jpg','')
    else:#if len(base_name) == 4:        
        date = base_name.split("_")[0]
        time = base_name.split("_")[1]
        res  = base_name.split("_")[2]
        sat  = base_name.split("_")[3].replace('.jpg','')

    sat  = args.get('sat')
    sat  = args.get('sat')
    col = get_category_numeric_id(sat)
    #print(sat)
    #print(col)
    #res  = base_name.split("_")[2]
    #sat  = base_name.split("_")[3].replace('.jpg','')
    
    if sat is not None:
        
        path = os.path.join(args.get('clipps'),sat,date) 
        
        col = get_category_numeric_id(sat)
        #print(sat)
        
        
        #imutils.resize(image, width=1050, height=1050)
        imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #ret, thresh = cv2.threshold(imgray, 125, 255, 0)
     
        
        ret, thresh = cv2.threshold(imgray,col[0][0],col[0][1],col[0][2])       
        tersehold = col[0][1]

            
        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        
        
        clipps = args.get('clipps')
# loop over the frames of the video
        # loop over the contours
        #n=0
#           bg = cv2.imread("/media/santex/3e8c7b9b-21f9-4a4a-b235-5eb558dcc67a/Ship-Net/static/bg.jpg")
#           bg = cv2.resize(bg, (2160,1080)) 
        n=0
        for c in sort_by_area(cnts):            
            epsilon = 0.001*cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, epsilon, True)
            # Position for writing text
            (x, y, w, h) = cv2.boundingRect(c)  

            go = int((image.shape[0]/1024))*w*h
            pct = image.shape[1]*image.shape[0] / 100
            found = go / pct
            #
            #print(go) 
            if type(frame) == 'int':
                 continue
                
                
            if go < tersehold:
                continue
            else:
                #cv2.putText(frame, "Sat: {}".format(sat), (6,30),0, 1, ( 255,  255, 255), 2)
                ROI = frame[y:y+h, x:x+w]
                go = h * w
                check = y+h        
                check2 = x
                n_red_pix = np.sum(ROI == 180)
                n_white_pix = np.sum(ROI == 255)
                
                wp = go / 100
                wp = n_white_pix / wp
                #print("white_pixel:{}".format(wp))
    
                (x, y, w, h) = cv2.boundingRect(c)
                image_width = image.shape[0]
                image_height = image.shape[1]
                
                ROI = frame[y:y+h, x:x+w]
                go = h * w
                check = y+h        
                check2 = x
                n_red_pix = np.sum(ROI == 180)
                n_white_pix = np.sum(ROI == 255)
                
                wp = go / 100
                wp = n_white_pix / wp
                if (y < 940):
                    ROIgray = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
                    
                    
                    
                    #ret, thresh = cv2.threshold(imgray, 125, 255, 0)
                    clipps = args.get('clipps')
                    base_dir,base_name = os.path.split(file_name)#.replace(".jpg","")
                    date = base_name.split("_")[0]
                    time = base_name.split("_")[1]
                    sat  = base_name.split("_")[2]
                    sat  = base_name.split("_")[3].replace('.jpg','')
                    #print(base_name.split("_"))
                    #RO = maintain_aspect_ratio_resize(ROI,440)
                    
                    hist=drawHistogram(ROI,True)
                    
                    
                    path = os.path.join(args.get('clipps'),sat,date) 
                    
                    
                    try: 
                        os.makedirs(path, exist_ok = True) 
                        print("Directory '%s' created successfully" %path)         
                    except:
                        print("Directory '%s' exists") 
             
             
             
                    im = '{}/{}_{}_{}_{}_{}_{}.jpg'.format(clipps,base_name,ROI_number,x,y,w,h)
                    cv2.imwrite(im, ROI)
                    hash = imagehash.average_hash(Image.open(im))
                    hashstr = str(hash)
                    os.remove(im)
                    im2 = '{}/{}_{}_{}_{}_{}_{}_{}.jpg'.format(path,hash,base_name,ROI_number,x,y,w,h)
                    cv2.imwrite(im2,maintain_aspect_ratio_resize(ROI,460,300))
                    nn=0
                    #ROI = sharpen(ROI)   
                    

                    pc = int(w/4)


                    x=x-(3*pc)
                    y=y-(3*pc)
                    w=w+(6*pc)
                    h=h+(6*pc)
                    ROIz=0
                    
                    if sat=="c3":
                        print(sat)
                        ROIx = org_image[(y*1):(y*1)+(h*1), (x*1):(x*1)+(w*1)]
                    elif sat=="c2":
                        print(sat)
                        ROIx = org_image[(y*1):(y*1)+(h*1), (x*1):(x*1)+(w*1)]
                    else:
                        ROIx = org_image[(y*4):(y*4)+(h*4), (x*4):(x*4)+(w*4)]

                    
                    try:
                        if ROIx is not None:
                            #ROIx=maintain_aspect_ratio_resize(ROIx,660,700)
                            ROIz=ROIx
                            ROIx= cv2.resize(ROIx, (790,600)) 
                            
                            
                    except:
                        pass
                            
                  #  ROI = rescale_by_width(ROI,480)
                    
            ##ROI = rescale_by_width( ROI,200)
                    
                    if (w / 1.151> h) or (h / 1.151> w):
                     
                        #hist=ROI   
                        if ROI is not None:
                                    
                #                n = count_colours(ROI)
                #                if n > 0:
                            #cv2.namedWindow(sat)

                            if 0:
                                if searchSub(hcontainer,hashstr[:2]) is not None:
                                    nn1 = searchSub(hcontainer,hashstr[:2])
                                
                                
                                if searchSub(hcontainer,hashstr[:-2]) is not None:
                                    nn2 = searchSub(hcontainer,hashstr[:-2])
                        
                            
                            #print("nn:{}".format(nn1))
                            #if nn1 == nn2 and nn1 is not None and nn2 is not None:
                            #    n = nn
                        
                        #ROI = ROIx


                        #print(n)


                        #hist = (hist,300)
                        ROI = cv2.resize(ROI, (970,790))
                        hist= cv2.resize(hist, (50,bg.shape[0]-100))
            
                        hcontainer[n]="{}".format(hash)
                        if n >= 0:    
                            bg = image_info(i,ROI, bg,bg.shape[0],25)
                        
                        
                        #slots += 1
                        bg = image_info(i,hist,bg,bg.shape[0]-80,20)
                        cv2.rectangle(frame, (x, y),(x + w, y + h), (0, 255, 0), 1)
                        messure=go
                        slot[0]=0   
                        slot[1]=1
                        h=0
                
    #            bg = image_info(i,ROI, bg,image.shape[0]+60,25)
                
        return frame,ROI_number,bg,slot


        
def drawHistogram(img,color=True,windowName='drawHistogram'):
    h = np.zeros((300,256,3))

    bins = np.arange(256).reshape(256,1)

    if color:
            channels =[ (255,0,0),(0,255,0),(0,0,255) ];
    else:
            channels = [(255,255,255)];

    for ch, col in enumerate(channels):
            hist_item = cv2.calcHist([img],[ch],None,[256],[0,255])
            #cv2.normalize(hist_item,hist_item,0,255,cv2.NORM_MINMAX)
            hist=np.int32(np.around(hist_item))
            pts = np.column_stack((bins,hist))
            #if ch is 0:
            cv2.polylines(h,[pts],False,col)

    cv2.normalize(hist,hist,0,255,cv2.NORM_MINMAX)

    h=np.flipud(h)

    return h
def logoOverlay(image,logo,alpha=1.0,x=0, y=0, scale=1.0):
    (h, w) = image.shape[:2]
    image = np.dstack([image, np.ones((h, w), dtype="uint8") * 255])
    #verlay = cv2.resize(logo, None,fx=scale,fy=scale)
    return image

def put4ChannelImageOn4ChannelImage(back, fore, x, y):
    rows, cols, channels = fore.shape
    trans_indices = fore[...,3] != 0 # Where not transparent
    overlay_copy = back[y:y+rows, x:x+cols]
    overlay_copy[trans_indices] = fore[trans_indices]
    back[y:y+rows, x:x+cols] = overlay_copy
def image_info(post_id,hist, image,x,y):
    try:
        x_offset=x
        y_offset=y
        image[y_offset:y_offset+hist.shape[0], x_offset:x_offset+hist.shape[1]] = hist
    except:
        pass

    return image
def image_add(post_id,hist , image,x,y):

    x_offset=x
    y_offset=y
    image[y_offset:y_offset, x_offset:x_offset] = hist

    return image

def solve(pts, pt, hash):
   x, y = pt
   idx = -1
   smallest = float("inf")
   out = {}
   for p in pts:
      key = p
      p = pts[p]['point']
      dist =  abs(y - p[1])
      out[key]=dist
      if dist < smallest:
        idx = key
        smallest = dist


   #pprint.pprint([pt,out,smallest,idx])
   return idx
"""
def get_category_numeric_id(category):
    if (category.startswith('c2')): #black red
        return [[220,250,0],50]
    elif (category.startswith('c3')): #black blue
        return  [[227,250,250],50]
    elif (category.startswith('0131')): # black blue
        return [[240,255,0],300]
    elif (category.startswith('1600')): #black yellow
         return [[0,250,0],50]
    elif (category.startswith('0304')): #black red
        return [[127,255,0],300]
    elif (category.startswith('0211')): #black lila
        return [[127,255,0],2000]
    elif (category.startswith('0335')):#black blue
        return [[127,255,0],300]
    elif (category.startswith('1700')): # black reddisch
        return [[0,190,0],1000]
    elif (category.startswith('0094')): #black green
        return [[127,240,0],1000]
    elif (category.startswith('0171')): #black yellow
        return [[127,255,0],300]
    elif (category.startswith('0193')): #black orange
        return [[127,255,0],300]
    elif (category.startswith('4500')): #black yellow
        return [[0,255,0],100]
    else:
        return -1
"""
def get_category_numeric_id(category):
    if (category.startswith('c2')): #black red
        return [[190,180,0], 1000]
    elif (category.startswith('c3')): #black blue
        return  [[180,180,0],1000]

    elif (category.startswith('0131')): # black blue
        return [[0,240,0],50]
    elif (category.startswith('1600')): #black yellow
         return [[0,240,0],50]
    elif (category.startswith('0304')): #black red
        return [[0,240,0],50]
    elif (category.startswith('0211')): #black lila
        return [[0,240,0],50]
    elif (category.startswith('0335')):#black blue
        return [[0,240,0],50]
    elif (category.startswith('1700')): # black reddisch
        return [[0,210,0],50]
    elif (category.startswith('0094')): #black green
        return [[0,240,0],50]
    elif (category.startswith('0171')): #black yellow
        return [[0,240,0],50]
    elif (category.startswith('0193')): #black orange
        return [[0,240,0],50]
    elif (category.startswith('4500')): #black yellow
        return [[0,240,0],50]
    else:
        return [[0,240,0],50]

def read_frame_as_jpeg(in_filename, frame_num):
    out, err = (
        ffmpeg
        .input(in_filename)
    #    .filter('select', 'gte(n,{})'.format(frame_num))
        .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
        .run(capture_stdout=True)
    )
    return out



def start_ffmpeg_process1(in_filename):
    logger.info('Starting ffmpeg process1')
    args = (
        ffmpeg
        .input(in_filename)
        .output('pipe:', format='rawvideo', pix_fmt='rgb24')
        .compile()
    )
    return subprocess.Popen(args, stdout=subprocess.PIPE)


def start_ffmpeg_process2(out_filename, width, height):
    args = (
        ffmpeg
        .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(width, height))
        .output(out_filename, pix_fmt='yuv420p')
        .overwrite_output()
        .compile()
    )
    return subprocess.Popen(args, stdin=subprocess.PIPE)


def run(in_filename, out_filename, process_frame):
    width, height = get_video_size(in_filename)
    process1 = start_ffmpeg_process1(in_filename)
    process2 = start_ffmpeg_process2(out_filename, width, height)
    while True:
        in_frame = read_frame(process1, width, height)
        if in_frame is None:
            break

        out_frame = process_frame(in_frame)
        write_frame(process2, out_frame)

    process1.wait()

    process2.stdin.close()
    process2.wait()

    logger.info('Done')



# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--source", help="path to the image file's")
ap.add_argument("-s", "--sat", default="c2", help="c3 c2 0171 ....")
ap.add_argument("-m", "--max-area", type=int, default=1050, help="maximum area size")
ap.add_argument("-c", "--clipps", default="/tmp/clipps", help="clipp's out dir")
ap.add_argument("-e", "--expr", default="2022", help="match")
args = vars(ap.parse_args())
pathIn = args.get('source')

fps = 1
frame_array = []
class_name = []
labelList = re.split(os.sep+os.sep,args.get('source'))
#print(labelList)
sat=labelList[len(labelList)-1]
#print(labelList[len(labelList)-1])
pathOut = os.path.join(os.getcwd())
#args.{"sat":sat}
saved_video_file_name = os.path.join(args.get('clipps'),"{}_{}.mp4".format(args.get('sat'),args.get('expr')))

expr = args.get('expr')
dirs = find(pathIn,'*'+expr+'*')

ROI_number = 0
messure=0
cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
cap.set(3,1050)
cap.set(4,1050)
process2 = start_ffmpeg_process2(saved_video_file_name,3400,1800)
path=""
process = None
#dirs.sort(key = lambda x: x[5:-4])
#bg = cv2.imread("static/bg.png")
#ret, thresh = cv2.threshold(imgray, 127, 255, 0)
#bg = cv2.resize(bg, (2280,1160))
bg = cv2.imread(os.path.join(os.getcwd(),"static"+os.sep+os.sep+"bg.png"));

bg = cv2.resize(bg, (3400,1800))
#bg = cv2.resize(bg, (3290,1780))
k=0
cx=0
slots=0
slot =[ 1,0,0,0,1,1,1,1 ]
hcontainer={}
n=0
slotmap = {}
c=0
xname=[]
sat = args.get('sat')
for i,file_name in enumerate(dirs):
    image = cv2.imread(file_name)


    if image is None:
        continue


    #image = supperEnhance(image)

    org_image = image

    
    #date = image[300:600, 400,800].copy()
    fname=file_name.split("/")
    print(fname)


    #xname=[fname[3][0:8],fname[3][9:13]]
    if sat.startswith("c"):
      
      image = cv2.resize(image, (1080,1080))
      date = image[1035:1075 ,0:560].copy()
    else:
      date = image[3920:4050 ,0:1850].copy()


    extracted_text_rgb = date
    extracted_text = pytesseract.image_to_string(extracted_text_rgb)
    print(" Extracted Text:\n")
    date = extracted_text.replace("\n","").replace("'","").split(" ")

    if len(date)< 4:       
        
        date=[]
        date.append("shipnet")
        date.append(sat)
        #date.append(xname[0])

        if len(xname) == 1:
          date.append(xname[0])
        elif len(xname) > 0:
          date.append(xname[1])
        else:
          date.append("hi")

        #pprint.pprint([date, "~".join(date)])
    
        
    count={}
        
    n=0
    o=0
    
    #org_image = cv2.resize(org_image, (2000,2000))
    if sat.startswith("c"):

      print(f"csat: {sat}")
      #org_image = cv2.resize(org_image, (2056,2056))
      
      image,ROI_number,bg,slot = gradient_ascent(image, file_name, ROI_number,bg,slot,hcontainer,org_image, date)

      #image,ROI_number,bg,slot,n,c,o = gradient_ascentxy(org_image, file_name, ROI_number,bg,slot,hcontainer,org_image,n,cx,i,o)
    else:
      image = cv2.resize(image, (1080,1080))
      image,ROI_number,bg,slot,n,c,slotmap = gradient_ascentx(image, file_name, ROI_number,bg,slot,hcontainer,org_image,n,cx,i,slotmap , date)
      

      
        

    #image  = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    image = cv2.resize(image, (1700,1700))
    bg  = image_info(i,image,bg,0,23)

    #, pix_fmt='yuv420p').overwrite_output().run_async(pipe_stdin=Trure)

    try:
      write_frame(process2, bg)
    except:
      pass
    """
    process2.stdin.write(
        out_frame
        .astype(np.uint8)
        .tobytes()
    )
    """

    
#except:
    #gradient_ascent(bg, file_name, ROI_number)
    #hist=drawHistogram(image)
    #
    if n >3:
        n = 0
        cx=cx+1

    #    time.sleep(0.3)
    #cv2.putText(bg, "[  {}  ]".format(slots), (int(image.shape[0]*1.15),image.shape[1]+50),4, 1, (0, 0, 255), 1)

    # hist = cv2.resize(hist, (int(bg.shape[0]/4),int(hist.shape[1]/2)+150))


    #bg  = image_info(i,hist,bg,int(bg.shape[0]*1),int(bg.shape[0]/2-200))
    #if bg is None:
     #   continue
    if cx * n >3:
        cx=0


    #print(saved_video_file_name)#
    #cv2.namedWindow(sat)
    #cv2.resizeWindow(sat, 1700, 1200)
    """
    xbg=bg      
    
    xbg = cv2.resize(xbg, (int(xbg.shape[1]/1.9),int(xbg.shape[0]/1.9)))
    
    cv2.imshow(sat,xbg)
    #cv2.imshow(sat,date)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
      break

    """
