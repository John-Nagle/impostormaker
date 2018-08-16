#
#   impostorfile.py - part of impostormaker
#
#   System for taking a set of images taken in Second Life and 
#   turning them into a properly aligned and measured texture for
#   a billboard impostor.
#
#   Images must be surrounded by a solid-color frame and should be backed
#   by a solid-color background. The images will be clipped to the frame
#   and the solid color background will be made transparent.
#
#   All the images are combined into one texture image, which is a power of
#   2 in size in both dimensions.
#
#
import PIL
import PIL.Image
import PIL.ImageStat
import PIL.ImageFilter
import PIL.ImageOps
import math
import greenscreen

#   Useful constants
GREEN_RANGE_MIN_HSV = (100, 80, 70)                 # green screen range
GREEN_RANGE_MAX_HSV = (185, 255, 255)

####GREENISH_RANGE_MIN_HSV = (100, 40, 35)              # green tinge range for cleanup
GREENISH_RANGE_MIN_HSV = (60, 40, 35  )              # ***TEMP TEST***
GREENISH_RANGE_MIN_HSV = (60, 0, 0  )              # ***TEMP TEST***
GREENISH_RANGE_MAX_HSV = (130, 255, 255)

#   Useful functions

def countrect(rect) :
    count = (1+rect[2]-rect[0]) * (1+rect[3]-rect[1])

def insetrect(rect, inset) :
    '''
    Rectangle bounds inset into rect
    '''
    insetrect = (rect[0] + inset, rect[1] + inset, rect[2] - inset, rect[3] - inset)
    if insetrect[0] >= insetrect[2] or insetrect[1] >= insetrect[3] :   # if degenerate
        return None
    if insetrect[0] >= rect[2] or insetrect[2] <= rect[0] or insetrect[1] >= rect[3] or insetrect[3] <= rect[1] :
        return None
    return(insetrect)
    
    
def colorinrange(color, colorrange) :
    '''
    Is color within bounds given?
    '''
    (locolor, hicolor) = colorrange # color limits
    if (color[0] < locolor[0]) or (color[0] > hicolor[0]) :
        return False            # out of bounds
    if (color[1] < locolor[1]) or (color[1] > hicolor[1]) :
        return False            # out of bounds
    if (color[2] < locolor[2]) or (color[2] > hicolor[2]) :
        return False            # out of bounds
    return True                     # color 
        
def combinestddev(x, y) :
    """
    Combine standard deviations. 
    Each input is (count, mean, stddev)
    Output is also (count, mean, stddev)
    
    Formula from
    https://en.wikipedia.org/wiki/Pooled_variance#Pooled_standard_deviation
    """
    (nx, ux, sx) = x                # count, mean, std dev
    (ny, uy, sy) = y
    n = nx + ny                     # total count
    if n <= 0 :                     # avoid divide by zero for empty case
        return (0,0.0,0.0)
    u = (nx*ux + ny*uy) / n         # average
    ssq = ((nx*sx*sx) + (ny*sy*sy))/n + ((nx*ny)/(n*n))*(ux-uy)*(ux-uy) # square of standard dev
    ####print("combinestddev: ", x, y, " -> ",(n,u,math.sqrt(ssq))); # ***TEMP***
    return (n, u, math.sqrt(ssq))   # return n, mean, standard dev
    
def combineuniformity(ua, ub) :
    '''
    Combine uniformity values for rectangles.
    '''
    unif =  [combinestddev(                         # returns list by colorchan of (count, mean, stddev)
        (ua[0][i], ua[1][i], ua[2][i]),
        (ub[0][i], ub[1][i], ub[2][i]))
        for i in range(len(ua))]
    unif = [(unif[0][i], unif[1][i], unif[2][i]) for i in range(len(unif))] # transpose
    ####print("combineuniformity: ",ua,ub, " -> ", unif)  # ***TEMP***
    return unif
    
    
      

