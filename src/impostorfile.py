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
        self.inputimg = PIL.Image.open(self.filename, mode="r")
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
        
    def sweeph(self, top, bottom, width) :
        '''
        Sweep across the image horizontally in bands and return
        the standard deviation for each band. 
        '''
        imgrect = self.inputimg.getbbox()                    # bounds of image
        return [self._rectuniformity((x, top, x+width-1, bottom)) for x in range(imgrect[0], imgrect[2]-width-1, width)]
            
        
    def sweepv(self, left, right, height) :
        '''
        Sweep across the image horizontally in bands and return
        the standard deviation for each band. 
        '''
        imgrect = self.inputimg.getbbox()                    # bounds of image
        return [self._rectuniformity((left, y, right, y+height-1)) for y in range(imgrect[1], imgrect[3]-height-1, height)]
        
    def testsweeps(self) :
        '''
        Test and dump for sweep
        '''
        imgrect = self.inputimg.getbbox()                    # bounds of image
        (left, top, bottom, right) = imgrect
        height = bottom-top+1
        scantop = top + int(height/4)                   # scan the middle half of the image
        scanbot = bottom - int(height/4)
        width = 10                                      # band width 10 pixels
        print("Test horizontal sweep")
        scanres = self.sweeph(scantop, scanbot, width)
        for i in range(len(scanres)) :
            print(scanres[i])
        print("")
       
        
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
        print(rect) # ***TEMP***
        croppedrgb = self.inputrgb.crop(rect)           # extract rectangle of interest
        stats = PIL.ImageStat.Stat(croppedrgb)          # image statistics
        return(stats.count, stats.mean, stats.stddev)

