import cv2
import sys
from library import fillInBackground

# 定数定義
IMG_HEIGHT=int(256)
IMG_WIDTH=int(512)
FOURCC=cv2.VideoWriter_fourcc(*"MP4V")
FPS=float(30.0)
VIDEO_NAME="./test.mp4"
WINDOW_NAME="Camera"

# 前処理
## 内臓カメラ起動
cap=cv2.VideoCapture(0)

if not cap.isOpened():
    print("キャプチャできませんでした。")    
    sys.exit()

dst=cv2.VideoWriter(VIDEO_NAME,FOURCC,FPS,(IMG_WIDTH,IMG_HEIGHT),isColor=True)

save_fig=None

while cap.isOpened():
    ret,src=cap.read()

    if not(ret) or src is None:
        continue
    save_fig=src

    # srcに対してスーツを着せるなどの加工処理（試しに背景を緑色にしてみる）
    src=fillInBackground(src,(0,255,0))

    # 表示
    cv2.imshow(WINDOW_NAME,src)
    cv2.moveWindow(WINDOW_NAME,0,0)

    # 書き込み
    dst.write(cv2.resize(src,(IMG_WIDTH,IMG_HEIGHT)))

    # q キーが押されたら停止する
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.imwrite("my_image.jpg",save_fig)

# 後処理
cap.release()
dst.release()
cv2.destroyAllWindows()