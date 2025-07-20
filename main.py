import sys
from PyQt6.QtWidgets import QApplication, QWidget, QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer
from backend.app import VirtualTryOnApp
import cv2
import threading

clothes = ["スーツ", "Tシャツ"]
clothes_name = ["suit", "shirt"]
current_cloth_idx = 0
processing_thread = None
stop_event = threading.Event()
latest_frame = None
frame_lock = threading.Lock()
app_backend = None

display_timer = QTimer()

camera_id = 0

def run_processing_thread(camera):
    global app_backend, latest_frame
    try:
        app_backend = VirtualTryOnApp(camera)
        app_backend.switchDrawingCloth  # ← 初期状態でスーツ非表示

        while not stop_event.is_set():
            frame = app_backend.read()
            if frame is not None:
                with frame_lock:
                    latest_frame = frame.copy()
    except Exception as e:
        print(f"映像処理中にエラーが発生しました: {e}")
    finally:
        if app_backend:
            app_backend.stop()
        print("映像処理スレッドを終了しました。")

def update_display_window():
    global latest_frame
    WINDOW_NAME = "Virtual Try-On"

    with frame_lock:
        frame_to_show = latest_frame

    if frame_to_show is not None:
        try:
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.imshow(WINDOW_NAME, frame_to_show)
            cv2.waitKey(1)
        except cv2.error:
            pass

def toggle_video(checked):
    if checked:
        button_cloth_on_off.setIcon(QIcon("front/img/suit.png"))
        button_cloth_on_off.setStyleSheet(base_style + button_clicked)
        label_show_status.setText("表示:ON")
        if app_backend:
            app_backend.switchDrawingCloth()
    else:
        button_cloth_on_off.setIcon(QIcon("front/img/unsuit.png"))
        button_cloth_on_off.setStyleSheet(base_style + button_unclicked)
        label_show_status.setText("表示:OFF")
        if app_backend:
            app_backend.switchDrawingCloth()

def create_button_label_set(button, label, label2):
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(button)
    layout.addWidget(label)
    layout.addWidget(label2)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return container

def change_cloth():
    global current_cloth_idx
    current_cloth_idx = (current_cloth_idx + 1) % len(clothes)
    label_cloth_status.setText(f"現在の服:{clothes[current_cloth_idx]}")
    app_backend.changeCloth(clothes_name[current_cloth_idx])

def start_processing():
    global processing_thread
    stop_event.clear()
    processing_thread = threading.Thread(target=run_processing_thread, args=(camera_id,), daemon=True)
    processing_thread.start()
    display_timer.start(33)

def change_camera_id():
    global camera_id, app_backend, processing_thread
    camera_id = (camera_id + 1) % 2
    camera_action.setText(f"カメラID : {camera_id}")
    stop_event.set()
    if processing_thread is not None:
        print("[INFO] 前のスレッド終了待機中...")
    try:
        processing_thread.join(timeout=3.0)
    except Exception as e:
        print(f"[ERROR] スレッド終了待ち中に例外: {e}")
    finally:
        processing_thread = None

    # 3. app_backend を安全に停止
    try:
        if app_backend:
            print("[INFO] app_backend.stop() を呼び出し中")
            app_backend.stop()
    except Exception as e:
        print(f"[WARN] stop() 実行中に例外: {e}")
    finally:
        app_backend = None

    # 4. OpenCV ウィンドウを安全に閉じる
    try:
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"[WARN] OpenCVウィンドウ終了で例外: {e}")

    # 5. 少し待つことでリソース競合を回避
    import time
    time.sleep(0.3)

    # 6. 新しいカメラで処理再開
    start_processing()

# GUI setup
guiapp = QApplication(sys.argv)
guiapp.setStyleSheet("""
    QLabel {
        color: black;
    }
""")
font = QFont("Meiryo", 14, QFont.Weight.Bold)
guiapp.setFont(font)
window = QWidget()
window.setWindowTitle("VirtualCloth")
window.setStyleSheet("background-color: white;")
window.setFixedSize(500, 500)

display_timer.timeout.connect(update_display_window)

# スーツON/OFFボタン
button_cloth_on_off = QToolButton()
button_cloth_on_off.toggled.connect(toggle_video)
button_cloth_on_off.setCheckable(True)
button_cloth_on_off.setIcon(QIcon("front/img/unsuit.png"))
button_cloth_on_off.setIconSize(QSize(150, 150))
base_style = """
    QToolButton {
        background-color: #1565d0;
        color: white;
        border-radius: 55px;
        border: 2px solid #388E3C;
        min-width: 150px;
        min-height: 150px;
        max-width: 150px;
        max-height: 150px;
    }
    QToolButton:checked {
        background-color: #FFA726;
    }
"""
button_clicked = """
    QToolButton:hover {
        background-color: #FFB74D;
    }
"""
button_unclicked = """
    QToolButton:hover {
        background-color: #2575f0;
    }
"""
button_cloth_on_off.setStyleSheet(base_style + button_unclicked)
label_cloth_on_off = QLabel("表示切替")
label_show_status = QLabel("表示:OFF")

# 衣装切り替えボタン
button_change_cloth = QToolButton()
button_change_cloth.clicked.connect(change_cloth)
button_change_cloth.setIcon(QIcon("front/img/change_cloth.png"))
button_change_cloth.setIconSize(QSize(150, 150))
button_change_cloth.setStyleSheet("""
    QToolButton {
        background-color: #1565d0;
        color: white;
        border-radius: 55px;
        border: 2px solid #388E3C;
        min-width: 150px;
        min-height: 150px;
        max-width: 150px;
        max-height: 150px;
    }
    QToolButton:pressed {
        background-color: #0b3cde;
    }
    QToolButton:hover {
        background-color: #2575f0;
    }
""")
button_change_cloth.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
label_change_cloth = QLabel("服切り替え")
label_cloth_status = QLabel("現在の服:スーツ")

widget1 = create_button_label_set(button_cloth_on_off, label_cloth_on_off, label_show_status)
widget2 = create_button_label_set(button_change_cloth, label_change_cloth, label_cloth_status)

# メニュー
menu = QMenu()
camera_action = menu.addAction(f"カメラID : {camera_id}", change_camera_id)
menu.addAction("fuga")
menu.addAction("piyo")
menu.setStyleSheet("""
QMenu {
    background-color: #444444;
    color: white;
    border: 1px solid #222222;
    padding: 5px;
}
QMenu::item {
    padding: 5px 20px;
    background-color: transparent;
}
QMenu::item:selected {
    background-color: #0078d7;
}
""")

button_menu = QToolButton()
button_menu.setText("その他の設定 ")
button_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
button_menu.setMenu(menu)
button_menu.setStyleSheet("""
    QToolButton {
        background-color: #1565d0;
        color: white;
        border-radius: 55px;
        border: 2px solid #388E3C;
        min-width: 150px;
        min-height: 30px;
        max-width: 150px;
        max-height: 30px;
    }
    QToolButton:hover {
        background-color: #2575f0;
    }
""")

# レイアウト
h_layout = QHBoxLayout()
h_layout.addWidget(widget1)
h_layout.addWidget(widget2)
h_layout.setSpacing(10)
h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

layout = QVBoxLayout()
layout.setAlignment(Qt.AlignmentFlag.AlignTop)
layout.addLayout(h_layout)
layout.setSpacing(60)
layout.addWidget(button_menu, alignment=Qt.AlignmentFlag.AlignCenter)

window.setLayout(layout)
window.show()

# 起動時に映像処理を開始
start_processing()

sys.exit(guiapp.exec())
