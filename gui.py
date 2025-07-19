import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtGui import QFont

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("VirtualCloth")
window.setStyleSheet("background-color: white;")
window.setFixedSize(500, 500)

button1 = QPushButton("服表示ON/OFF")
button1.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;     /* 背景色 */
        color: white;                  /* 文字色 */
        border-radius: 10px;           /* 角丸 */
        border: 2px solid #388E3C;     /* 枠線 */
        min-width: 150px; /* ボタンサイズ幅*/
        min-height: 150px; /* ボタンサイズ高さ*/
        max-width: 150px;
        max-height: 150px;
    }
    QPushButton:hover {
        background-color: #45a049;     /* ホバー時 */
    }
""")
button2 = QPushButton("服切り替え")
button2.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;     /* 背景色 */
        color: white;                  /* 文字色 */
        border-radius: 10px;           /* 角丸 */
        border: 2px solid #388E3C;     /* 枠線 */
        min-width: 150px; /* ボタンサイズ幅*/
        min-height: 150px; /* ボタンサイズ高さ*/
        max-width: 150px;
        max-height: 150px;
    }
    QPushButton:hover {
        background-color: #45a049;     /* ホバー時 */
    }
""")
label = QLabel("そのほかの設定")
label.setStyleSheet("color: black; font-size: 14pt;")
combo = QComboBox()
combo.setStyleSheet("""
    QComboBox {
        background-color: #4CAF50;     /* 背景色 */
        color: white;                  /* 文字色 */
        border-radius: 10px;           /* 角丸 */
        border: 2px solid #388E3C;     /* 枠線 */
    }
    QComboBox:hover {
        background-color: #45a049;     /* ホバー時 */
    }
""")
combo.addItems(["1", "2", "3"])

h_layout = QHBoxLayout()
h_layout.addWidget(button1)
h_layout.addWidget(button2)
h_layout.setSpacing(5) 
layout = QVBoxLayout()
layout.addLayout(h_layout)
layout.addWidget(label)
layout.addWidget(combo)

window.setLayout(layout)
window.show()

font = QFont("Meiryo", 12, QFont.Weight.Bold)
button1.setFont(font)
button2.setFont(font)
combo.setFont(font)
sys.exit(app.exec())