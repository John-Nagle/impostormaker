#
#   greenscreen.py - part of impostormaker
#
#   Green screen removal support
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

#   Useful constants
GREEN_RANGE_MIN_HSV = (100, 80, 70)                 # green screen range
GREEN_RANGE_MAX_HSV = (185, 255, 255)

####GREENISH_RANGE_MIN_HSV = (100, 40, 35)              # green tinge range for cleanup
GREENISH_RANGE_MIN_HSV = (60, 40, 35  )              # ***TEMP TEST***
GREENISH_RANGE_MIN_HSV = (60, 0, 0  )              # ***TEMP TEST***
GREENISH_RANGE_MAX_HSV = (130, 255, 255)

#   Useful functions
    
def rgb_to_hsv(r, g, b) :
    '''
    RGB to HSV color space, only for green screening
    
    Inputs and outputs are all in 0..1 range.
    
    From    
    https://github.com/kimmobrunfeldt/howto-everything/blob/master/remove-green.md
    '''
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return 0.0, 0.0, v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v
    
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
    
    
def balancegreentingepixel(color, greentingerange) :
    '''
    Balance a color with a greenish tinge.
    
    Color must be (r,g,b,a)
    
    This is applied only to edge pixels, so we can be a bit more
    aggressive than if we applied it to the whole image.
    '''
    (r, g, b, a) = color
    if a == 0 :                     # do not modify if alpha is zero
        return color
    h_ratio, s_ratio, v_ratio = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    hsvcolor = (h_ratio * 360, s_ratio * 255, v_ratio * 255)
    if not colorinrange(hsvcolor, greentingerange) :   # if not in greenish tint range
        return(color)               # no change
    g = min(g, int((r+b)/2))        # make non green
    return(r,g,b,128)               # return at half alpha

    
def balancegreentinge(img, edgemask, greentingerange) :
    '''
    Remove greenish tinge in-place.
    '''
    pix = img.load()
    msk = edgemask.load()                # only do areas with nonzero mask
    (left, top, right, bottom) = img.getbbox()
    for x in range(left, right) :   # apply pixel fix to all pixels
        for y in range(top, bottom) :
            m = msk[x,y]
            if m == 0 :             # skip if not in edge mask
                continue
            pix[x,y] = balancegreentingepixel(pix[x,y],greentingerange)
            
def invertwhite(n) :
    '''
    Invert full value in an image channel.
    
    Used in blanking out the interior of an alpha mask in createedgemask.
    '''
    if n > 254 :
        return(0)
    return n
            
def createedgemask(mask, distance) :
    '''
    Create a mask that includes only pixels within a
    few pixels of the edge.
    '''
    blurmask = mask.filter(PIL.ImageFilter.GaussianBlur(distance))  # construct blurred mask
    edgemask = PIL.Image.new("L",mask.size,0)       # empty alpha mask
    edgemask.paste(blurmask, mask)                  # edges only
    return edgemask.point(invertwhite)              # blank out interior of image  
    
def makegreenscreenmask(img, colorrange) :
    '''
    Make green screen mask. Colorrange is the range of green to be masked.
    Colorrange is in HSV form, but the image is RGB.
    '''
    (min_h, min_s, min_v),(max_h, max_s, max_v) = colorrange    # HSV bounds
    pix = img.load()                                    # force into memory
    width, height = img.size
    mask = PIL.Image.new("L",img.size,0)                # create matching alpha mask
    mpix = mask.load()                                  # force into memory
    #   Scan for green pixels
    for x in range(width):
        for y in range(height):
            r, g, b = pix[x, y]
            h_ratio, s_ratio, v_ratio = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            h, s, v = (h_ratio * 360, s_ratio * 255, v_ratio * 255)
            if min_h <= h <= max_h and min_s <= s <= max_s and min_v <= v <= max_v:
                v = 0
            else :
                v = 255
            mpix[x,y] = v
    return mask    
    
def cleanmaskouteredge(mask, maxdist) :
    '''
    Remove any nonzero pixels at the outer edge of the mask image.
    
    This cleans up any junk left over by cropping.
    '''
    (left, top, right, bottom) = mask.getbbox()
    pix = mask.load()                                   # force into memory
    for x in range(left, right) :                       # do top and bottom
        for y in range(top, top+maxdist) :              # clean inward from top
            if pix[x,y] > 0 :
                pix[x,y] = 0
            else :
                break                                   # no more pixels in this column
        for y in range(bottom-1, bottom-maxdist-1,-1) : # clean inward from bottom
            if pix[x,y] > 0 :
                pix[x,y] = 0
            else :
                break 
    for y in range(top, bottom) :                       # do left and right
        for x in range(left, left+maxdist) :            # clean inward from left
            if pix[x,y] > 0 :
                pix[x,y] = 0
            else :
                break 
        for x in range(right-1, right-maxdist-1,-1) :   # clean inward from bottom
            if pix[x,y] > 0 :
                pix[x,y] = 0
            else :
                break 
                
def removegreenscreen(img, greenrangehsv, greenishrangehsv,maxcleandist, edgethickness, verbose=False) :
    '''
    Remove green screen from image
    '''
    mask = makegreenscreenmask(img, greenrangehsv)
    cleanmaskouteredge(mask, maxcleandist)              # clean up mask outer edge
    if verbose :
        mask.show()
    maskedimage = PIL.Image.new("RGBA",img.size)        # output is RGBA image
    maskedimage.paste(img ,mask)                        # create RGBA transparent where green was
    maskedimage.putalpha(mask)                          # add alpha channel
    if verbose :
        maskedimage.show()                              # after removing green screen
    edgemask = createedgemask(mask,edgethickness)
    if verbose :
        edgemask.show()
    balancegreentinge(maskedimage, edgemask, greenishrangehsv)
    return maskedimage                                  # output is RGBA image                          

                
#   Unit test

def unittest() :
    import glob
    greenrangehsv = (GREEN_RANGE_MIN_HSV, GREEN_RANGE_MAX_HSV)
    greenishrangehsv = (GREENISH_RANGE_MIN_HSV, GREENISH_RANGE_MAX_HSV)
    MAXCLEANDIST = 4                                    # optional outer edge cleanup
    EDGETHICKNESS = 1.5                                 # green noise area range
    TESTFILES = "../testdata/greenscreen/*.jpg"
    testfiles = glob.glob(TESTFILES)                    # get list of files to test
    for testfile in testfiles :
        print("File: " + testfile)                      # working on this file
        img = PIL.Image.open(testfile)
        img2 = removegreenscreen(img, greenrangehsv, greenishrangehsv,MAXCLEANDIST, EDGETHICKNESS, False)  # remove green screen
        img2.show()
    print("Test complete. Check the images.")
    



if __name__ == "__main__" :                             # if running standalone
    unittest()
      


