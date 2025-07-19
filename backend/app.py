import cv2
import mediapipe as mp
import numpy as np
import math
import pyvirtualcam

class Config:
    """設定値を管理するクラス"""
    CAMERA_INDEX = 0
    TORSO_IMAGE_PATH = 'assets/torso.png'
    UPPER_ARM_IMAGE_PATH = 'assets/upper_arm.png'
    FOREARM_IMAGE_PATH = 'assets/forearm.png'
    # 描画パラメータ
    SUIT_SHOULDER_WIDTH_RATIO = 0.8  # 画像内の肩幅の比率 (1.0に近い値で肩にフィット)
    SUIT_SHOULDER_LINE_RATIO = 0.1  # 回転中心のY座標の比率 (画像の上辺から何%の位置か)
    SUIT_UPWARD_SHIFT_RATIO = 0.15  # 画像を上方向にシフトさせるオフセット率 (大きいほど上に移動)
    ROTATION_MARGIN_RATIO = 1.4  # 回転時に画像がはみ出さないように確保する余白の比率
    UPPER_ARM_SCALE_FACTOR = 1.5  # 上腕画像の拡大率
    FOREARM_SCALE_FACTOR = 1.2  # 前腕画像の拡大率

class BodyPartDrawer:
    """身体パーツの描画を担当するクラス"""

    def __init__(self):
        """初期化"""
        self.mp_pose = mp.solutions.pose

    def _overlay_png(self, background_img, foreground_img, pos):
        """
        背景画像にアルファチャンネル付きのPNG画像を重ねて表示する。
        pos: (x, y) - 重ねて表示する左上の座標
        """
        x, y = pos
        bg_h, bg_w, _ = background_img.shape
        fg_h, fg_w, _ = foreground_img.shape

        # 画面外なら処理しない
        if x >= bg_w or y >= bg_h or x + fg_w <= 0 or y + fg_h <= 0:
            return

        # 重ね合わせる領域を計算
        roi_y1, roi_y2 = max(0, y), min(bg_h, y + fg_h)
        roi_x1, roi_x2 = max(0, x), min(bg_w, x + fg_w)
        fg_roi_y1, fg_roi_y2 = max(0, -y), max(0, -y) + (roi_y2 - roi_y1)
        fg_roi_x1, fg_roi_x2 = max(0, -x), max(0, -x) + (roi_x2 - roi_x1)
        
        roi = background_img[roi_y1:roi_y2, roi_x1:roi_x2]
        fg_roi = foreground_img[fg_roi_y1:fg_roi_y2, fg_roi_x1:fg_roi_x2]
        
        if roi.size == 0 or fg_roi.size == 0:
            return

        # アルファブレンディング
        fg_rgb = fg_roi[:, :, :3]
        alpha = np.expand_dims(fg_roi[:, :, 3] / 255.0, axis=2)
        blended_roi = (fg_rgb * alpha) + (roi * (1 - alpha))
        background_img[roi_y1:roi_y2, roi_x1:roi_x2] = blended_roi.astype(np.uint8)

    def draw_torso(self, frame, landmarks, suit_image):
        """検出されたポーズに合わせて、フレームに胴体を描画する"""
        if not landmarks:
            return
        
        # 1. 両肩の座標を取得
        frame_height, frame_width, _ = frame.shape
        left_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

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
        assumed_suit_shoulder_width = original_suit_width * Config.SUIT_SHOULDER_WIDTH_RATIO
        scale = detected_shoulder_width / assumed_suit_shoulder_width if assumed_suit_shoulder_width > 0 else 1.0
        
        new_suit_width = int(original_suit_width * scale)
        new_suit_height = int(original_suit_height * scale)
        if new_suit_width <= 0 or new_suit_height <= 0:
            return
        scaled_suit = cv2.resize(suit_image, (new_suit_width, new_suit_height))

        # 4. スーツ画像を肩の傾きに合わせて回転
        angle = math.atan2(left_shoulder_y - right_shoulder_y, left_shoulder_x - right_shoulder_x) * (180 / math.pi)
        rotation_center = (new_suit_width // 2, int(new_suit_height * Config.SUIT_SHOULDER_LINE_RATIO))
        
        # 回転後の画像が収まるようにキャンバスサイズを計算
        rotated_canvas_width = int(new_suit_width * Config.ROTATION_MARGIN_RATIO)
        rotated_canvas_height = int(new_suit_height * Config.ROTATION_MARGIN_RATIO)

        # 回転行列を計算し、画像の中心がずれないように補正
        rotation_matrix = cv2.getRotationMatrix2D(rotation_center, angle, 1.0)
        rotation_matrix[0, 2] += (rotated_canvas_width / 2) - rotation_center[0]
        rotation_matrix[1, 2] += (rotated_canvas_height / 2) - rotation_center[1]

        rotated_suit = cv2.warpAffine(scaled_suit, rotation_matrix, (rotated_canvas_width, rotated_canvas_height),
                                      flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        
        # カメラ映像は鏡像なので、それに合わせて画像を左右反転
        rotated_suit = cv2.flip(rotated_suit, 1)

        # 5. スーツ画像を重ねる最終位置を計算
        pos_x = shoulder_center_x - (rotated_canvas_width // 2)
        upward_shift = int(new_suit_height * Config.SUIT_UPWARD_SHIFT_RATIO)
        pos_y = shoulder_center_y - (rotated_canvas_height // 2) - upward_shift
        self._overlay_png(frame, rotated_suit, (pos_x, pos_y))

    def draw_limb(self, frame, landmarks, start_joint, end_joint, limb_image, scale_factor=1.0):
        """検出されたポーズの特定の部位（手足など）に合わせて画像を描画する"""
        if not landmarks:
            return
        
        # 1. 関節の座標を取得
        frame_height, frame_width, _ = frame.shape
        start_lm = landmarks.landmark[start_joint]
        end_lm = landmarks.landmark[end_joint]

        if not (start_lm.visibility > 0.5 and end_lm.visibility > 0.5):
            return

        # 2. 関節のピクセル座標と中心、長さを計算
        start_x, start_y = int(start_lm.x * frame_width), int(start_lm.y * frame_height)
        end_x, end_y = int(end_lm.x * frame_width), int(end_lm.y * frame_height)
        center_x, center_y = (start_x + end_x) // 2, (start_y + end_y) // 2
        
        limb_length = math.hypot(end_x - start_x, end_y - start_y)
        if limb_length < 1:
            return

        # 3. 画像のサイズを部位の長さに合わせてスケーリング
        original_limb_height, original_limb_width, _ = limb_image.shape
        scale = (limb_length / original_limb_height if original_limb_height > 0 else 1.0) * scale_factor
        new_limb_width, new_limb_height = int(original_limb_width * scale), int(original_limb_height * scale)

        if new_limb_width <= 0 or new_limb_height <= 0:
            return
        scaled_limb = cv2.resize(limb_image, (new_limb_width, new_limb_height))

        # 4. 画像を部位の傾きに合わせて回転
        # 縦向きの画像を関節の角度に合わせるため、-90度のオフセットを追加
        angle = math.atan2(end_y - start_y, end_x - start_x) * (180 / math.pi) - 90
        rotation_center = (new_limb_width // 2, new_limb_height // 2)
        
        # 回転後の画像が収まるようにキャンバスサイズを計算
        rotated_canvas_width = int(math.hypot(new_limb_width, new_limb_height) * Config.ROTATION_MARGIN_RATIO)
        rotated_canvas_height = rotated_canvas_width

        # 回転行列を計算し、画像の中心がずれないように補正
        rotation_matrix = cv2.getRotationMatrix2D(rotation_center, angle, 1.0)
        rotation_matrix[0, 2] += (rotated_canvas_width / 2) - rotation_center[0]
        rotation_matrix[1, 2] += (rotated_canvas_height / 2) - rotation_center[1]

        rotated_limb = cv2.warpAffine(scaled_limb, rotation_matrix, (rotated_canvas_width, rotated_canvas_height),
                                      flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        
        # カメラ映像は鏡像なので、それに合わせて画像を左右反転
        rotated_limb = cv2.flip(rotated_limb, 1)
        
        # 5. 画像を重ねる最終位置を計算
        pos_x, pos_y = center_x - (rotated_canvas_width // 2), center_y - (rotated_canvas_height // 2)
        self._overlay_png(frame, rotated_limb, (pos_x, pos_y))


class VirtualTryOnApp:
    """バーチャル試着アプリケーション"""
    
    def __init__(self):
        """アプリケーションの初期化"""
        self.config = Config()
        self.drawer = BodyPartDrawer()
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
        self.images = self._load_images()

    def _load_images(self):
        """試着用の画像を読み込む"""
        images = {}
        paths = {
            "torso": self.config.TORSO_IMAGE_PATH,
            "upper_arm": self.config.UPPER_ARM_IMAGE_PATH,
            "forearm": self.config.FOREARM_IMAGE_PATH,
        }
        for name, path in paths.items():
            img = self._load_rgba_image(path)
            if img is None:
                raise IOError(f"画像の読み込みに失敗しました: {path}")
            images[name] = img
            # 腕パーツの場合は、左右反転させた画像も用意しておく
            if 'arm' in name:
                images[f"flipped_{name}"] = cv2.flip(img, 1)
        return images

    def _load_rgba_image(self, path):
        """アルファチャンネル付きの画像を読み込む。なければエラーを出力する。"""
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"エラー: {path} が見つかりません。")
            return None
        if len(img.shape) < 3 or img.shape[2] != 4:
            print(f"エラー: {path} にはアルファチャンネル（透過情報）がありません。透過PNGで保存してください。")
            return None
        return img

    def run(self):
        """アプリケーションのメインループを実行する"""
        if not self.cap.isOpened():
            print("エラー: カメラを開けませんでした。")
            return

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("エラー: フレームを読み取れませんでした。")
                break

            # カメラ映像を左右反転して鏡のように見せる
            frame = cv2.flip(frame, 1)
            results = self._process_frame(frame)
            self._draw_all(frame, results)

            cv2.imshow("Virtual Try-On", frame)

            # 'q'キーで終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self._cleanup()

    def _process_frame(self, frame):
        """フレームを処理してポーズを検出する"""
        frame.flags.writeable = False
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        frame.flags.writeable = True
        return results

    def _draw_all(self, frame, results):
        """すべてのパーツを描画する"""
        if not results.pose_landmarks:
            return
        
        landmarks = results.pose_landmarks
        
        # 描画順序: 奥側(末端)から手前(中心)へ描画する
        # 1. 前腕
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW, self.mp_pose.PoseLandmark.LEFT_WRIST, self.images["forearm"], scale_factor=self.config.FOREARM_SCALE_FACTOR)
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.RIGHT_ELBOW, self.mp_pose.PoseLandmark.RIGHT_WRIST, self.images["flipped_forearm"], scale_factor=self.config.FOREARM_SCALE_FACTOR)

        # 2. 上腕
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.LEFT_ELBOW, self.images["upper_arm"], scale_factor=self.config.UPPER_ARM_SCALE_FACTOR)
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.RIGHT_SHOULDER, self.mp_pose.PoseLandmark.RIGHT_ELBOW, self.images["flipped_upper_arm"], scale_factor=self.config.UPPER_ARM_SCALE_FACTOR)
        
        # 3. 胴体
        self.drawer.draw_torso(frame, landmarks, self.images["torso"])

    def _cleanup(self):
        """リソースを解放する"""
        self.pose.close()
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        app = VirtualTryOnApp()
        app.run()
    except (IOError, cv2.error) as e:
        # 画像の読み込み失敗やカメラ関連のエラーを捕捉
        print(f"アプリケーションの実行中にエラーが発生しました: {e}")