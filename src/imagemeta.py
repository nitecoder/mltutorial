# encoding: utf-8

import piexif
from libxmp.utils import file_to_dict

# Functions for working with Image Metadata
#

class MWG:
    RS_NS="http://www.metadataworkinggroup.com/schemas/regions/"
    RS_AppliedTo_w="mwg-rs:Regions/mwg-rs:AppliedToDimensions/stDim:w" # 1000
    RS_AppliedTo_h="mwg-rs:Regions/mwg-rs:AppliedToDimensions/stDim:h" # 661
    RS_AppliedTo_unit="mwg-rs:Regions/mwg-rs:AppliedToDimensions/stDim:unit" # pixel
    
    RS_Region_Rotation="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Rotation" #: -1.41981                
    RS_Region_Name="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Name" #: Elvis Presley  
    RS_Region_Type="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Type" #: Face                        
    RS_Region_Area_h="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:h" #: 0.10747           
    RS_Region_Area_w="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:w" #: 0.07105            
    RS_Region_Area_x="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:x" #: 0.21682   # center x         
    RS_Region_Area_y="mwg-rs:Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:y" #: 0.43201   # center y         

class Region:
    def __init__(self, center_x, center_y, height, width, name, rotation, region_type):
        self.center_x = center_x
        self.center_y = center_y
        self.height = height
        self.width = width
        self.rotation = rotation
        self.name = name
        self.type = region_type
        
    def apply(self, applied_to_w, applied_to_h, applied_to_unit, rounder=None):
        self.applied_to_w = applied_to_w
        self.applied_to_h = applied_to_h
        self.applied_to_unit = applied_to_unit

        if not rounder:
            rounder = lambda x: x
                    
        self.applied_width = rounder(self.width * self.applied_to_w)
        self.applied_height = rounder(self.height * self.applied_to_h)
        self.applied_center_x = rounder(self.center_x * self.applied_to_w)
        self.applied_center_y = rounder(self.center_y * self.applied_to_h)
        
        self.applied_x = rounder(self.center_x * self.applied_to_w - self.applied_width / 2)
        self.applied_y = rounder(self.center_y * self.applied_to_h - self.applied_height / 2)
        
        
    def __repr__(self):
        return str([(self.center_x, self.center_y), (self.width, self.height), 
                {"type": self.type, "name":self.name, "rotation":self.rotation,
                 "applied_to": (self.applied_to_w, self.applied_to_h)}])
    

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
            
def read_all_meta(filename):
    """Reads the provided file and returns all metadata in a dictionary specified by 
       file_to_dict from libxmp.
       { <ns> : [ ( <key>, <value>, <options> ), ... ], ... }
           where:
               <ns> is a namespace URI
               <key> is the key of the property
               <value> is the value
               <options> is a dictionary of standard options, if any
    """
    xmp = file_to_dict(filename)
    return xmp
    
def _get_prop(props, prop_name, func=None):
    tup = props.get(prop_name, None)
    if not tup:
        return None
    
    opts = tup[2]
    
    #print ("'%s': '%s'" % (tup[0], tup[1]))
    #print ("Options %s" % opts)

    # for now let's ignore options. But if they are needed they are at index [2]
    return func(tup[1]) if func else tup[1]
    
    
def read_regions(filename_or_dict):
    """Read the provided file and extrac region metadata from it.
       Argument can be a filename or a dictionary returned from :read_all_meta
       Returns list of :Region objects.
    """
    if not isinstance(filename_or_dict, dict):
        xmp = file_to_dict(filename_or_dict)
    else:
        xmp = filename_or_dict
        
    MWG.rs = xmp.get(MWG.RS_NS, None)
    if not MWG.rs:
        return None
    
    # index the elements into a dictionary for easy access
    props = {}
    for tup in MWG.rs:
        props[tup[0]] = tup

    # get the dimensions
    applied_to_h = _get_prop(props, MWG.RS_AppliedTo_h, num)
    applied_to_w = _get_prop(props, MWG.RS_AppliedTo_w, num)
    applied_to_unit = _get_prop(props, MWG.RS_AppliedTo_unit) # assume pixel for now

    if not applied_to_h or not applied_to_w:
        print ("ERR: %s: Missing AppliedTo H or W" % (filename_or_dict))
        # TODO: should default to other image dimensions instead
        return None
    
    regions = []
    i = 0
    while True:
        i += 1
        r = Region(
                center_x = _get_prop(props, MWG.RS_Region_Area_x % i, num),
                center_y = _get_prop(props, MWG.RS_Region_Area_y % i, num),
                height = _get_prop(props, MWG.RS_Region_Area_h % i, num),
                width = _get_prop(props, MWG.RS_Region_Area_w % i, num),
                rotation = _get_prop(props, MWG.RS_Region_Rotation % i, num),
                name = _get_prop(props, MWG.RS_Region_Name % i),
                region_type = _get_prop(props, MWG.RS_Region_Type % i)
            )

        if not r.center_x:
            # ran out of regions, exit
            break
        
        if not r.center_y or not r.height or not r.width:
            print ("ERR: %s: Region %d has incomplete settings: %s" % (i, filename_or_dict, r))
            continue
        
        r.apply(applied_to_w, applied_to_h, applied_to_unit, int)
        
        # Assume they are all faces for now
        regions.append(r)

    return regions