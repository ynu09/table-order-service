"""
robot 경로 뜨는 페이지
"""

# import debugpy


import threading
import time
from collections import deque

import PyQt5.QtCore
import PyQt5.QtGui
import PyQt5.QtWidgets
import rclpy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from rclpy.node import Node
from rclpy.qos import QoSProfile
from std_msgs.msg import String

from table_order.kitchen_gui_admin import MenuManager, SettingsDialog
from table_order.db import db
from table_order.kitchen_node import KitchenNavi

# from admin_page import MenuManager, SettingsDialog
# from db import db
# from kitchen_node import KitchenNavi


class MyImage(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setPixmap(QPixmap(image_path))
        self.setScaledContents(True)
        self.setFixedSize(50, 50)  # 이미지 크기 조정
        self.setStyleSheet("background: transparent;")

        # self.timer = QTimer()
        # self.timer.timeout.connect(self.move_image)
        # self.timer.start(50)  # 50ms 간격으로 이미지 이동

        self.parent_widget = parent
        # self.direction = QPoint(
        #     random.choice([-1, 1]), random.choice([-1, 1])
        # )  # 초기 이동 방향

    def move_image(self):
        if not self.parent_widget:
            return

        # 현재 위치
        current_pos = self.pos()

        # 부모 위젯 크기 가져오기
        parent_width = self.parent_widget.width()
        parent_height = self.parent_widget.height()

        # # 새 위치 계산
        # new_x = current_pos.x() + self.direction.x() * 5
        # new_y = current_pos.y() + self.direction.y() * 5

        # 벽에 부딪히면 방향 반전
        # if new_x <= 0 or new_x + self.width() >= parent_width:
        #     self.direction.setX(-self.direction.x())
        # if new_y <= 0 or new_y + self.height() >= parent_height:
        #     self.direction.setY(-self.direction.y())

        # 새로운 위치로 이동
        self.move(current_pos + self.direction)


combo_log_level = 0


class SecondPage(QWidget):

    class ThreadRefreshLog(PyQt5.QtCore.QThread):
        result = PyQt5.QtCore.pyqtSignal(str)

        def __init__(self):
            # debugpy.debug_this_thread()
            super().__init__()
            # self.started.emit()

        def run(self):
            # debugpy.debug_this_thread()

            self.db_conn = db()
            # starttime = time.time()
            level_dict = {
                0: "info",
                1: "warning",
                2: "error",
                3: "debug",
                4: "fatal",
            }
            global combo_log_level
            while True:
                log_level_from_combo = 4
                if type(combo_log_level) == type(QComboBox()):
                    log_level_from_combo = int(combo_log_level.currentText())
                log_data_all = self.db_conn.read_log(log_level_from_combo)
                log_readable = []
                for msg in log_data_all:
                    log_readable.append(f"[{level_dict[msg[0]]}][{msg[2]}]{msg[1]}")
                self.result.emit("\n".join(log_readable))
                time.sleep(0.3)

        def stop(self):
            # #debugpy.debug_this_thread()
            self.quit()
            self.wait(5000)

    class ThreadKitchenNode(PyQt5.QtCore.QThread):
        result_set_initial_pose = PyQt5.QtCore.pyqtSignal(str)

        def __init__(self):
            # debugpy.debug_this_thread()
            PyQt5.QtCore.QThread.__init__(self)
            self.node_kitchen = KitchenNavi()
            # self.started.emit()

        def run(self):
            # debugpy.debug_this_thread()
            # starttime = time.time()
            db_conn = db()

            # 초기 위치 설정 (주방)
            while (
                not self.node_kitchen.set_initial_pose_service_client.wait_for_service(
                    timeout_sec=0.5
                )
            ):
                db_conn.log("Service /set_initial_pose not available, waiting again...")
                print("Service /set_initial_pose not available, waiting again...")
            self.node_kitchen.set_initial_pose(*self.node_kitchen.init_pose)
            print("spin start")
            rclpy.spin(self.node_kitchen)
            # while True:
            #     rclpy.spin_once(self.node_kitchen, timeout_sec=0.5)
            #     # self.result_set_initial_pose_service_client.emit(
            #     #     self.node_kitchen.set_initial_pose()
            #     # )
            #     self.usleep(500)

        def stop(self):
            # #debugpy.debug_this_thread()
            self.quit()
            self.wait(5000)

    def __init__(self, parent=None):
        # debugpy.debug_this_thread()
        super().__init__(parent)

        # self.threadkitchennode = self.ThreadKitchenNode(self)
        # self.threadkitchennode.started.connect(self.refresh_log)
        # self.threadkitchennode.start()

        self.thread_refresh_log = self.ThreadRefreshLog()
        self.thread_refresh_log.result.connect(self.refresh_log)
        self.thread_refresh_log.start()

        self.thread_node_kitchen = self.ThreadKitchenNode()
        self.thread_node_kitchen.result_set_initial_pose.connect(self.refresh_log)
        print("thread_node_kitchen start")
        self.thread_node_kitchen.start()

        self.init_ui()

    def refresh_log(self, msg):
        # debugpy.debug_this_thread()
        self.log_display.setText(msg)
        self.log_display.moveCursor(QTextCursor.End)
        # time.sleep(1)

    def init_ui(self):
        # debugpy.debug_this_thread()
        # 메인 수평 레이아웃 (왼쪽과 오른쪽을 나누기 위함)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 왼쪽 위젯
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)

        # 상단 '주방' 텍스트
        kitchen_btn = QPushButton("주방")
        kitchen_btn.setStyleSheet(
            "QPushButton {font-size: 24px;font-weight: bold;color: black;background-color: #f0f0f0;padding: 10px;}"
        )
        kitchen_btn.setFixedSize(100, 100)
        # kitchen_btn.setAlignment(Qt.AlignCenter)
        kitchen_btn.clicked.connect(self.go_kitchen_button_clicked)

        # 테이블 그리드를 포함할 위젯
        table_widget = QWidget()
        table_widget.setStyleSheet("background-color: #404040;")
        grid_layout = QGridLayout(table_widget)
        grid_layout.setSpacing(10)

        # 테이블 버튼 생성
        for i in range(9):
            row = i // 3
            col = i % 3
            btn = QPushButton(str(i + 1))
            btn.setFixedSize(70, 70)
            btn.setStyleSheet(
                "QPushButton {background-color: #d3d3d3;border: none;border-radius: 5px;font-size: 18px;font-weight: bold;}"
            )
            btn.clicked.connect(lambda checked, x=i: self.go_button_clicked(x))
            grid_layout.addWidget(btn, row, col)
            # 수평, 수직 간격을 모두 10픽셀로 설정
            grid_layout.setSpacing(30)

        # 왼쪽 레이아웃에 위젯들 추가
        left_layout.addWidget(table_widget, alignment=Qt.AlignCenter)
        left_layout.addWidget(kitchen_btn, alignment=Qt.AlignRight)

        # 오른쪽 위젯 (로그 표시 영역)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 로그를 표시할 텍스트 에디터
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(
            "QTextEdit {background-color: #ffffff;border: none;font-family: 'Courier New';font-size: 12px;}"
        )
        right_layout.addWidget(self.log_display)

        # 화재경보 버튼
        fire_alert_btn = QPushButton("🔥 화재경보")
        fire_alert_btn.setFixedSize(100, 30)
        fire_alert_btn.setStyleSheet(
            "QPushButton {background-color: #FFD700;color: #FF0000;font-weight: bold;border-radius: 5px;border: 1px solid #FFB300;}QPushButton:hover {background-color: #FFC400;}"
        )
        fire_alert_btn.clicked.connect(self.show_fire_alert)

        # 이전 페이지 버튼
        back_btn = QPushButton("◀")
        back_btn.setFixedSize(30, 30)
        back_btn.setStyleSheet(
            "QPushButton {background-color: #4CAF50;color: white;font-weight: bold;border-radius: 5px;}"
        )
        back_btn.clicked.connect(self.go_back)

        self.combo_log_level = QComboBox()
        self.combo_log_level.addItems(["0", "1", "2", "3", "4"])
        global combo_log_level
        combo_log_level = self.combo_log_level

        # 버튼들 순서대로 추가
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.combo_log_level, alignment=Qt.AlignLeft)
        bottom_layout.addStretch()
        bottom_layout.addWidget(fire_alert_btn, alignment=Qt.AlignRight)
        bottom_layout.addWidget(back_btn, alignment=Qt.AlignRight)

        right_layout.addLayout(bottom_layout)

        # 왼쪽과 오른쪽 위젯을 메인 레이아웃에 추가
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # 왼쪽과 오른쪽의 비율을 1:1로 설정
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 1)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #404040;")

    def go_button_clicked(self, i):
        self.thread_node_kitchen.node_kitchen.navigate_to_pose_send_goal(i)

    def go_kitchen_button_clicked(self):
        self.thread_node_kitchen.node_kitchen.navigate_to_pose_send_goal(9)

    def go_back(self):
        if self.parent():
            self.parent().setCurrentIndex(0)

    def show_fire_alert(self):
        self.flag_fire = True
        self.db_conn = db()

        def thread_function():
            # rclpy.init()
            # node_pub = FirePublisher()
            # # msg = String()
            # # msg.data = "test123"
            # # while self.flag_fire == True:
            # #     node_pub.publisher_.publish(msg)
            # #     node_pub.get_logger().info(f"Published message: {msg}")
            # # pub_node.publisher_.publish()
            # while self.flag_fire == True:
            #     rclpy.spin_once(node_pub)
            # node_pub.destroy_node()
            # rclpy.shutdown()
            db_conn = db()
            while self.flag_fire:
                msg = String()
                msg.data = f"fire {time.time() + 1.5}"
                # print(msg.data)
                db_conn.log(f"[Topic][fire][Published] {msg.data}", 4)
                self.thread_node_kitchen.node_kitchen.fire_alert_publisher.publish(msg)
                time.sleep(0.5)
                # rclpy.spin_once(self.thread_node_kitchen.node_kitchen)

        thread = threading.Thread(target=thread_function)
        thread.start()

        # message = "화재경보", "화재가 발생했습니다! 테이블에 알립니다."
        self.db_conn.log("화재발생")
        res = QMessageBox.warning(self, "화재발생", "화재발생\n테이블에 알립니다.")
        if res == QMessageBox.Ok:
            self.flag_fire = False

        # message = "화재경보", "화재가 발생했습니다! 테이블에 알립니다."
        # res = QMessageBox.warning(
        #     self, "화재경보", "화재가 발생했습니다!\n테이블에 알립니다."
        # )
        # if res == QMessageBox.Ok:
        #     self.flag_fire = False
