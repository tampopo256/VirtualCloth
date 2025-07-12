import cv2
import mediapipe as mp
import numpy as np
import math

CAMERA_INDEX = 1
SUIT_IMAGE_PATH = 'assets/body_suit.png'
SUIT_SHOULDER_WIDTH_RATIO = 0.8 # 画像内の肩幅の比率 (胴体画像の場合、1.0に近い値で肩にフィット)
SUIT_SHOULDER_LINE_RATIO = 0.1 # 回転中心のY座標の比率 (画像の上辺から何%の位置を回転中心にするか)
SUIT_UPWARD_SHIFT_RATIO = 0.15 # 画像を上方向にシフトさせるオフセット率 (大きいほど上に移動)
ROTATION_MARGIN_RATIO = 1.4 # 回転時に画像がはみ出さないように確保する余白の比率

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
    """検出されたポーズに合わせて、フレームにスーツを描画する"""
    if not landmarks:
        return

    frame_height, frame_width, _ = frame.shape

    # 1. 両肩の座標を取得
    left_shoulder = landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

    if not (left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5):
        return

    # 2. 肩のピクセル座標と中心、幅を計算
    left_shoulder_x = int(left_shoulder.x * frame_width)
    left_shoulder_y = int(left_shoulder.y * frame_height)
    right_shoulder_x = int(right_shoulder.x * frame_width)
    right_shoulder_y = int(right_shoulder.y * frame_height)

    shoulder_center_x = (left_shoulder_x + right_shoulder_x) // 2
    shoulder_center_y = (left_shoulder_y + right_shoulder_y) // 2
    detected_shoulder_width = abs(right_shoulder_x - left_shoulder_x)

    # 3. スーツ画像のサイズを肩幅に合わせてスケーリング
    original_suit_height, original_suit_width, _ = suit_image.shape
    assumed_suit_shoulder_width = original_suit_width * SUIT_SHOULDER_WIDTH_RATIO
    scale = detected_shoulder_width / assumed_suit_shoulder_width if assumed_suit_shoulder_width > 0 else 1.0
    
    new_suit_width = int(original_suit_width * scale)
    new_suit_height = int(original_suit_height * scale)
    if new_suit_width <= 0 or new_suit_height <= 0:
        return
    scaled_suit = cv2.resize(suit_image, (new_suit_width, new_suit_height))

    # 4. スーツ画像を肩の傾きに合わせて回転
    # 鏡像（左右反転した映像）に合わせて角度を計算
    angle = math.atan2(left_shoulder_y - right_shoulder_y, left_shoulder_x - right_shoulder_x) * (180 / math.pi)
    
    rotation_center = (new_suit_width // 2, int(new_suit_height * SUIT_SHOULDER_LINE_RATIO))
    
    rotated_canvas_width = int(new_suit_width * ROTATION_MARGIN_RATIO)
    rotated_canvas_height = int(new_suit_height * ROTATION_MARGIN_RATIO)

    rotation_matrix = cv2.getRotationMatrix2D(rotation_center, angle, 1.0)
    rotation_matrix[0, 2] += (rotated_canvas_width / 2) - rotation_center[0]
    rotation_matrix[1, 2] += (rotated_canvas_height / 2) - rotation_center[1]

    rotated_suit = cv2.warpAffine(scaled_suit, rotation_matrix, (rotated_canvas_width, rotated_canvas_height),
                                  flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    # 鏡像映像で正しく見えるように、最終的な画像を左右反転して向きを修正
    rotated_suit = cv2.flip(rotated_suit, 1)

    # 5. スーツ画像を重ねる最終位置を計算
    pos_x = shoulder_center_x - (rotated_canvas_width // 2)
    # 肩の中心を基準に、回転中心のずれと上下シフトを考慮してY座標を決定
    upward_shift = int(new_suit_height * SUIT_UPWARD_SHIFT_RATIO)
    pos_y = shoulder_center_y - (rotated_canvas_height // 2) - upward_shift

    # 6. スーツ画像をフレームに重ねる
    overlay_png(frame, rotated_suit, (pos_x, pos_y))


def main():
    # MediaPipe Poseの初期化
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

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

        # スーツを描画
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