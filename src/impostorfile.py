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

#   Useful functions

def _insetrect(rect, insetwidth) :
    '''
    Rectangle inset insetwidth into rect
    '''
    insetrect = (rect[0] + insetwidth, rect[1] + insetwidth, rect[2] - insetwidth, rect[3] - insetwidth)
    if insetrect[0] >= insetrect[2] or insetrect[1] >= insetrect[3] :   # if degenerate
        return None
    if insetrect[0] >= rect[2] or insetrect[2] <= rect[0] or insetrect[1] >= rect[3] or insetrect[3] <= rect[1] :
        return None
    return(insetrect)


def combinestddev(s1, s2) :
    """
    Combine standard deviations. 
    Each input is (count, mean, stddev)
    Output is also (count, mean, stddev)
    
    Formula from
    https://en.wikipedia.org/wiki/Pooled_variance#Pooled_standard_deviation
    """
    pass    # ***MORE***

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
       
        
    def _frameuniformity(self, rect, insetwidth) :
        '''
        Measure uniformity for a frame whose outside is "rect" and
        whose thickness is "insetwidth".
        
        Input is (ulx, uly, llx, lly) tuple.
        
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
        sd0 = _rectstddev(rect0)
        sd1 = _rectstddev(rect1)
        sd2 = _rectstddev(rect2)
        sd3 = _rectstddev(rect3)
        
            
        pass # ***MORE***
        
    def _rectstddev(self, rect) :
        '''
        Run the uniformity test on a rectangle.
        '''
        croppedrgb = self.inputrgb.crop(rect)
        count = croppedrgb.count()                      # n number of pixels (3-tuple)
        mean = croppedrgb.mean()                        # μ average of pixels (3-tuple)
        stddev = croppedrgb.stddev()                    # σ stddev of pixels (3-tuple)
        devr = (count[0],mean[0],stddev[0])
        devg = (count[1],mean[1],stddev[1])
        devb = (count[2],mean[2],stddev[2])
        #   ***WRONG*** must not combine colors yet
        return(combinestddev(combinestddev(devr,devg),devb)) # combine all 3 color channels

