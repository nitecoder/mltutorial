# encoding: utf-8

from argparse import ArgumentParser
import dlib
from skimage import io
import piexif
from libxmp.utils import file_to_dict

MWG_RS_NS="http://www.metadataworkinggroup.com/schemas/regions/"
MWG_RS_AppliedTo_w="mwg-rs:Regions/mwg-rs:AppliedToDimensions/stDim:w" # 1000
MWG_RS_AppliedTo_h="mwg-rs:Regions/mwg-rs:AppliedToDimensions/stDim:h" # 661
MWG_RS_AppliedTo_unit="mwg-rs:Regions/mwg-rs:AppliedToDimensions/stDim:unit" # pixel

MWG_RS_Region_Rotation="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Rotation" #: -1.41981                
MWG_RS_Region_Name="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Name" #: Elvis Presley  
MWG_RS_Region_Type="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Type" #: Face                        
MWG_RS_Region_Area_h="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:h" #: 0.10747           
MWG_RS_Region_Area_w="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:w" #: 0.07105            
MWG_RS_Region_Area_x="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:x" #: 0.21682   # center x         
MWG_RS_Region_Area_y="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:y" #: 0.43201   # center y         

# Create a HOG face detector using the built-in dlib class
face_detector = dlib.get_frontal_face_detector()

win = dlib.image_window()


def show_faces(filename, regions):
    image = io.imread(filename)

    print ("Opening window")
    win.set_image(image)
    for i, face_rect in enumerate(regions):
        win.add_overlay(face_rect)
            
    
def detect_faces(filename, show=False):
    image = io.imread(filename)
    detected_faces = face_detector(image, 1)
    return detected_faces


def dump_exif(filename):
    data = piexif.load(filename)
    print ("Loaded EXIF with %s" % data.keys())
    for k in ["0th", "1st", "Interop", "GPS"]:
        print ("%s %s" % (k, data.get(k, None)))
        
def dump_xmp(filename):
    print ("Printing XMP")
    xmp = file_to_dict(filename)
    for ns in xmp.keys():
        print ("%s" % ns)
        dc = xmp[ns]
        for dc_tuple in dc:
            print ("   %s: %s" % (dc_tuple[0], dc_tuple[1]))
            #if dc_tuple[2]:
            #    print ("   %s options: %s" % (dc_tuple[0], dc_tuple[2]))

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)
            
def read_regions(filename):
    xmp = file_to_dict(filename)
    mwg_rs = xmp.get(MWG_RS_NS, None)
    if not mwg_rs:
        return None
    
    # index the elements into a dictionary for easy access
    props = {}
    for tup in mwg_rs:
        props[tup[0]] = tup

    def _get_prop(prop_name, func=None):
        tup = props.get(prop_name, None)
        if not tup:
            return None
        
        opts = tup[2]
        
        #print ("'%s': '%s'" % (tup[0], tup[1]))
        #print ("Options %s" % opts)

        # for now let's ignore options. But if they are needed they are at index [2]
        return func(tup[1]) if func else tup[1]
        
    # get the dimensions
    applied_to_h = _get_prop(MWG_RS_AppliedTo_h, num)
    applied_to_w = _get_prop(MWG_RS_AppliedTo_w, num)
    applied_to_unit = _get_prop(MWG_RS_AppliedTo_unit) # assume pixel for now

    if not applied_to_h or not applied_to_w:
        print ("ERR: %s: Missing AppliedTo H or W" % (filename))
        return None
    
    regions = []
    i = 0
    while True:
        i += 1
        r = {
            "x" : _get_prop(MWG_RS_Region_Area_x % i, num),
            "y" : _get_prop(MWG_RS_Region_Area_y % i, num),
            "h" : _get_prop(MWG_RS_Region_Area_h % i, num),
            "w" : _get_prop(MWG_RS_Region_Area_w % i, num),
            "rotation" : _get_prop(MWG_RS_Region_Rotation % i, num),
            "name" : _get_prop(MWG_RS_Region_Name % i),
            "type" : _get_prop(MWG_RS_Region_Type % i)
        }
        if not r['x']:
            # ran out of regions, exit
            break
        
        if not r['y'] or not r['h'] or not r['w']:
            print ("ERR: %s: Region %d has incomplete settings: %s" % (i, filename, r))
            continue
        
        r['w'] = int(r['w'] * applied_to_w)
        r['h'] = int(r['h'] * applied_to_h)
        r['x'] = int(r['x'] * applied_to_w - r['w'] / 2)
        r['y'] = int(r['y'] * applied_to_h - r['h'] / 2)
        
        # Assume they are all faces for now
        regions.append(r)

    return regions

def _to_dlib_regions(rs):
    res = []
    for r in rs:
        left = r['x']
        top = r['y']
        right = r['x'] + r['w']
        bottom = r['y'] + r['h']
        res.append(dlib.rectangle(left=left, top=top, right=right, bottom=bottom))
    return res
    
def main():
    parser = ArgumentParser()
    parser.add_argument("--show", dest="show", help="Show image with detected faces", action="store_true")
    parser.add_argument(dest="files", help="Image files to process", nargs="+")
    
    args = parser.parse_args()
    
    for f in args.files:
        #exif = load_exif(f)
        #load_xmp(f)
        r1 = read_regions(f)
        show_faces(f, _to_dlib_regions(r1))
        
        res = detect_faces(f, args.show)
        print ("%s :: %s of %s" % (f, len(res), len(r1)))
        print ("%s" % res[0])
       
    if args.show:
        dlib.hit_enter_to_continue() 
    
# ---------------------------
if __name__ == "__main__":
    main()