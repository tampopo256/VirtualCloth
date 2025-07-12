import cv2
import mediapipe as mp

def main():
    # MediaPipe Poseの初期化
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    # PCに接続されているカメラを起動する
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。")
        return

    while True:
        # カメラから1フレーム（1枚の画像）読み込む
        ret, frame = cap.read()

        if not ret:
            print("エラー: フレームを読み取れませんでした。")
            break

        # フレームを左右に反転させる
        frame = cv2.flip(frame, 1)

        # パフォーマンス向上のため、フレームを書き込み不可にする
        frame.flags.writeable = False
        # BGR画像をRGBに変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # ポーズを検出
        results = pose.process(rgb_frame)

        # フレームを書き込み可に戻す
        frame.flags.writeable = True

        # 検出されたポーズのランドマークを描画
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS)

        # "Camera Feed"という名前のウィンドウにフレームを表示する
        cv2.imshow("Camera Feed", frame)

        # 'q'キーが押されたらループを抜ける
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # カメラとウィンドウを解放する
    pose.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()