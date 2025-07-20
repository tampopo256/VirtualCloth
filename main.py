import sys
from PyQt6.QtWidgets import QApplication, QWidget, QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer
from backend.app import VirtualTryOnApp
import cv2
import threading

clothes = ["スーツ","Tシャツ", "上裸"] # 変更可能な衣装(推定)
current_cloth_idx = 0 # 現在の衣装管理用
processing_thread = None
stop_event = threading.Event()
latest_frame = None
frame_lock = threading.Lock()
app_backend = None

# GUI更新用のタイマー
display_timer = QTimer()

def run_processing_thread():
    """映像処理のみを行うスレッドのターゲット関数 (GUI操作はしない)"""
    global app_backend, latest_frame
    try:
        app_backend = VirtualTryOnApp()
        
        while not stop_event.is_set():
            frame = app_backend.read()
            if frame is not None:
                with frame_lock:
                    global latest_frame
                    latest_frame = frame.copy()
    
    except Exception as e:
        print(f"映像処理中にエラーが発生しました: {e}")
    finally:
        if app_backend:
            app_backend.stop()
        print("映像処理スレッドを終了しました。")

def update_display_window():
    """メインスレッドで実行され、フレームを表示する関数"""
    global latest_frame
    WINDOW_NAME = "Virtual Try-On"
    
    with frame_lock:
        frame_to_show = latest_frame
    
    if frame_to_show is not None:
        try:
            cv2.imshow(WINDOW_NAME, frame_to_show)
            # 'q'キーで終了、またはウィンドウが閉じられたかを確認
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                # ユーザーがウィンドウを閉じた場合、ボタンの状態を更新
                if button_cloth_on_off.isChecked():
                    button_cloth_on_off.setChecked(False)
        except cv2.error:
            # ウィンドウが予期せず閉じられた場合のエラーを無視
            if button_cloth_on_off.isChecked():
                button_cloth_on_off.setChecked(False)

def toggle_video(checked):
    """アイコン切り替え用 (服ON/OFF)"""
    global processing_thread
    if checked:
        # ONにする処理
        button_cloth_on_off.setIcon(QIcon("front/img/suit.png"))
        button_cloth_on_off.setStyleSheet(base_style + button_clicked)
        label_show_status.setText("表示:ON")
        
        stop_event.clear()
        processing_thread = threading.Thread(target=run_processing_thread, daemon=True)
        processing_thread.start()
        # 30FPS相当で表示を更新
        display_timer.start(33)
    else:
        # OFFにする処理
        display_timer.stop() # 先にタイマーを止める
        
        button_cloth_on_off.setIcon(QIcon("front/img/unsuit.png"))
        button_cloth_on_off.setStyleSheet(base_style + button_unclicked)
        label_show_status.setText("表示:OFF")
        
        if processing_thread and processing_thread.is_alive():
            stop_event.set() # スレッドに停止を通知
        
        cv2.destroyAllWindows()
    
def create_button_label_set(button, label, label2): # 表示管理用
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(button)
    layout.addWidget(label)
    layout.addWidget(label2)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return container

def change_cloth(): # 服切り替え用ボタン
    global current_cloth_idx
    current_cloth_idx = (current_cloth_idx + 1) % len(clothes)
    label_cloth_status.setText(f"現在の服:{clothes[current_cloth_idx]}")

# 基本設定
guiapp = QApplication(sys.argv)
guiapp.setStyleSheet("""
    QLabel {
        color: black; /* 文字色*/
        
    }
""")
font = QFont("Meiryo", 14, QFont.Weight.Bold)
guiapp.setFont(font)
window = QWidget()
window.setWindowTitle("VirtualCloth")
window.setStyleSheet("background-color: white;")
window.setFixedSize(500, 500)

display_timer.timeout.connect(update_display_window)

# 服ON/OFFボタン
button_cloth_on_off = QToolButton()
button_cloth_on_off.toggled.connect(toggle_video)
button_cloth_on_off.setCheckable(True)
button_cloth_on_off.setIcon(QIcon("front/img/unsuit.png"))
button_cloth_on_off.setIconSize(QSize(150, 150))
base_style = """
    QToolButton {
        background-color: #1565d0;     /* 背景色 */
        color: white;                  /* 文字色 */
        border-radius: 55px;           /* 角丸 */
        border: 2px solid #388E3C;     /* 枠線 */
        min-width: 150px; /* ボタンサイズ幅*/
        min-height: 150px; /* ボタンサイズ高さ*/
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

# 衣装切り替え用ボタン
button_change_cloth = QToolButton()
button_change_cloth.clicked.connect(change_cloth)
button_change_cloth.setIcon(QIcon("front/img/change_cloth.png"))
button_change_cloth.setIconSize(QSize(150, 150))
button_change_cloth.setStyleSheet("""
    QToolButton {
        background-color: #1565d0;     /* 背景色 */
        color: white;                  /* 文字色 */
        border-radius: 55px;           /* 角丸 */
        border: 2px solid #388E3C;     /* 枠線 */
        min-width: 150px; /* ボタンサイズ幅*/
        min-height: 150px; /* ボタンサイズ高さ*/
        max-width: 150px;
        max-height: 150px;
    }
    QToolButton:pressed {
        background-color: #0b3cde; /* 押している間 */
    }                 
    QToolButton:hover {
        background-color: #2575f0;     /* ホバー時 */
    }
""")
button_change_cloth.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
label_change_cloth = QLabel("服切り替え")
label_cloth_status = QLabel("現在の服:スーツ")

# 配置調整用
widget1 = create_button_label_set(button_cloth_on_off, label_cloth_on_off, label_show_status)
widget2 = create_button_label_set(button_change_cloth, label_change_cloth, label_cloth_status)

# その他の設定用
menu = QMenu()
menu.addAction("hoge")
menu.addAction("fuga")
menu.addAction("piyo")
menu.setStyleSheet("""
QMenu {
    background-color: #444444;      /* 背景色 */
    color: white;                   /* 文字色 */
    border: 1px solid #222222;      /* 枠線 */
    padding: 5px;                   /* 内側の余白 */
}
QMenu::item {
    padding: 5px 20px;
    background-color: transparent;
}
QMenu::item:selected {
    background-color: #0078d7;     /* 選択中の背景色 */
}
""")

## 設定中身用
button_menu = QToolButton()
button_menu.setText("その他の設定 ")
button_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
button_menu.setMenu(menu)
button_menu.setStyleSheet("""
    QToolButton {
        background-color: #1565d0;     /* 背景色 */
        color: white;                  /* 文字色 */
        border-radius: 55px;           /* 角丸 */
        border: 2px solid #388E3C;     /* 枠線 */
        min-width: 150px; /* ボタンサイズ幅*/
        min-height: 30px; /* ボタンサイズ高さ*/
        max-width: 150px;
        max-height: 30px;
    }
    QToolButton:hover {
        background-color: #2575f0;     /* ホバー時 */
    }
""")

# 配置管理
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

# app=VirtualTryOnApp()

# while True:
#     if app.ret or (app.frame is not None):
#         cv2.imshow("main",app.frame)
#     # 'q'キーで終了
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         app.stop()
#         break
# print("1")
# ウィンドウ閉じた際の処理 (終了)
sys.exit(guiapp.exec())