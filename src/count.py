from PIL import Image
import numpy as np
import cv2 as cv
from pillow_heif import register_heif_opener

IMAGE_NUMBER = 1

#contains all the info to run houghCircles
class DetectionData:

    def __init__(self, method, dp, minDist, p1, p2, minRadius, maxRadius):
        self.method = method
        self.dp = dp
        self.minDist = minDist
        self.p1 = p1
        self.p2 = p2
        self.minRadius = minRadius
        self.maxRadius = maxRadius

def main():

    # oldDetection = DetectionData(cv.HOUGH_GRADIENT_ALT, 1, 10, 100, 0.9, 2, 50)

    newDetection = DetectionData(cv.HOUGH_GRADIENT_ALT, 1, 10, 100, 0.9, 2, 50)

    print("Opening Images")
    images = open_jpg(IMAGE_NUMBER)


    print("Recoloring images")
    images = [cv.cvtColor(recolor_image(img), cv.COLOR_BGR2GRAY) for img in images]
    
    #cv.imshow("recolored", images[0])
    #images = [cv.imread('2023-11-21\IMG_4574.jpg', cv.IMREAD_GRAYSCALE)]
    #images = [cv.imread('img1.jpg', cv.IMREAD_GRAYSCALE)]
    print("Detecting Dishes")
    dishes = np.empty(IMAGE_NUMBER, dtype='object')
    colonies = np.empty(IMAGE_NUMBER, dtype='object')
    for i in range(len(images)):
        #print(type(images[i]))
        #circles = cv.HoughCircles(img, cv.HOUGH_GRADIENT_ALT, 1, 10, param1=100,param2=0.9,minRadius=2,maxRadius=50)
        #print(circles)
        dishes[i] = detect_dish(images[i])
        #images[i] = annotate_image(images[i], dishes)

    print("Blacking out images")
    for i in range(len(images)):
        images[i] = blackout_image(images[i], dishes[i][0][0])

    print("Finding Colonies")
    for i in range(len(images)):
        colonies[i] = get_colonies(images[i], newDetection)
        #images[i] = #annotate_image(images[i], colonies)

    images = [cv.cvtColor(img, cv.COLOR_GRAY2BGR) for img in images]

    print("Saving Images")
    for i in range(len(images)):
        images[i] = annotate_image(images[i], colonies[i])
        cv.imwrite('2023-11-21-Annotated/IMG_' + str(i + 4574) + '.jpg', images[i])

def process_images_from_paths(paths):
    images = []

    # prepare reading of heic images
    register_heif_opener()

    for path in paths:
        
        if (path.lower().endswith(('.png', '.jpg', '.jpeg'))):
            image = cv.imread(path, cv.IMREAD_COLOR)
            # cv.imshow("Image", image)
            # cv.waitKey(0)
            # cv.destroyAllWindows()
            images.append(image)
        elif (path.lower().endswith(('.heic'))):
            # print("reading as heic")
            images.append(cv.cvtColor(np.array(Image.open(path).convert('RGB')), cv.COLOR_RGB2BGR))
        else:
            print("Could not find file: ", path)
        pass
    print("Number of images opened: " + str(len(images)))
    # Convert the images to black and white
    images = [cv.cvtColor(recolor_image(img), cv.COLOR_BGR2GRAY) for img in images]
    return process_images(images)

# this function processes a list of images stored as numpy arrays
def process_images(images, detection_data = DetectionData(cv.HOUGH_GRADIENT_ALT, 1, 10, 100, 0.9, 2, 50)):

    dishes = np.empty(len(images), dtype='object')
    colonies = np.empty(len(images), dtype='object')
    
    # detect dishes in images
    for i in range(len(images)): 
        dishes[i] = detect_dish(images[i])
        
    # black out image background
    for i in range(len(images)):
        images[i] = blackout_image(images[i], dishes[i][0][0])

    # Count the colonies
    for i in range(len(images)):
        colonies[i] = get_colonies(images[i], detection_data)

    images = [cv.cvtColor(img, cv.COLOR_GRAY2BGR) for img in images]

    # Annotate images
    for i in range(len(images)):
        images[i] = annotate_image(images[i], colonies[i])

    return colonies, images

# Oppens the images from 2023-11-21
def open_heic(num = 36):
    # This is required to open .HEIC images
    register_heif_opener()
    # open the images with modifeid pil since cv doesnt handle them, then convert them to np array, the cv format
    return np.array([cv.cvtColor(np.array(Image.open('2023-11-21/IMG_' + str(i) + '.HEIC').convert('RGB')), cv.COLOR_RGB2BGR) for i in range(4574,4574+num)])

# open jpg images (faster than open_heic)
def open_jpg(num = 36):
    return np.array([cv.imread('2023-11-21/IMG_' + str(i) + '.jpg', cv.IMREAD_COLOR) for i in range(4574,4574+num)])

def get_colonies(img, dd):
    img = cv.medianBlur(img, 5)
    circles = cv.HoughCircles(img, dd.method, dd.dp, dd.minDist, param1=dd.p1,param2=dd.p2,minRadius=dd.minRadius,maxRadius=dd.maxRadius)
    if (type(circles) != type(None)):
        circles = np.uint16(np.around(circles))
        return circles
    return None

# annotates an image based on colony circles (draws circles onto colonies)
def annotate_image(img, circles, c1=(0,255,0), c2 =(0, 0, 255)):
    # Colorize the image
    #TODO: Add color checker before recolorization
    #img = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
    for i in circles[0,:]:
        cv.circle(img, (i[0],i[1]), i[2], c1, 2)
        cv.circle(img, (i[0],i[1]), 2, c2, 3)
    return img

def recolor_image(img, cL=4.0, tGS=(8,8)):
    
    # converting to LAB color space
    lab= cv.cvtColor(img, cv.COLOR_BGR2LAB)
    l_channel, a, b = cv.split(lab)

    # Applying CLAHE to L-channel
    clahe = cv.createCLAHE(clipLimit=cL, tileGridSize=tGS)
    cl = clahe.apply(l_channel)

    # merge the CLAHE enhanced L-channel with the a and b channel
    limg = cv.merge((cl,a,b))

    # Converting image from LAB Color model to BGR color spcae
    enhanced_img = cv.cvtColor(limg, cv.COLOR_LAB2BGR)

    # Stacking the original image with the enhanced image
    return np.hstack((img, enhanced_img))

# return an image with all pixels outside of the circle colored black
def blackout_image(img, circle):
    # create a blackout mask of the image
    mask = np.zeros_like(img)
    mask = cv.circle(mask, (circle[0], circle[1]), circle[2], (255,255,255), -1)
    # combine the mask with the image and return it
    return cv.bitwise_and(img, mask)

def detect_dish(img):
    #TODO: Ensure that detect dish only finds one circle
    img = cv.medianBlur(img, 5)
    circles = cv.HoughCircles(img,cv.HOUGH_GRADIENT_ALT,1.5,5,param1=300,param2=0.97,minRadius=100,maxRadius=0)
    if (type(circles) != type(None)):
        circles = np.uint16(np.around(circles))
        return circles
    return None

if (__name__ == "__main__"):
  # main()
    colonies, images = process_images_from_paths(["img1.jpg", "img1.jpg", "2023-11-21\IMG_4605.HEIC"])
    for c in colonies:
        print(len(c[0]))