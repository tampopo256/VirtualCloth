import cv2
import mediapipe as mp
import numpy as np

# --- 定数 ---
CAMERA_INDEX = 1
SUIT_IMAGE_PATH = 'assets/suit.png'
# スーツ画像内の肩幅を画像幅に対する比率で仮定 (この値を調整して横幅のフィット感を変えられます)
SUIT_SHOULDER_WIDTH_RATIO = 0.3
# 肩の中心からスーツ画像の上辺までのオフセット率 (この値を調整して縦位置を変えられます。小さくすると下に移動)
SUIT_VERTICAL_OFFSET_RATIO = 1 / 4.0

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

    height, width, _ = frame.shape

    # 両肩の座標を取得
    left_shoulder = landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

    if not (left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5):
        return

    # 肩の中心座標と肩幅を計算
    left_x, left_y = int(left_shoulder.x * width), int(left_shoulder.y * height)
    right_x, right_y = int(right_shoulder.x * width), int(right_shoulder.y * height)
    shoulder_center_x = (left_x + right_x) // 2
    shoulder_center_y = (left_y + right_y) // 2
    detected_shoulder_width = abs(right_x - left_x)

    # スーツ画像のスケーリング
    original_suit_height, original_suit_width, _ = suit_image.shape  # 変数名を明確に
    assumed_suit_shoulder_width = original_suit_width * SUIT_SHOULDER_WIDTH_RATIO
    scale = detected_shoulder_width / assumed_suit_shoulder_width if assumed_suit_shoulder_width > 0 else 1.0
    new_suit_width = int(original_suit_width * scale)
    new_suit_height = int(original_suit_height * scale)
    if new_suit_width <= 0 or new_suit_height <= 0:
        return
    scaled_suit = cv2.resize(suit_image, (new_suit_width, new_suit_height))

    # スーツ画像を重ねる位置を計算
    suit_height, suit_width, _ = scaled_suit.shape  # 変数名を明確に
    pos_x = shoulder_center_x - (suit_width // 2)
    pos_y = shoulder_center_y - int(suit_height * SUIT_VERTICAL_OFFSET_RATIO)

    # スーツ画像をフレームに重ねる
    overlay_png(frame, scaled_suit, (pos_x, pos_y))


def main():
    # MediaPipe Poseの初期化
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    # スーツの画像を読み込み
    suit_img = cv2.imread(SUIT_IMAGE_PATH, cv2.IMREAD_UNCHANGED)
    if suit_img is None:
        print(f"エラー: {SUIT_IMAGE_PATH} が見つかりません。")
        return

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

        # スーツを描画 (suit_img を渡すように変更)
        draw_suit(frame, results.pose_landmarks, suit_img, mp_pose)

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