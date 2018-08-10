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
import math

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
    for i in range(len(color)) :    # test each color channel
        if (color[i] < locolor[i]) or (color[i] > hicolor[i]) :
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
        ####self.inputrgb = self.inputimg # ***TEMP***
        
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
                print("Best stddev x: ",x,beststddev)       # ***TEMP***
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
            ####print("Sweepv: ",y,means, rect)                       # ***TEMP***
            if not colorinrange(means, colorrange) :        # if color outside range for this scan (anywhere near red)
                continue                                    # ignore
            stddev = sum(stddevs) / 3                       # std dev of all 3 colors
            if stddev < beststddev :                        # new winner
                besty = y
                beststddev = stddev
        return besty                                        # winner, or none
                
     
    def testsweeps(self) :
        '''
        Test and dump for sweep. Debug use only.
        '''
        MAXALLOWEDDEV = 5.0                                 # max std dev of pixels, units 0..255
        REDRANGE = ((128,0,0),(255,63,63))                  # color range where red dominates
        GREENRANGE = ((0,128,0),(128,255,128))              # color range where green dominates
        
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
        thickness = 10 ### 5                                       # minimum frame width
        print("Test sweeps")
        xleft = self.sweeph(scantop, scanbot, left, xcenter, thickness, REDRANGE)
        xright = self.sweeph(scantop, scanbot, right, xcenter, thickness, REDRANGE)
        print("X frame limits: ", xleft, xright)
        ytop = self.sweepv(scanleft, scanright, top, ycenter, thickness, REDRANGE)
        ybot = self.sweepv(scanleft, scanright, bottom, ycenter, thickness, REDRANGE)
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
        print("Tightening from top: ", innerrect)
        innerrectgood = list(innerrect)                     # make modifiable
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for y in range(innerrectgood[1], ycenter) :
            innerrectwrk[1] = y
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            print("Rect: ",innerrectwrk, " Stddev: ", stddev) # ***TEMP***
            if (stddev > MAXALLOWEDDEV) :                   # can't reduce any more
                break
            innerrectgood[1] = y                            # OK, save
        #   Tighten from bottom
        print("Tightening from bottom: ", innerrect)
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for y in range(innerrectgood[3],ycenter,-1) :
            innerrectwrk[3] = y
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            print("Rect: ",innerrectwrk, " Stddev: ", stddev) # ***TEMP***
            if (stddev > MAXALLOWEDDEV) :                   # can't reduce any more
                break
            innerrectgood[3] = innerrectwrk[3]              # OK, save
        #   Tighten from left
        print("Tightening from left: ", innerrect)
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for x in range(innerrectgood[0],ycenter) :
            innerrectwrk[0] = x
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            print("Rect: ",innerrectwrk, " Stddev: ", stddev) # ***TEMP***
            if (stddev > MAXALLOWEDDEV) :                   # can't reduce any more
                break
            innerrectgood[0] = innerrectwrk[0]              # OK, save
        print("Tightening from right: ", innerrect)
        innerrectwrk = list(innerrectgood)                  # copy, not ref
        for x in range(innerrectgood[2],ycenter,-1) :
            innerrectwrk[2] = x
            (color, stddev) = self._framestddev(outerrect, innerrectwrk)
            print("Rect: ",innerrectwrk, " Stddev: ", stddev) # ***TEMP***
            if (stddev > MAXALLOWEDDEV) :                   # can't reduce any more
                break
            innerrectgood[2] = innerrectwrk[2]              # OK, save
        self.inputrgb.crop(innerrectgood).show()            # show reduced frame
        
            
            
       
        
    def _framestddev(self, rect, innerrect) :
        '''
        Measure uniformity for a frame whose outside is "rect" and
        whose thickness is "insetwidth".
        
        Input is (ulx, uly, lrx, lry) tuple.
        
        Output is (color, stddev)
        '''
        #   Compute four non-overlapping rectangles that form the
        #   frame and combine them.
        print("rects: ",rect, innerrect)
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
        ####self.inputrgb.crop(rect1).show()    # ***TEMP***
        sd0 = self._rectstddev(rect0)
        sd1 = self._rectstddev(rect1)
        sd2 = self._rectstddev(rect2)
        sd3 = self._rectstddev(rect3)
        print("sd0: ",sd0)  # ***TEMP***
        print("sd1: ",sd1)  # ***TEMP***
        print("sd2: ",sd2)  # ***TEMP***
        print("sd3: ",sd3)  # ***TEMP***
        #    Combine uniformity data
        uchans = combineuniformity(combineuniformity(combineuniformity(sd0,sd1),sd2),sd3)
        print("uchans: ", uchans) # ***TEMP***
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

        

