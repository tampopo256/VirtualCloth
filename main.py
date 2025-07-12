import cv2

def main():
    # PCに接続されているデフォルトのカメラを起動する
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

        # フレームを左右に反転させる (1: 左右反転, 0: 上下反転)
        frame = cv2.flip(frame, 1)

        # "Camera Feed"という名前のウィンドウにフレームを表示する
        cv2.imshow("Camera Feed", frame)

        # 'q'キーが押されたらループを抜ける
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # カメラとウィンドウを解放する
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()