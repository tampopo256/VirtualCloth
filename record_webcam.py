import cv2
import sys

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

while cap.isOpened():
    ret,src=cap.read()

    if not(ret) or src is None:
        continue

    # srcに対してスーツを着せるなどの加工処理（試しに背景を緑色にしてみる）
    

    # 表示
    cv2.imshow(WINDOW_NAME,src)

    # 書き込み
    dst.write(src)

    # q キーが押されたら停止する
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# 後処理
cap.release()
dst.release()
cv2.destroyAllWindows()