class ImpostorFile:

    '''
    One input image for impostor building
    '''

    def __init__(self, impostor, filename) :
        self.impostor = impostor                        # parent object
        self.filename = filename                        # the filename
        self.inputimg = None                            # input image object
        self.inputrb = None                             # input image in RGB form
        
    def readimage(self) :                               
        '''
        Read image from file
        '''
        self.inputimg = PIL.Image.open(self.filename)
        self.inputrgb = self.inputimg.convert(mode="RGB")  # we want to work on this as RGB
        
    def show(self) :                                    
        '''
        Show image for debug purposes
        '''
        if self.inputimg :
            self.inputimg.show()                        # display for debug
            
    def findframe(self) :
        '''
        Find boundaries of a uniform colored frame around the image
        
        Raises exception if no reasonable frame
        '''
        pass                                            # ***MORE***
                
    def sweeph(self, top, bottom, xstart, xend, thickness, colorrange) :
        '''
        Sweep across the image horizontally in bands of "thickness"
        and return the most uniform band where the color is in colorrange.
        
        if xstart > xend, scan right to left.
        
        The bottom pixel is bottom-1, i.e. top=0, bottom=10 means 0..9
        '''
        incr = thickness
        if xstart > xend :                                  # invert incr if right to left
            incr = -incr
        beststddev = math.inf                               # best standard deviation seen
        bestx = None                                        # no hit yet
        for x in range(xstart,xend, incr) :
            (counts, means, stddevs) = self._rectstddev((min(x,x+incr), top, max(x, x+incr), bottom))  # scan a rectangle
            if not colorinrange(means, colorrange) :        # if color outside range for this scan (anywhere near red)
                continue                                    # ignore
            stddev = sum(stddevs) / 3                       # std dev of all 3 colors
            if stddev < beststddev :                        # new winner
                bestx = x
                beststddev = stddev
        return bestx                                        # winner, or none
                
    def sweepv(self, left, right, ystart, yend, thickness, colorrange) :
        '''
        Sweep across the image horizontally in bands of "thickness"
        and return the most uniform band where the color is in colorrange.
        
        if ystart > yend, scan bottom to top
        
        The bottom pixel is bottom-1, i.e. top=0, bottom=10 means 0..9
        '''
        incr = thickness
        if ystart > yend :                                  # invert incr if right to left
            incr = -incr
        beststddev = math.inf                               # best standard deviation seen
        besty = None                                        # no hit yet
        for y in range(ystart, yend, incr) :
            (counts, means, stddevs) = self._rectstddev((left, min(y,y+incr), right, max(y, y+incr)))  # scan a rectangle
            if not colorinrange(means, colorrange) :        # if color outside range for this scan (anywhere near red)
                continue                                    # ignore
            stddev = sum(stddevs) / 3                       # std dev of all 3 colors
            if stddev < beststddev :                        # new winner
                besty = y
                beststddev = stddev
        return besty                                        # winner, or none
        
    def findgreenscreencolor(self, rect, greenrange, maxalloweddev) :
        '''
        Find most prevalent color in green range for green screen removal
        
        Checks a thin area slightly inside the frame for uniformity
        
        ***NEEDS WORK*** should not need such a big allowed deviation
        '''
        INSETDIST = 10
        for insetdist in range(0,INSETDIST) :
            wrkrect = insetrect(rect, insetdist)                     # far enough in to escape edge noise
            (color, stddev) = self._framestddev(wrkrect, insetrect(wrkrect,1))
            if stddev > maxalloweddev :
                print("Findgreenscreencolor - could not find uniform green region. Std dev: ", stddev)
                continue
            if not colorinrange(color, greenrange) :
                print("Findgreenscreencolor - could not find uniform green region. Color: ", color)
                continue
            return color
        return None
        
    def tightenframe(self, outerrect, innerrect, maxalloweddev) :
        '''
        Tighten frame around image. Brings innerrect inward until no longer in
        an all-red area. The frame is the area between outerrect and innerect.
        
        Returns (rect, stddevofcolor)
        '''
        (left, top, right, bottom) = innerrect
        xcenter = int((left+right)/2)
        ycenter = int((top+bottom)/2)                       # center of the image

        #   Tighten frame around image
        print("Tightening from top: ", innerrect)
        innerrectgood = list(innerrect)                     # make modifiable
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        stddevgood = 0.0
        for y in range(innerrectgood[1], ycenter) :
            innerrectwrk[1] = y
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            if (stddev > maxalloweddev) :                   # can't reduce any more
                break
            innerrectgood[1] = y                            # OK, save
            stddevgood = stddev                             # valid stddev
        print("Rect: ",innerrectgood, " Stddev: ", stddevgood) # ***TEMP***
        #   Tighten from bottom
        print("Tightening from bottom: ", innerrect)
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for y in range(innerrectgood[3],ycenter,-1) :
            innerrectwrk[3] = y
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            if (stddev > maxalloweddev) :                   # can't reduce any more
                break
            innerrectgood[3] = innerrectwrk[3]              # OK, save
            stddevgood = stddev                             # valid stddev
        print("Rect: ",innerrectgood, " Stddev: ", stddevgood) # ***TEMP***
        #   Tighten from left
        print("Tightening from left: ", innerrectgood)
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for x in range(innerrectgood[0],ycenter) :
            innerrectwrk[0] = x
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            if (stddev > maxalloweddev) :                   # can't reduce any more
                break
            innerrectgood[0] = innerrectwrk[0]              # OK, save
            stddevgood = stddev                             # valid stddev
        print("Rect: ",innerrectgood, " Stddev: ", stddevgood) # ***TEMP***
        print("Tightening from right: ", innerrectgood)
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for x in range(innerrectgood[2],ycenter,-1) :
            innerrectwrk[2] = x
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            if (stddev > maxalloweddev) :                   # can't reduce any more
                break
            innerrectgood[2] = innerrectwrk[2]              # OK, save
            stddevgood = stddev                             # valid stddev
        print("Rect: ",innerrectgood, " Stddev: ", stddevgood) # ***TEMP***
        return (innerrectgood, stddevgood)                  # Returns rect
     
    def testsweeps(self) :
        '''
        Test and dump for sweep. Debug use only.
        '''
        MAXALLOWEDDEV = 1.0                                 # max std dev of pixels, units 0..255
        REDLIMITS = ((128,0,0),(255,63,63))                  # color range where red dominates
        ####GREENLIMITS = ((0,128,0),(128,255,128))              # color range where green dominates
        ####GREENTOL = 10                                       # green screen tolerance
        MAXCLEANDIST = 4                                    # go this far in from edge when cleaning edges
        EDGETHICKNESS = 1.5                                 # range for cleaning out green edge pixels
        
        imgrect = self.inputrgb.getbbox()                   # bounds of image
        (left, top, right, bottom) = imgrect
        height = bottom - top
        width = right -left
        scantop = top + int(height/4)                       # scan the middle half of the image
        scanbot = bottom - int(height/4)
        scanleft = left + int(width/4)
        scanright = right - int(width/4)
        xcenter = int((left+right)/2)
        ycenter = int((top+bottom)/2)                       # center of the image
        thickness = 10                                      # minimum frame width
        print("Test sweeps")
        xleft = self.sweeph(scantop, scanbot, left, xcenter, thickness, REDLIMITS)
        xright = self.sweeph(scantop, scanbot, right, xcenter, thickness, REDLIMITS)
        print("X frame limits: ", xleft, xright)
        ytop = self.sweepv(scanleft, scanright, top, ycenter, thickness, REDLIMITS)
        ybot = self.sweepv(scanleft, scanright, bottom, ycenter, thickness, REDLIMITS)
        print("Y frame limits: ", ytop, ybot)
        if not (xright is not None and xleft is not None and ytop is not None and ybot is not None) :
            print("Failed to find frame limits.")
            return None
        # Validate frame
        outerrect = (xleft, ytop, xright, ybot)
        innerrect = insetrect(outerrect, thickness)
        (color, stddev) = self._framestddev(outerrect, innerrect)
        print("Frame color: ",color, "Stddev: ",stddev)       
        if stddev > MAXALLOWEDDEV :
            print("Frame area is not uniform enough.")
            croppedrgb = self.inputrgb.crop(outerrect)      # extract rectangle of interest
            croppedrgb.show()                               # show failed frame
            return None
        #   Tighten frame around image
        (innerrectgood, stddev) = self.tightenframe(outerrect, innerrect, MAXALLOWEDDEV)
        #   Do green screen
        croppedimage = self.inputrgb.crop(innerrectgood)     # crop out frame
        croppedimage.show()
        #   Clip green in HSV space
        greenrangehsv = (GREEN_RANGE_MIN_HSV, GREEN_RANGE_MAX_HSV)
        greenishrangehsv = (GREENISH_RANGE_MIN_HSV, GREENISH_RANGE_MAX_HSV)
        maskedimage = greenscreen.removegreenscreen(croppedimage, greenrangehsv, greenishrangehsv,MAXCLEANDIST, EDGETHICKNESS, False)  # remove green screen
        maskedimage.show()
        maskedimage.save("/tmp/testmask.png")               # ***TEMP***
            
           
        
    def _framestddev(self, rect, innerrect) :
        '''
        Measure uniformity for a frame whose outside is "rect" and
        whose thickness is "insetwidth".
        
        Input is (ulx, uly, lrx, lry) tuple.
        
        Output is (color, stddev)
        '''
        #   Compute four non-overlapping rectangles that form the
        #   frame and combine them.
        if innerrect is None :                                  # None
            return None 
        if innerrect[0] < rect[0] or innerrect[1] < rect[1] or innerrect[2] > rect[2] or innerrect[3] > rect[3] :
            return None                                         # not properly nested
        if innerrect[0] >= innerrect[2] or innerrect[1] >= innerrect[3] :
            return None                                         # degenerate
        rect0 = (innerrect[0], rect[1], rect[2], innerrect[1])  # top
        rect1 = (innerrect[2], innerrect[1], rect[2], rect[3])  # right
        rect2 = (rect[0], innerrect[3], innerrect[2], rect[3])  # bottom
        rect3 = (rect[0], rect[1], innerrect[0], innerrect[3])  # left
        sd0 = self._rectstddev(rect0)
        sd1 = self._rectstddev(rect1)
        sd2 = self._rectstddev(rect2)
        sd3 = self._rectstddev(rect3)
        #    Combine uniformity data
        uchans = combineuniformity(combineuniformity(combineuniformity(sd0,sd1),sd2),sd3)
        (counts, means, stddevs) = uchans
        stddev = sum(stddevs) / len(stddevs)            # std dev from that color
        return (means, stddev)       
        
    def _rectstddev(self, rect) :
        '''
        Run the uniformity test on a rectangle.
        '''
        croppedrgb = self.inputrgb.crop(rect)           # extract rectangle of interest
        ####croppedrgb.show()                           # ***TEMP***
        stats = PIL.ImageStat.Stat(croppedrgb)          # image statistics
        return(stats.count, stats.mean, stats.stddev)
               
    def findframe(self, rect=None, minthickness=10) :
        '''
        Find solid color frame within rect
        
        The frame must be at least minthickness thick.
        '''
        if rect is None :                                   # if no rect given
            rect = self.inputrgb.getbbox()                  # use entire image
        if minthickness < 2 :                               # frame must be at least two pixels
            return None                                     # not meaningful
        #   ***MORE***

        

