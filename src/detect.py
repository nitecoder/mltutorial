# encoding: utf-8

from argparse import ArgumentParser
import dlib
from skimage import io
from imagemeta import read_regions


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


def _to_dlib_regions(rs):
    res = []
    for r in rs:
        left = r.applied_x
        top = r.applied_y
        right = r.applied_x + r.applied_width
        bottom = r.applied_y + r.applied_height
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
        print (r1)
       
    if args.show:
        dlib.hit_enter_to_continue() 
    
# ---------------------------
if __name__ == "__main__":
    main()