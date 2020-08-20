#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 16:58:06 2020

@author: emmastanley
"""

import MMCorePy 
import time 
import serial
import cv2
import matplotlib.pyplot as plt
import csv
import numpy as np
from skimage import color, measure

'''
Image acquisition and image analysis functions for a rectangular array of inkjet-printed
droplets are contained below. 

NOTE: This version of DropletCellCount does not include Empty Droplet Exclusion as discussed in my thesis. 
- Emma 
'''

#%%
########################

mmc = MMCorePy.CMMCore()
print(mmc.getVersionInfo())
print(mmc.getAPIVersionInfo())

########################

#ENSURE ShutterControlv2_lab.ino IS UPLOADED TO BOARD BEFORE RUNNING THIS SCRIPT!!!

#establish port and baud rate for serial connection
port = 'COM20' #THIS PORT MAY CHANGE DEPENDING ON WHAT THE ARDUINO IS PLUGGED INTO.
               #FIND OUT THE NAME OF THE PORT FROM ARDUINO > TOOLS > PORT.
baud = 9600

#open the serial connection to arduino
arduino = serial.Serial(port, baud)
time.sleep(2) #There must be a 2 second delay after estabslishing serial port, reason below
#https://arduino.stackexchange.com/questions/58061/problem-sending-string-with-python-to-arduino-through-serial-port

#print port connected to arduino 
print(arduino.name)

########################

#load and initialize devices
mmc.loadSystemConfiguration('C:\Program Files\Micro-Manager-2.0gamma\ES_WorkingConfig_Colour.cfg') #imports configuration file from micromanager
mmc.initializeAllDevices() 


#%%
def arrayAcquisition_ShutterControl(ncols,nrows,dx,dy,expBF,expFL,array_label,directory):

    '''
    
    arrayAcquisition: a function that acquires images with the currently initialized micromanager camera and stage
    in an XY array of a specified length and width, and displays the images in the spyder console/plot viewer. 
    Images are saved to a specified directory with array and image labels (labelled sequentially in order of capture).
    
    the images are acquired from left to right on odd number rows, and right to left on even number rows, 
    and from top to bottom of array (starting in top left corner)
    for example, the sequence to acquire images from an array of ncols=4 and nrows=3,
    
     . . . .
     . . . .
     . . . .
     
     would be 
    
    -> -> -> ->
    <- <- <- <-
    -> -> -> ->
    
    and the printed XY position labels correspond to 
    
    (0,0)   (10,0)   (20,0)   (30,0)
    (0,-10) (10,-10) (20,-10) (30,-10)
    (0,-20) (10,-20) (20,-20) (30,-20)
    
    
    ShutterControl: opens and closes the shutter for the fluorescent laser via stepper motor. 
    sends a command to the arduino via serial connection and waits for the arduino to send a command
    corresponding to open or closed position. enables the capture of both brightfield and fluorescent
    images from the same position on the array.
     
    inputs: 
        ncols: number of columns in the array 
        nrows: number of rows in the array 
        dx: horizontal (x) distance between objects in the array, in microns
        dy: vertical distance (y) between objects in the array, in microns
        expBF: exposure of camera for bright field images, in ms
        expFL: exposure of camera for fluorescent images, in ms
        array_label: label of the array to append to saved files, character string or number
        directory: full file path of folder to save images to, character string 
        
    requirements:
        XY stage and camera must be loaded and initialized 
        arduino code must be uploaded to uno and correct port must be opened
        
    libraries required:
        MMCorePy
        matplotlib
        time
        serial
        
    Note: There are some redunancies in the code that can be re-written to create a more concise function. 
    I did not attempt to re-work it since I was not able to validate that it would still work effectively due to lab shutdowns.
    -Emma

    '''    
    
    ###set relative position of stage to 0,0
    mmc.setOriginXY() 
    print(mmc.getXYPosition('XYStage'))  
 
   
    colcount=1 #a variable to index the current column
    rowcount=1 # a variable to index the current row 
    
    nobjects=nrows*ncols #determine how many objects are in the array
    nimgs_bf=0 #a variable to keep track of the number of brightfield images captured
    nimgs_fl=0 #a variable to keep track of the number of fluorescent images captured



    while rowcount<=nrows: #while current row index is within the specified array size
        
        if colcount<=ncols and (rowcount%2)!=0: #if there are more columns in the array and row number is odd
            
            ###ensure shutter is open for brightfield image to be acquired
            
            arduino.write('a') #send command for opening shutter
            data = arduino.readline() #read data from serial port
            while data != 'o\r\n': #wait for shutter to finish opening. \r\n are characters that get appended to data sent from Arduino
                pass
            if data == 'o\r\n':
                print ('Shutter is open')
                
            ###acquire brightfield image from camera
            
            mmc.setExposure(expBF)
            mmc.snapImage() 
            img = mmc.getImage()
            nimgs_bf=nimgs_bf+1 
            
            plt.imshow(img, cmap='gray') #show image in spyder viewer
            plt.show()
            
            label='{}/array{}_BFimage{}.png'.format(directory,array_label,str(nimgs_bf).zfill(4))
            img=img.astype('uint8') #convert image to a format that imwrite can use
            cv2.imwrite(label,img) #save image
            
            print('Brightfield image {} captured.'.format(nimgs_bf))
            
            ###close shutter to acquire fluroescent image
            
            arduino.write('z') #send command for closing shutter
            data = arduino.readline()
            while data != 'c\r\n': #wait for shutter to finish closing. \r\n are characters that get appended to data sent from Arduino
                pass
            if data == 'c\r\n':
                print ('Shutter is closed')
    
            
            ###acquire fluorescent image from camera
            
            mmc.setExposure(expFL)
            mmc.snapImage() 
            img = mmc.getImage()
            nimgs_fl=nimgs_fl+1 
            
            plt.imshow(img, cmap='gray') #show image in spyder viewer 
            plt.show()
            
            label='{}/array{}_FLimage{}.png'.format(directory,array_label,str(nimgs_fl).zfill(4))
            img=img.astype('uint8') #convert image to a format that imwrite can use
            cv2.imwrite(label,img) #save image
            
            print('Fluorescent image {} captured.'.format(nimgs_fl))
            
            
            ###move position of the stage to the next droplet
            if colcount<ncols: #as long as the column is not the last column in the array
                mmc.setRelativeXYPosition('XYStage',-dx,0) #move dx units left (camera centers on droplet to the right)
                print(mmc.getXYPosition('XYStage')) #print position of stage after horizontal movement
        
            colcount=colcount+1 #increase column index
            
            time.sleep(0.5) #brief delay after moving stage to allow the camera to focus
            
            
        if colcount<=ncols and (rowcount%2)==0: #if there are more columns in the array and the row number is even
           
           ###ensure shutter is openfor brightfield image to be acquired
            
            arduino.write('a') #send command for opening shutter
            data = arduino.readline()
            while data != 'o\r\n': #wait for shutter to finish opening.\r\n are characters that get appended to data sent from Arduino
                pass
            if data == 'o\r\n':
                print ('Shutter is open')
                
            
            ###acquire brightfield image from camera
            
            mmc.setExposure(expBF)
            mmc.snapImage() 
            img = mmc.getImage()
            nimgs_bf=nimgs_bf+1 
            
            plt.imshow(img, cmap='gray') #show image in spyder viewer 
            plt.show()
            
            label='{}/array{}_BFimage{}.png'.format(directory,array_label,str(nimgs_bf).zfill(4))
            img=img.astype('uint8') #convert image to a format that imwrite can use
            cv2.imwrite(label,img) #save image
            
            
            print('Brightfield image {} captured.'.format(nimgs_bf))
            
            
            ###close shutter to acquire fluroescent image
            
            arduino.write('z') #send command for opening shutter
            data = arduino.readline()
            while data != 'c\r\n': #wait for shutter to finish closing. \r\n are characters that get appended to data sent from Arduino
                pass
            if data == 'c\r\n':
                print ('Shutter is closed')
    
            ###acquire fluorescent image from camera
            
            mmc.setExposure(expFL)
            mmc.snapImage() 
            img = mmc.getImage()
            nimgs_fl=nimgs_fl+1 
            
            plt.imshow(img, cmap='gray') #show image in spyder viewer 
            plt.show()
            
            label='{}/array{}_FLimage{}.png'.format(directory,array_label,str(nimgs_fl).zfill(4))
            img=img.astype('uint8') #convert image to a format that imwrite can use
            cv2.imwrite(label,img) #save image
            
            print('Fluorescent image {} captured.'.format(nimgs_fl))
            
            ###move position of the stage
            if colcount<ncols: #as long as the column is not the last column in the array
                mmc.setRelativeXYPosition('XYStage', dx,0) #move dx units right (camera centers on droplet to the left)
                print(mmc.getXYPosition('XYStage')) #print position of stage after horizontal movement
            
            colcount=colcount+1 #increase column index
            
            time.sleep(0.5) #brief delay after moving stage to allow camera to focus
            
            
            
        if colcount>ncols: #if the column index exceeds the number of columns in the array 
            
            mmc.snapImage() #the program needs a placeholder as it doesn't want two stage movement commands back to back (not sure why). snapimage does not actually capture an image unless it is followed by getimage.
            
            mmc.setRelativeXYPosition('XYStage',0,-dy) #move dy units down (to next row)
            print(mmc.getXYPosition('XYStage')) #print position  of stage after horizontal movement 
            
            colcount=1 #reset column index to 1 
            rowcount=rowcount+1 #increase row index 
    
            time.sleep(0.5) #brief delay after moving stage to allow camera to focus
            
            
    arduino.close() #close the serial port connection once while loop is exited 
    
    
    if nimgs_bf!=nimgs_fl:
        print('Error: Different number of brightfield and fluroescent images captured')
        
    if nimgs_bf==nimgs_fl:
        
        if nobjects!=nimgs_bf: 
            print('Error: Not all objects in array were captured.')
        else:
            print('{} bright field and {} fluorescent images were captured.').format(nimgs_bf, nimgs_fl)
    
        
    return 

#%%
def DropletCellCount(directory,array_label,nrows,ncols,mag):
    
    '''
    DropletCellCount_Watershed: a function designed to be used for determining
    the number of beads contained in each image of inkjet-printed droplets 
    captured with arrayAcquisition
    
    Lines of code to display each step of image processing are included but commented out 
    
    inputs:
        directory: full file path of folder that images from arrayAcquisition were
        saved to, character string 
        array_label: label of the array appended to saved files from arrayAcquisition, 
        character string or int
        ncols: number of columns in the array
        nrows: number of rows in the array 
        mag: objective lens used for image capture, either '10x', '20x', or '40x'
        
    returns: 
        count: an array where each space corresponds to the number of objects counted in 
        the series of images
        
    libraries required:
        import matplotlib.pyplot as plt
        import cv2
        import numpy as np
        from skimage import color, measure
    '''

    
    ##############################
   
    ###USER INPUT PRIOR TO RUNNING FUNCTION
    ###Define min and max expected diameter for desired cell type in microns
    diam_min = 8
    diam_max = 18
    
    ##############################
    
    
    nimgs=ncols*nrows #define number of images to pull from file
    count = np.zeros(nimgs) #initialize array for object count data 
    
    
    ###define equivalent area in microns, depending on objective lens used
    ###specific apertures should be added and pixel to um scale confirmed for future use 
    
    if mag=='40x' or mag=='40X':
        pixels_to_um=7.68
    elif mag=='20x' or mag == '20X':
        pixels_to_um=2.2
    elif mag=='10x' or mag == '10X':
        pixels_to_um=1.0568
    else:
        pixels_to_um=1
        print('Magnification incorrectly entered - measurements will be displayed in pixels.')
        pixels_to_um=1
 
    ###labels for image path to match the format it was saved as 
    array= 'array'+str(array_label)
    extension = '.png'
    
    
    ###CSV file initialization
    filename='CellCount_'+array+'.csv' 
    with open(filename,'w') as f: #create a csv file
        headers=['Image','Cell Count', 'Flags', 'Diameters (microns)', 'Areas (microns^2)','File Path', 'File Name'] #column headers
        writer=csv.DictWriter(f, fieldnames=headers) 
        writer.writeheader() #write headers to file
    
    
        for i in range(nimgs): ###for each image that was captured in the given array
            
            ###Read image from file
            index=str(i+1).zfill(4) #number of the image
            imgName=array+'_FLimage'+index+extension #name of the image
            imgPath=directory+'/'+imgName #full path of the image
            img=cv2.imread(imgPath) #read image from file            
            # imgrgb=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # plt.imshow(imgrgb)
            # plt.title('Original Image')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
            
            img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) #convert the image to grayscale 
            # plt.imshow(img_gray,cmap='gray')
            # plt.title('Grayscale Image')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
            
            
            ###Perform Ostu thresholding to create a binary image
            ret2,thresh = cv2.threshold(img_gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            # plt.imshow(thresh,cmap='gray')
            # plt.title('Ostu Thresholding')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
        
            ###Perform morphological opening to remove small objects in the image
            kernel = np.ones((3,3),np.uint8) #define the structuring element
            opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 1) #number of iterations can be modified
            # plt.imshow(opening,cmap='gray')
            # plt.title('Morphological Opening')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
        
        
            ###Determine the sure background region for watershed segmentation using dilation
            sure_bg = cv2.dilate(opening,kernel,iterations=1) #iterations = how many pixels to dilate the objects, can be modified
            # plt.imshow(opening, cmap="gray")
            # plt.title('Sure Background')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
        
        
            ###Determine the sure forground region for watershed segmentation using distance transform
            dist_transform = cv2.distanceTransform(opening,cv2.DIST_L2,5)
            ret, sure_fg = cv2.threshold(dist_transform,0.2*dist_transform.max(),255,0) #threshold distance transform using 20% of max value in distance transform, can be modified
            # plt.imshow(dist_transform, cmap="gray")
            # plt.title('Distance Transform')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
            
            # plt.imshow(sure_fg, cmap="gray")
            # plt.title('Sure Foreground')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
        
        
            ###Determine the unknown region for watershed segmentation by subtracting foreground from background
            sure_fg = np.uint8(sure_fg)
            unknown = cv2.subtract(sure_bg,sure_fg)
            # plt.imshow(unknown, cmap="gray")
            # plt.title('Unknown Region')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
    
        
            ### Marker labelling for watershed segmentation
            ret, markers = cv2.connectedComponents(sure_fg)
            markers = markers+1 # Add one to all labels so that sure background is not 0, but 1
            markers[unknown==255] = 0 # mark the region of unknown with zero
            # plt.imshow(markers, cmap="jet")
            # plt.title('Watershed')
            # plt.xticks([]),plt.yticks([])
            # plt.show()
        
            ###Perform watershed segmenation
            markers = cv2.watershed(img,markers)
            img[markers == -1] = [255,0,0]
        
            ###Generate coloured representation of processed imaged
            img2=color.label2rgb(markers, bg_label=0)
            plt.imshow(img2)
            plt.title('Image'+index)
            plt.xticks([]),plt.yticks([])
            plt.show()
        
            #define list which will contain characteristics for each image
            regions = measure.regionprops(markers,intensity_image=img_gray)
        
            ###define some output variables
            
            cell_count=-1 #a variable to keep track of the objects counted in each image
                          #starts at -1 since regions counts the background as a separate object 
            size_check= 0 #acts as a flag for size
            count_check= 0 #acts as a flag for cell count
            check = '' #initialize check flag 
            diameters=[] #initialize list for diameters
            areas=[] #initialize list for areas
            
            ###Determine metrics of identified regions (first one is always the background region)
            ###If the object is too small or too large to be confidently identified as a bead, flag the image for manual checking 
            for prop in regions:
                
                if prop.equivalent_diameter/pixels_to_um < diam_min and prop.equivalent_diameter < 0.95*len(img_gray[1]):
                    print("Flagged for manual check: Unidentified object in image. Location: {} \n\n".format(imgPath))
                    size_check = 1 #change the value of the flag
                if prop.equivalent_diameter/pixels_to_um > diam_max and prop.equivalent_diameter < 0.95*len(img_gray[1]):
                    print("Flagged for manual check: Unidentified object in image. Location: {} \n\n".format(imgPath))
                    size_check = 1 #change the value of the flag
                    
                #print("Label: {} Area: {} um^2 Equivalent Diameter:{} um".format(prop.label, prop.area/(pixels_to_um)**2, prop.equivalent_diameter/pixels_to_um))
                #uncomment above line to print characteristic for each region in each image
                
                ###Add diameters and areas to list as long as they are too small to be the background region
                if prop.equivalent_diameter<0.95*len(img_gray[1]):
                    diameters.append(round(prop.equivalent_diameter/pixels_to_um,2))
                    
                if prop.area<(0.85*len(img_gray[1]))**2:
                    areas.append(round(prop.area/(pixels_to_um)**2,2))
                    
        
                cell_count=cell_count+1 #increasing the cell count variable for each object identified
                
            ### Flag an object for manual checking if there is more than one cell identified   
            count[i]=cell_count
            
            if count[i]>1:
                print("Flagged for manual check: More than one bead identified. Location: {}\n\n".format(imgPath))
                count_check = 1 #change the value of the flag
                
            ### Determine which (if any) flags to write to .csv
            if size_check>0:
                check='Size warning'
            if count_check>0:
                check='Count warning'
            if size_check>0 and count_check>0:
                check = 'Size and count warning'
                
            ###writing info to .csv file
            writer.writerow({'Image': index, 
                             'Cell Count': cell_count, 
                             'Flags': check,
                             'Diameters (microns)': diameters,
                             'Areas (microns^2)': areas,
                             'File Path': imgPath,
                             'File Name': imgName})
            
              
    return count
#%%
    
###Examples for running the functions
    
nrows= 4
ncols= 3
dx=dy=900 #um
directory='C:\Users\Admin\Desktop\Emma\Test imgs\Mar4Beads'
array_label= 'arduino_mar4_beads_20X_4'
exposure_bf = 100 #ms
exposure_fl = 60 #ms

mag='40X'

#acquisition function
arrayAcquisition_ShutterControl(ncols, nrows, dx, dy, exposure_bf, exposure_fl, array_label,directory)

#analysis function
count= DropletCellCount(directory,array_label,nrows,ncols,mag)











