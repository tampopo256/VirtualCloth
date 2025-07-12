import cv2
import mediapipe as mp
import numpy as np

# --- 定数 ---
CAMERA_INDEX = 1
SUIT_IMAGE_PATH = 'assets/suit.png'
SUIT_BASE_WIDTH = 500
# 肩の中心からスーツ画像の上辺までのオフセット率 (画像の高さに対する割合)
SUIT_VERTICAL_OFFSET_RATIO = 1 / 3.5

def overlay_png(background_img, foreground_img, pos):
    """
    背景画像にアルファチャンネル付きのPNG画像を重ねて表示する。
    pos: (x, y) - 重ねて表示する左上の座標
    """
    x, y = pos

    bg_h, bg_w, _ = background_img.shape
    fg_h, fg_w, _ = foreground_img.shape

    if x >= bg_w or y >= bg_h or x + fg_w <= 0 or y + fg_h <= 0:
        return

    roi_y1 = max(0, y)
    roi_y2 = min(bg_h, y + fg_h)
    roi_x1 = max(0, x)
    roi_x2 = min(bg_w, x + fg_w)

    fg_roi_y1 = max(0, -y)
    fg_roi_y2 = fg_roi_y1 + (roi_y2 - roi_y1)
    fg_roi_x1 = max(0, -x)
    fg_roi_x2 = fg_roi_x1 + (roi_x2 - roi_x1)
    
    roi = background_img[roi_y1:roi_y2, roi_x1:roi_x2]
    fg_roi = foreground_img[fg_roi_y1:fg_roi_y2, fg_roi_x1:fg_roi_x2]
    
    if roi.size == 0 or fg_roi.size == 0:
        return

    fg_rgb = fg_roi[:, :, :3]
    alpha = np.expand_dims(fg_roi[:, :, 3] / 255.0, axis=2)

    blended_roi = (fg_rgb * alpha) + (roi * (1 - alpha))

    background_img[roi_y1:roi_y2, roi_x1:roi_x2] = blended_roi.astype(np.uint8)


def draw_suit(frame, landmarks, suit_image, mp_pose):
    """
    検出されたポーズに合わせて、フレームにスーツを描画する
    """
    if not landmarks:
        return

    h, w, _ = frame.shape

    # 1. 両肩の座標を取得
    left_shoulder = landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

    # 肩が両方とも検出できた場合のみ処理
    if not (left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5):
        return

    # 2. 肩の中心座標を計算
    lx, ly = int(left_shoulder.x * w), int(left_shoulder.y * h)
    rx, ry = int(right_shoulder.x * w), int(right_shoulder.y * h)
    shoulder_center_x = (lx + rx) // 2
    shoulder_center_y = (ly + ry) // 2

    # 3. スーツ画像を重ねる位置を計算
    suit_h, suit_w, _ = suit_image.shape
    pos_x = shoulder_center_x - (suit_w // 2)
    pos_y = shoulder_center_y - int(suit_h * SUIT_VERTICAL_OFFSET_RATIO)

    # 4. スーツ画像をフレームに重ねる
    overlay_png(frame, suit_image, (pos_x, pos_y))


def main():
    # MediaPipe Poseの初期化
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    # スーツの画像を読み込み、リサイズ
    suit_img = cv2.imread(SUIT_IMAGE_PATH, cv2.IMREAD_UNCHANGED)
    if suit_img is None:
        print(f"エラー: {SUIT_IMAGE_PATH} が見つかりません。")
        return
    
    suit_aspect_ratio = suit_img.shape[0] / suit_img.shape[1]
    resized_suit_h = int(SUIT_BASE_WIDTH * suit_aspect_ratio)
    resized_suit = cv2.resize(suit_img, (SUIT_BASE_WIDTH, resized_suit_h))

    # カメラを起動
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("エラー: フレームを読み取れませんでした。")
            break

        frame = cv2.flip(frame, 1)

        frame.flags.writeable = False
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        frame.flags.writeable = True

        # スーツを描画
        draw_suit(frame, results.pose_landmarks, resized_suit, mp_pose)

        # 骨格の描画はコメントアウト中
        # if results.pose_landmarks:
        #     mp_drawing.draw_landmarks(
        #         frame,
        #         results.pose_landmarks,
        #         mp_pose.POSE_CONNECTIONS)

        cv2.imshow("Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # リソースを解放
    pose.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()