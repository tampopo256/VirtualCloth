import cv2
import numpy as np

# 顔検出用カスケード
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# 服画像の読み込み（RGBA: 透明背景のPNG）
clothing = cv2.imread("shirt.png", cv2.IMREAD_UNCHANGED)
if clothing is None:
    raise FileNotFoundError("shirt.png が見つかりません")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    if len(faces) > 0:
        # 一番大きな顔を使う
        (x, y, w, h) = max(faces, key=lambda rect: rect[2] * rect[3])

        # 📌 肩幅 ≒ 顔幅 * 2.2, 胴体長 ≒ 顔高さ * 2.5
        cloth_width = int(w * 2.2)
        cloth_height = int(h * 2.5)

        # 📌 服の位置：顔の下から開始（少し上にして首元に合わせる）
        cloth_x = x - int((cloth_width - w) / 2)
        cloth_y = y + h - int(h * 0.2)

        # 📌 服画像をリサイズ
        resized_cloth = cv2.resize(clothing, (cloth_width, cloth_height))
        ch, cw = resized_cloth.shape[:2]
        alpha = resized_cloth[:, :, 3] / 255.0

        # 📌 貼り付け領域（画面の外にはみ出ないよう補正）
        x1 = max(cloth_x, 0)
        y1 = max(cloth_y, 0)
        x2 = min(cloth_x + cw, frame.shape[1])
        y2 = min(cloth_y + ch, frame.shape[0])

        for c in range(3):
            frame[y1:y2, x1:x2, c] = (
                alpha[0:(y2 - y1), 0:(x2 - x1)] * resized_cloth[0:(y2 - y1), 0:(x2 - x1), c] +
                (1 - alpha[0:(y2 - y1), 0:(x2 - x1)]) * frame[y1:y2, x1:x2, c]
            )

    cv2.imshow("Clothing Fit Better", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
