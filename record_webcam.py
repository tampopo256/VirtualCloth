import cv2
import sys

# 定数定義
IMG_HEIGHT=int(256)
IMG_WIDTH=int(512)
FOURCC=cv2.VideoWriter_fourcc(*"MP4V")
FPS=float(30.0)
VIDEO_NAME="./test.mp4"

# 前処理
## 内臓カメラ起動
cap=cv2.VideoCapture(0)

if not cap.isOpened():
    print("キャプチャできませんでした。")    
    sys.exit()

dst=cv2.VideoWriter(VIDEO_NAME,FOURCC,FPS,(IMG_WIDTH,IMG_HEIGHT),isColor=True)

while cap.isOpened():
    ret,src=cap.read()

    # srcに対してスーツを着せるなどの加工処理

    # 書き込み
    dst.write(src)
    cv2.imshow(src)

# 後処理
cap.release()
dst.release()
cv2.destroyAllWindows()