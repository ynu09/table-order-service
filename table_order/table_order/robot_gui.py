import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
from table_order.db import db
from table_order.robot_node import RobotNavi
import rclpy


class RobotWindow(QWidget):

    class Thread_robot_node(QThread):
        result = pyqtSignal(str)

        def __init__(self):
            # debugpy.debug_this_thread()
            super().__init__()
            # self.started.emit()
            self.robot_node = RobotNavi()

        def run(self):
            # debugpy.debug_this_thread()

            self.db_conn = db()
            time.sleep(0.3)

            print("spin start")
            rclpy.spin(self.robot_node)

    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread_node_robot = self.Thread_robot_node()
        self.thread_node_robot.start()

    def initUI(self):
        # 메인 레이아웃
        layout = QVBoxLayout()

        # 메시지를 표시할 흰색 박스
        message_box = QLabel()
        message_box.setText("음식을 내리신 후\n아래 화면의 확인 버튼을\n눌러주세요!")
        message_box.setFixedSize(700, 500)
        message_box.setAlignment(Qt.AlignCenter)

        message_box.setStyleSheet(
            """
            QLabel {
                background-color: white;
                padding: 30px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
            }
        """
        )
        message_box.setWordWrap(True)

        # 확인 버튼
        confirm_btn = QPushButton("확인")
        confirm_btn.setFixedSize(200, 50)  # 버튼 크기 고정
        confirm_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        confirm_btn.clicked.connect(self.go_kitchen_button_clicked)

        # 레이아웃에 위젯 추가
        layout.addStretch()  # 상단 여백
        layout.addWidget(message_box, alignment=Qt.AlignCenter)
        layout.addSpacing(20)  # 메시지 박스와 버튼 사이 간격
        layout.addWidget(confirm_btn, alignment=Qt.AlignCenter)
        layout.addStretch()  # 하단 여백

        self.setLayout(layout)

        # 윈도우 설정
        self.setStyleSheet("background-color: #404040;")  # 배경색 설정

        self.setWindowTitle("로봇 화면")
        self.setGeometry(100, 100, 800, 600)
        self.center()

    def center(self):
        # 화면 중앙에 윈도우 배치
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def go_kitchen_button_clicked(self):
        self.thread_node_robot.robot_node.navigate_to_pose_send_goal(9)


def main():

    # PyQt 앱 생성
    app = QApplication(sys.argv)

    # 메인 윈도우 생성
    window = RobotWindow()
    window.setStyleSheet("background-color: #404040;")
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
