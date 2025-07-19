import sys
from PyQt6.QtWidgets import QApplication, QWidget, QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize


clothes = ["スーツ","Tシャツ", "上裸"] # 変更可能な衣装(推定)
current_cloth_idx = 0 # 現在の衣装管理用

def create_button_label_set(button, label, label2): # 表示管理用
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(button)
    layout.addWidget(label)
    layout.addWidget(label2)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return container

def toggle_icon(checked): # アイコン切り替え用 (服ON/OFF)
    if checked:
        button_cloth_on_off.setIcon(QIcon("img/suit.png"))
        button_cloth_on_off.setStyleSheet(base_style + button_clicked)
        label_show_status.setText("表示:ON")
        #(ここでbackendと統合)
    else:
        button_cloth_on_off.setIcon(QIcon("img/unsuit.png"))
        button_cloth_on_off.setStyleSheet(base_style + button_unclicked)
        label_show_status.setText("表示:OFF")
        #(ここで何もなしに)

def change_cloth(): # 服切り替え用ボタン
    global current_cloth_idx
    current_cloth_idx = (current_cloth_idx + 1) % len(clothes)
    label_cloth_status.setText(f"現在の服:{clothes[current_cloth_idx]}")

# 基本設定
app = QApplication(sys.argv)
app.setStyleSheet("""
    QLabel {
        color: black; /* 文字色*/
        
    }
""")
font = QFont("Meiryo", 14, QFont.Weight.Bold)
app.setFont(font)
window = QWidget()
window.setWindowTitle("VirtualCloth")
window.setStyleSheet("background-color: white;")
window.setFixedSize(500, 500)

# 服ON/OFFボタン
button_cloth_on_off = QToolButton()
button_cloth_on_off.toggled.connect(toggle_icon)
button_cloth_on_off.setCheckable(True)
button_cloth_on_off.setIcon(QIcon("img/unsuit.png"))
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
button_change_cloth.setIcon(QIcon("img/change_cloth.png"))
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
menu.addAction("自己画像表示")
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

# ウィンドウ閉じた際の処理 (終了)
sys.exit(app.exec())