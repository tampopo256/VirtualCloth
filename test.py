import os
import numpy as np
import numpy.typing as npt
import cv2
import sys
from library import fetchPathNames

# 定数定義
WINDOW_H=512
WINDOW_W=1024

# メイン処理
path_names=fetchPathNames("./test_images")
path_names.sort()
imgs=[]

for path_name in path_names:
    window_name=f"Path Name:{path_name}"
    img=cv2.imread(path_name,cv2.IMREAD_COLOR)
    imgs.append(img)
    # 内容確認
    cv2.namedWindow(window_name,cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name,(WINDOW_W,WINDOW_H))
    cv2.moveWindow(window_name,0,0)
    cv2.imshow(window_name,cv2.imread(path_name,cv2.IMREAD_COLOR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

sys.exit()

for img in imgs:
    img_gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    img_blur=cv2.blur(img_gray,(5,5))

    med_val = np.median(img_blur)
    sigma = 0.33  # 0.33
    min_val = int(max(0, (1.0 - sigma) * med_val))
    max_val = int(max(255, (1.0 + sigma) * med_val))

    cv2.imshow("test",cv2.Canny(img_gray,threshold1=min_val,threshold2=min_val))
    cv2.waitKey(0)
    cv2.destroyAllWindows()