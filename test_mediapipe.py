import os
import mediapipe as mp
import cv2
from library import fetchPathNames

with mp.selfie_segmentation.SelfieSegmentation(
    model_selection=0) as selfie_segmentation:
    
    for name in fetchPathNames("./test_images"):
        src=cv2.imread(name,cv2.IMREAD_COLOR)
    
