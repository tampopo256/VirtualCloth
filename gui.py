import sys
from PyQt6.QtWidgets import QApplication, QWidget, QToolButton, QMenu, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize

clothes = ["スーツ","Tシャツ", "上裸"]
current_cloth_idx = 0

def create_button_label_set(button, label, label2):
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.addWidget(button)
    layout.addWidget(label)
    layout.addWidget(label2)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return container

def toggle_icon(checked):
    if checked:
        button_cloth_on_off.setIcon(QIcon("img/suit.png"))
        label_show_status.setText("表示:ON")
    else:
        button_cloth_on_off.setIcon(QIcon("img/unsuit.png"))
        label_show_status.setText("表示:OFF")

def change_cloth():
    global current_cloth_idx
    current_cloth_idx = (current_cloth_idx + 1) % len(clothes)
    label_cloth_status.setText(f"現在の服:{clothes[current_cloth_idx]}")

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

button_cloth_on_off = QToolButton()
button_cloth_on_off.toggled.connect(toggle_icon)
button_cloth_on_off.setCheckable(True)
button_cloth_on_off.setIcon(QIcon("img/unsuit.png"))
button_cloth_on_off.setIconSize(QSize(150, 150))
button_cloth_on_off.setStyleSheet("""
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
        background-color: #0b3cde;
    }
    QToolButton:hover {
        background-color: #2575f0;     /* ホバー時 */
    }
""")
label_cloth_on_off = QLabel("表示切替")
label_show_status = QLabel("表示:OFF")

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
    QToolButton:hover {
        background-color: #2575f0;     /* ホバー時 */
    }
""")
button_change_cloth.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
label_change_cloth = QLabel("服切り替え")
label_cloth_status = QLabel("現在の服:スーツ")

widget1 = create_button_label_set(button_cloth_on_off, label_cloth_on_off, label_show_status)
widget2 = create_button_label_set(button_change_cloth, label_change_cloth, label_cloth_status)

menu = QMenu()
menu.addAction("1")
menu.addAction("2")
menu.addAction("3")

button_menu = QToolButton()
button_menu.setText("その他の設定")
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


sys.exit(app.exec())