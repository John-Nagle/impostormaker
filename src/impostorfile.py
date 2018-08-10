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
    ssq = ((nx*ux*ux) + (ny*uy*uy))/n + ((nx*ny)/(n*n))*(ux-uy)*(ux-uy) # square of standard dev
    return (n, u, math.sqrt(ssq))   # return n, mean, standard dev

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
            (counts, means, stddevs) = self._rectuniformity((min(x,x+incr), top, max(x, x+incr), bottom))  # scan a rectangle
            if not colorinrange(means, colorrange) :        # if color outside range for this scan (anywhere near red)
                continue                                    # ignore
            stddev = sum(stddevs) / 3                       # std dev of all 3 colors
            if stddev < beststddev :                        # new winner
                bestx = x
                beststdddev = stddev
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
            (counts, means, stddevs) = self._rectuniformity((left, min(y,y+incr), right, max(y, y+incr)))  # scan a rectangle
            ####print("Sweepv: ",y,means, rect)                       # ***TEMP***
            if not colorinrange(means, colorrange) :        # if color outside range for this scan (anywhere near red)
                continue                                    # ignore
            stddev = sum(stddevs) / 3                       # std dev of all 3 colors
            if stddev < beststddev :                        # new winner
                besty = y
                beststdddev = stddev
        return besty                                        # winner, or none
                
     
    def testsweeps(self) :
        '''
        Test and dump for sweep. Debug use only.
        '''
        REDRANGE = ((128,0,0),(255,127,127))                # color range where red dominates
        imgrect = self.inputrgb.getbbox()                   # bounds of image
        (left, top, right, bottom) = imgrect
        height = bottom - top
        width = right -left
        scantop = top + int(height/4)                       # scan the middle half of the image
        scanbot = bottom - int(height/4)
        scanleft = left + int(width/4)
        scanright = right - int(width/4)
        thickness = 5                                       # minimum frame width
        print("Test horizontal sweeps")
        xleft = self.sweeph(scantop, scanbot, left, int((left+right)/2), thickness, REDRANGE)
        xright = self.sweeph(scantop, scanbot, right, int((left+right)/2), thickness, REDRANGE)
        print("X frame limits: ", xleft, xright)
        print("Test vertical sweeps")
        ytop = self.sweepv(scanleft, scanright, top, int((top+bottom)/2), thickness, REDRANGE)
        ybot = self.sweepv(scanleft, scanright, bottom, int((top+bottom)/2), thickness, REDRANGE)
        print("Y frame limits: ", ytop, ybot)
        if (xright is not None and xleft is not None and ytop is not None and ybot is not None) :
            viewrect = (xleft, ytop, xright, ybot)
            croppedrgb = self.inputrgb.crop(viewrect)           # extract rectangle of interest
            croppedrgb.show()                                   # ***TEMP***
       
        
    def _frameuniformity(self, rect, insetwidth) :
        '''
        Measure uniformity for a frame whose outside is "rect" and
        whose thickness is "insetwidth".
        
        Input is (ulx, uly, lrx, lry) tuple.
        
        Output is (uniformity, color)
        '''
        #   Compute four non-overlapping rectangles that form the
        #   frame and combine them.
        innerrect = insetrect(rect, insetwidth)
        if innerrect is None :                          # degenerate
            return(None)
        rect0 = (innerrect[0], rect[1], rect[2], innerrect[1])  # top
        rect1 = (innerrect[3], innerrect[1], rect[2], rect[3])  # right
        rect2 = (rect[0], innerrect[3], innerrect[2], rect[3])  # bottom
        rect3 = (rect[0], rect[1], innerrect[0], innerrect[3])  # left
        sd0 = _rectuniformity(rect0)
        sd1 = _rectuniformity(rect1)
        sd2 = _rectuniformity(rect2)
        sd3 = _rectuniformity(rect3)
        #    Combine uniformity data
        uchans = combineuniformity(combineuniformity(combineuniformity(sd0,sd1),sd2),sd3)
        (counts, means, stddevs) = uchans
        color = means                                   # mean color
        stddev = avg(stddevs)                           # std dev from that color
        return (color, stddev)
        
        
    def _combineuniformity(self, ua, ub) :
        '''
        Combine uniformity values for rectangles.
        '''
        return [combinestddev(                          # returns list by colorchan of (count, mean, stddev)
            (ua[0][i], ua[1][i], ua[2][i]),
            (ub[0][i], ub[1][i], ub[2][i]))
            for i in range(length(u1))]
        
    def _rectuniformity(self, rect) :
        '''
        Run the uniformity test on a rectangle.
        '''
        croppedrgb = self.inputrgb.crop(rect)           # extract rectangle of interest
        ####croppedrgb.show()                           # ***TEMP***
        stats = PIL.ImageStat.Stat(croppedrgb)          # image statistics
        return(stats.count, stats.mean, stats.stddev)
        
    def findframeold(self, sweepsize=0.5, colorhint=None) :
        '''
        Find solid color frame around image of interest.
        
        Sweep size is the size of the band used to sweep
        across looking for solid color areas. 0.5 means
        half the image height or width.
        
        If color hint is given, colors closer to it will
        be preferred.
        '''
        #   Phase 1: Sweep horizontally and vertically to find the rough frame bounds
        (left, top, right, bottom) = self.inputrgb.getbbox()  
        scanthickness = 5                                   # scan a rect 5 pixels at a time
        #   Horizontal scan
        height = bottom-top+1
        scantop = top + int(height*sweepsize*0.5)           # scan the middle half of the image
        scanbot = bottom - int(height*sweepsize*0.5)
        scanh = self.sweeph(scantop, scanbot, width)
        #   Vertical scan
        width = right-left+1
        scanleft = left + int(width*sweepsize*0.5)
        scanright = right -int(width*sweepsize*0.5)
        scanh = self.sweepv(scanleft, scanright, width)
        
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

        

