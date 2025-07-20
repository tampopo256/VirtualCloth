import cv2
import mediapipe as mp
import numpy as np
import math
import pyvirtualcam
import numpy.typing as npt
import threading

class Config:
    """設定値を管理するクラス"""
    CAMERA_INDEX = 1
    SHIRT_ASSETS_PATH = 'assets/shirt'
    SUIT_ASSETS_PATH = 'assets/suit'

    # 描画パラメータ
    SUIT_SHOULDER_WIDTH_RATIO = 0.8  # 画像内の肩幅の比率 (1.0に近い値で肩にフィット)
    SUIT_SHOULDER_LINE_RATIO = 0.1  # 回転中心のY座標の比率 (画像の上辺から何%の位置か)
    SUIT_UPWARD_SHIFT_RATIO = 0.15 # 画像を上方向にシフトさせるオフセット率 (大きいほど上に移動)
    ROTATION_MARGIN_RATIO = 1.4  # 回転時に画像がはみ出さないように確保する余白の比率
    UPPER_ARM_SCALE_FACTOR = 1.5  # 上腕画像の拡大率
    FOREARM_SCALE_FACTOR = 1.2  # 前腕画像の拡大率
    FULLBODY_SCALE_FACTOR = 1.3 # fullbody画像の拡大率
    MIN_VISIBILITY_THRESHOLD = 0.5 # 関節の信頼度スコアの閾値(どれくらいはっきり検出できるか)
    # 腕の描画に関するパラメータ
    LIMB_DEFAULT_LENGTH_SHOULDER_WIDTH_RATIO = 1.2 # 肩幅に対する腕のデフォルト長の比率
    LIMB_INVISIBLE_OFFSET_X = 50 # 関節が見えない場合に腕を外側に描画するためのオフセット
    UPPER_ARM_ROTATION_CENTER_Y_RATIO = 0.1 # 上腕の回転中心のY座標比率
    LIMB_FALLBACK_DEFAULT_LENGTH_DENOMINATOR = 5 # 肩が検出できない場合の腕の長さ (身長に対する分母)

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

    def _rotate_image(self, image, angle, rotation_center, margin_ratio, use_hypot_for_canvas=False):
        """画像を回転させ、はみ出さないようにキャンバスを調整する"""
        h, w = image.shape[:2]
        
        if use_hypot_for_canvas:
            canvas_dim = int(math.hypot(w, h) * margin_ratio)
            canvas_width, canvas_height = canvas_dim, canvas_dim
        else:
            canvas_width = int(w * margin_ratio)
            canvas_height = int(h * margin_ratio)
            
        rotation_matrix = cv2.getRotationMatrix2D(rotation_center, angle, 1.0)
        # 回転中心をキャンバスの中心に合わせる補正
        rotation_matrix[0, 2] += (canvas_width / 2) - rotation_center[0]
        rotation_matrix[1, 2] += (canvas_height / 2) - rotation_center[1]

        rotated_image = cv2.warpAffine(image, rotation_matrix, (canvas_width, canvas_height),
                                       flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        return rotated_image

    def draw_torso(self, frame, landmarks, body_image, scale_factor=1.0):
        """検出されたポーズに合わせて、フレームに胴体を描画する"""
        if not landmarks:
            return
        
        # 1. 両肩の座標を取得
        frame_height, frame_width, _ = frame.shape
        left_shoulder_lm = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder_lm = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        if not (left_shoulder_lm.visibility > Config.MIN_VISIBILITY_THRESHOLD and right_shoulder_lm.visibility > Config.MIN_VISIBILITY_THRESHOLD):
            return

        # 2. 肩のピクセル座標と中心、幅、傾きを計算
        left_shoulder_x, left_shoulder_y = int(left_shoulder_lm.x * frame_width), int(left_shoulder_lm.y * frame_height)
        right_shoulder_x, right_shoulder_y = int(right_shoulder_lm.x * frame_width), int(right_shoulder_lm.y * frame_height)

        shoulder_center_x = (left_shoulder_x + right_shoulder_x) // 2
        shoulder_center_y = (left_shoulder_y + right_shoulder_y) // 2
        detected_shoulder_width = abs(right_shoulder_x - left_shoulder_x)
        angle = math.degrees(math.atan2(left_shoulder_y - right_shoulder_y, left_shoulder_x - right_shoulder_x))

        # 3. ボディ画像のサイズを肩幅に合わせてスケーリング
        original_suit_height, original_suit_width, _ = body_image.shape
        assumed_suit_shoulder_width = original_suit_width * Config.SUIT_SHOULDER_WIDTH_RATIO
        scale = detected_shoulder_width / assumed_suit_shoulder_width if assumed_suit_shoulder_width > 0 else 1.0
        scale *= scale_factor
        
        new_suit_width = int(original_suit_width * scale)
        new_suit_height = int(original_suit_height * scale)
        if new_suit_width <= 0 or new_suit_height <= 0:
            return
        scaled_suit = cv2.resize(body_image, (new_suit_width, new_suit_height))

        # 4. ボディ画像を肩の傾きに合わせて回転
        rotation_center = (new_suit_width // 2, int(new_suit_height * Config.SUIT_SHOULDER_LINE_RATIO))
        rotated_suit = self._rotate_image(scaled_suit, angle, rotation_center, Config.ROTATION_MARGIN_RATIO)
        
        # カメラ映像は鏡像なので、それに合わせて画像を左右反転
        rotated_suit = cv2.flip(rotated_suit, 1)

        # 5. ボディ画像を重ねる最終位置を計算
        rotated_canvas_height, rotated_canvas_width, _ = rotated_suit.shape
        pos_x = shoulder_center_x - (rotated_canvas_width // 2)
        upward_shift = int(new_suit_height * Config.SUIT_UPWARD_SHIFT_RATIO)
        pos_y = shoulder_center_y - (rotated_canvas_height // 2) - upward_shift
        self._overlay_png(frame, rotated_suit, (pos_x, pos_y))

    def _estimate_invisible_limb_endpoint(self, landmarks, start_joint, start_x, start_y, frame_width, frame_height):
        """検出できない手足の末端座標を推定する"""
        # 肩幅を計算して最低の腕長さを設定
        left_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        if left_shoulder.visibility > Config.MIN_VISIBILITY_THRESHOLD and right_shoulder.visibility > Config.MIN_VISIBILITY_THRESHOLD:
            left_shoulder_x = int(left_shoulder.x * frame_width)
            right_shoulder_x = int(right_shoulder.x * frame_width)
            detected_shoulder_width = abs(right_shoulder_x - left_shoulder_x)
            default_length = int(detected_shoulder_width * Config.LIMB_DEFAULT_LENGTH_SHOULDER_WIDTH_RATIO)
        else:
            default_length = frame_height // Config.LIMB_FALLBACK_DEFAULT_LENGTH_DENOMINATOR  # 肩が検出できない場合のフォールバック

        is_left_side = start_joint in [self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.LEFT_ELBOW]
        offset_x = Config.LIMB_INVISIBLE_OFFSET_X
        end_x = start_x + offset_x if is_left_side else start_x - offset_x
        end_y = start_y + default_length
        return end_x, end_y

    def draw_limb(self, frame, landmarks, start_joint, end_joint, limb_image, scale_factor=1.0):
        """検出されたポーズの特定の部位（手足など）に合わせて画像を描画する"""
        if not landmarks:
            return
        
        # 1. 関節の座標を取得
        frame_height, frame_width, _ = frame.shape
        start_lm = landmarks.landmark[start_joint]
        end_lm = landmarks.landmark[end_joint]
        
        if start_lm.visibility <= Config.MIN_VISIBILITY_THRESHOLD:
            return  # 開始点が検出できない場合はスキップ

        # 2. 関節のピクセル座標と中心、長さを計算
        start_x, start_y = int(start_lm.x * frame_width), int(start_lm.y * frame_height)
        
        if end_lm.visibility > Config.MIN_VISIBILITY_THRESHOLD:
            end_x, end_y = int(end_lm.x * frame_width), int(end_lm.y * frame_height)
        else:
            end_x, end_y = self._estimate_invisible_limb_endpoint(landmarks, start_joint, start_x, start_y, frame_width, frame_height)
        
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
        angle = math.degrees(math.atan2(end_y - start_y, end_x - start_x)) - 90
        
        is_upper_arm = start_joint in [self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        if is_upper_arm:
            # 上腕の場合、回転センターを上端近くに調整（トリミング考慮）
            rotation_center = (new_limb_width // 2, int(new_limb_height * Config.UPPER_ARM_ROTATION_CENTER_Y_RATIO))
        else:
            rotation_center = (new_limb_width // 2, new_limb_height // 2)

        rotated_limb = self._rotate_image(scaled_limb, angle, rotation_center, Config.ROTATION_MARGIN_RATIO, use_hypot_for_canvas=True)
        
        # カメラ映像は鏡像なので、それに合わせて画像を左右反転
        rotated_limb = cv2.flip(rotated_limb, 1)
        
        # 5. 画像を重ねる最終位置を計算
        rotated_canvas_height, rotated_canvas_width, _ = rotated_limb.shape
        if is_upper_arm:
            # 上腕の場合、回転中心（画像上端付近）を肩の位置に合わせる
            target_x, target_y = start_x, start_y
        else:
            # 前腕の場合、回転中心（画像中心）を肘と手首の中点に合わせる
            target_x, target_y = center_x, center_y

        pos_x = target_x - (rotated_canvas_width // 2)
        pos_y = target_y - (rotated_canvas_height // 2)
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
        self.images = self._load_all_assets()
        self.selected_cloth = 'shirt' # デフォルトの衣装
        self.ret,self.frame=self.cap.read()
        self.stopped=False
        # 定数
        self.cloth_state=False

        # スレッドの初期化と開始
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True # メインスレッドが終了したら、このスレッドも終了する
        self.thread.start()
        print(f"VideoStream thread for camera='{self.config.CAMERA_INDEX}' started.")
    
    def read(self)->npt.NDArray:
        return self.frame
    
    def stop(self):
        self.stopped=True
        self.thread.join()
        self._cleanup()

    def _load_all_assets(self):
        """すべての衣装アセットを読み込む"""
        assets = {
            'shirt': self.config.SHIRT_ASSETS_PATH,
            'suit': self.config.SUIT_ASSETS_PATH,
        }
        
        all_images = {}
        for cloth_name, path in assets.items():
            all_images[cloth_name] = self._load_images_from_path(path)
            
        return all_images

    def _load_images_from_path(self, path):
        """指定されたパスから衣装画像を読み込む"""
        image_names = {
            "fullbody": "0.png",
            "torso": "1.png",
            "upper_arm": "2.png",
            "forearm": "3.png",
        }
        
        loaded_images = {}
        for name, filename in image_names.items():
            image_path = f"{path}/{filename}"
            img = self._load_rgba_image(image_path)
            if img is None:
                raise IOError(f"画像の読み込みに失敗しました: {image_path}")
            
            loaded_images[name] = img
            # 腕のパーツは左右反転したバージョンも用意する
            if name in ["upper_arm", "forearm"]:
                loaded_images[f"flipped_{name}"] = cv2.flip(img, 1)

        return loaded_images


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

        while not self.stopped:
            ret, frame = self.cap.read()
            if not(ret) or frame is None:
                print("エラー: フレームを読み取れませんでした。")
                break

            results = self._process_frame(frame)
            if self.cloth_state:
                self._draw_all(frame, results)

            # 最新フレーム更新
            self.frame=frame

            # 仮想カメラ処理

        self.cap.release()

    def _process_frame(self, frame):
        """フレームを処理してポーズを検出する"""
        # パフォーマンス向上のため、画像を書き込み不可として参照渡しする
        frame.flags.writeable = False
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        frame.flags.writeable = True
        return results

    def _are_arms_visible(self, landmarks):
        """両腕が検出できているかを判定する"""
        left_elbow = landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
        return left_elbow.visibility > Config.MIN_VISIBILITY_THRESHOLD and right_elbow.visibility > Config.MIN_VISIBILITY_THRESHOLD

    def _draw_separate_body_parts(self, frame, landmarks):
        """腕と胴体を個別のパーツとして描画する"""
        cloth_images = self.images[self.selected_cloth]
        
        # 描画順序: 奥側(末端)から手前(中心)へ描画することで、正しい重なり順にする
        # 1. 前腕
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.LEFT_ELBOW, self.mp_pose.PoseLandmark.LEFT_WRIST, cloth_images["forearm"], scale_factor=self.config.FOREARM_SCALE_FACTOR)
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.RIGHT_ELBOW, self.mp_pose.PoseLandmark.RIGHT_WRIST, cloth_images["flipped_forearm"], scale_factor=self.config.FOREARM_SCALE_FACTOR)

        # 2. 上腕
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.LEFT_SHOULDER, self.mp_pose.PoseLandmark.LEFT_ELBOW, cloth_images["upper_arm"], scale_factor=self.config.UPPER_ARM_SCALE_FACTOR)
        self.drawer.draw_limb(frame, landmarks, self.mp_pose.PoseLandmark.RIGHT_SHOULDER, self.mp_pose.PoseLandmark.RIGHT_ELBOW, cloth_images["flipped_upper_arm"], scale_factor=self.config.UPPER_ARM_SCALE_FACTOR)
        
        # 3. 胴体
        self.drawer.draw_torso(frame, landmarks, cloth_images["torso"])

    def _draw_composite_body(self, frame, landmarks):
        """腕を組んだ合成画像を描画する"""
        cloth_images = self.images[self.selected_cloth]
        self.drawer.draw_torso(frame, landmarks, cloth_images["fullbody"], scale_factor=self.config.FULLBODY_SCALE_FACTOR)

    def _draw_all(self, frame, results):
        """すべてのパーツを描画する"""
        if not results.pose_landmarks:
            return
        
        landmarks = results.pose_landmarks
        
        if self._are_arms_visible(landmarks):
            self._draw_separate_body_parts(frame, landmarks)
        else:
            self._draw_composite_body(frame, landmarks)

    def changeCloth(self, cloth_name):
        """試着する衣装を切り替える"""
        if cloth_name in self.images:
            self.selected_cloth = cloth_name
            print(f"衣装を {cloth_name} に切り替えました。")
        else:
            print(f"エラー: 衣装 '{cloth_name}' が見つかりません。利用可能な衣装: {list(self.images.keys())}")
    
    def switchDrawingCloth(self):
        '''服装の表示状態を反転させる'''
        self.cloth_state=not(self.cloth_state)

    def _cleanup(self):
        """リソースを解放する"""
        self.pose.close()
        self.cap.release()
        cv2.destroyAllWindows()

# if __name__ == "__main__":
#     try:
#         app = VirtualTryOnApp()
#         app.run()
#     except (IOError, cv2.error) as e:
#         # 画像の読み込み失敗やカメラ関連のエラーを捕捉
#         print(f"アプリケーションの実行中にエラーが発生しました: {e}")