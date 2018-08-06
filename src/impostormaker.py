#
#   Imposter maker for Second Life
#
#   John Nagle
#   August, 2018.
#
#   License: GPLv3
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
import argparse
import glob
import PIL
import PIL.Image
import impostorfile

class Impostor :

    #   Constructor
    def __init__(self, args) :
        self.options = args
        print("File args: ", args.files)                # ***TEMP***
        self.filenames = args.files
        self.impostorfiles = []                         # impostor file object
        
    #   Read in all files
    def readfiles(self) :
        for name in self.filenames :
            ifile = impostorfile.ImpostorFile(self, name)            # object for this input image
            ifile.readimage()                           # read the image
            if self.options.verbose :
                ####ifile.show()                            # show image if verbose
                ifile.testsweeps()
                return                                  # ***TEMP***
            self.impostorfiles.append(ifile)            # accumulate image objects
            
        
  

def parseargs() :
     #  Parse command line options
     parser = argparse.ArgumentParser(description="Second Life impostor generator")                 # usual argument parser
     parser.add_argument("--width", dest="width", metavar="W", type=float, default=6.0, help="Width of image frame in meters")
     parser.add_argument("--height", dest="height", metavar="H", type=float, default=3.0, help="Width of image frame in meters")
     parser.add_argument("--rez", dest="rez", metavar="OUTPUTWIDTH", type=int, default=64, help="Width of each output image in pixels.")
     parser.add_argument("--faces", dest="faces", metavar="N", default="8", help="Total faces, including top and bottom.")
     parser.add_argument("--form", dest="form", metavar="FORMNAME", default="STAR", help="STAR = N faces in a star pattern. TSTAR: Star plus top and bottom.")
     parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Verbose mode")
     parser.add_argument("files", nargs='+')
     args = parser.parse_args()
     #  Option validation
     return args
     
#   Main program
def main() :
    args = parseargs()                              # parse and check options
    imp = Impostor(args)                            # create main impostor object
    imp.readfiles()                                 # read in all images

     
#   Run program
main()
