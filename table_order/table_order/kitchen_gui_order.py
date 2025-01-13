import time
from collections import deque

import matplotlib.pyplot as plt
import pandas as pd
import rclpy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from table_order.db import db


class MainPage(QWidget):

    class ThreadRefresh(QThread):
        refresh_orders = pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)

        def run(self):
            while True:
                time.sleep(1)
                self.refresh_orders.emit()

    class OrderBox(QGroupBox):
        delete_requested = pyqtSignal(object)  # 삭제 요청 시그널

        def __init__(self, order_id, table_number, parent=None):
            super().__init__(f"주문번호{order_id}", parent)
            self.orders = []  # 주문 목록 저장
            self.orders = deque()
            self.table_number = table_number
            self.order_id = order_id
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout()

            table_label = QLabel(f"T{self.table_number}")
            table_label.setStyleSheet(
                """QLabel { color: gray; font-size: 14px; font-weight: bold; padding: 2px; }"""
            )

            layout.addWidget(table_label)

            # 스크롤 영역 생성
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)

            # 스크롤 영역에 들어갈 위젯
            self.content_widget = QWidget()
            self.content_widget.setStyleSheet(
                "QWidget {background-color: #d3d3d3;border: none;border-radius: 5px;font-size: 18px;font-weight: bold;}"
            )
            self.content_layout = QVBoxLayout(self.content_widget)

            scroll.setWidget(self.content_widget)
            layout.addWidget(scroll)

            # print(f'버튼 찍어보기: {self.order_id}')
            # 삭제 버튼
            delete_btn = QPushButton("제조 완료")
            # delete_btn.clicked.connect(self.request_delete)
            delete_btn.setStyleSheet(
                "QPushButton {background-color: #d3d3d3;border: none;border-radius: 5px;font-size: 18px;font-weight: bold;}"
            )
            delete_btn.clicked.connect(
                lambda checked, x=self.order_id: self.request_delete(x)
            )
            layout.addWidget(delete_btn)

            self.setLayout(layout)
            self.setMinimumSize(100, 120)  # 최소 크기 설정

        def add_order(self, order_text):
            """주문 추가"""
            self.orders.append(order_text)
            order_label = QLabel(order_text)
            self.content_layout.addWidget(order_label)

        def request_delete(self, order_id):
            """주문 완료 버튼 클릭 시 삭제 요청 시그널 발생"""

            db_conn = db()
            db_conn.set_order_finished(order_id)

            # print(f'찍어보기 {order_id}')
            self.delete_requested.emit(self)
            db_conn.log(f"주문번호 {order_id} 완료")

        def get_orders(self):
            """현재 주문 목록 반환"""
            return self.orders

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.current_order_id = 1
        self.grid_layout = QGridLayout()
        self.order_boxes = []
        self.add_orders_from_db()
        self.setup_timer()

        self.thread_refresh = self.ThreadRefresh()
        self.init_ui()
        self.thread_refresh.refresh_orders.connect(self.refresh_list)
        self.thread_refresh.start()

    def init_ui(self):
        main_layout = QVBoxLayout()

        settings_layout = QHBoxLayout()

        settings_btn = QPushButton("⚙ 매출 확인")
        settings_btn.clicked.connect(self.show_graph)

        datetime_layout = QVBoxLayout()

        self.date_label = QLabel()
        self.date_label.setStyleSheet(
            "QLabel {color: #333333;font-size: 12px;padding: 2px;}"
        )

        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            "QLabel {color: #333333;font-size: 14px;font-weight: bold;padding: 2px;}"
        )

        datetime_layout.addWidget(self.date_label)
        datetime_layout.addWidget(self.time_label)
        datetime_layout.setSpacing(0)

        settings_layout.addWidget(settings_btn)
        settings_layout.addStretch()
        settings_layout.addLayout(datetime_layout)

        main_layout.addLayout(settings_layout)
        main_layout.addLayout(self.grid_layout)

        bottom_layout = QHBoxLayout()

        bottom_layout.addStretch()

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(30, 30)
        next_btn.setStyleSheet(
            "QPushButton {background-color: #4CAF50;color: white;font-weight: bold;border-radius: 5px;}"
        )
        next_btn.clicked.connect(self.next_page)

        # bottom_layout.addWidget(robot_btn)
        bottom_layout.addWidget(next_btn)
        bottom_layout.setSpacing(10)
        bottom_layout.setContentsMargins(20, 0, 0, 0)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)
        self.update_datetime()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

    def update_datetime(self):
        current_datetime = QDateTime.currentDateTime()
        self.date_label.setText(current_datetime.toString("yyyy년 MM월 dd일"))
        self.time_label.setText(current_datetime.toString("HH:mm:ss"))

    def create_order_box(self, table_number, order_num):

        box = self.OrderBox(order_num, table_number)
        box.delete_requested.connect(self.delete_order_box)
        self.order_boxes.append(box)
        self.grid_layout.addWidget(
            box, (len(self.order_boxes) - 1) // 4, (len(self.order_boxes) - 1) % 4
        )
        # self.current_order_id += 1
        return box

    def delete_order_box(self, box):
        self.grid_layout.removeWidget(box)
        box.hide()
        self.order_boxes.remove(box)
        box.deleteLater()
        self.rearrange_boxes()

    def rearrange_boxes(self):
        for box in self.order_boxes:
            self.grid_layout.removeWidget(box)

        for i, box in enumerate(self.order_boxes):
            box.table_number = i + 1
            self.grid_layout.addWidget(box, i // 4, i % 4)

    def show_graph(self):
        db_conn = db()
        data = db_conn.runsql("select * from Orders")

        # 데이터프레임으로 변환
        df = pd.DataFrame(
            data, columns=["ID", "OrderID", "메뉴", "수량", "시간", "상태"]
        )
        df["시간"] = pd.to_datetime(df["시간"])  # 시간 변환
        df["시간대"] = df["시간"].dt.hour  # 시간대 추출

        prices = db_conn.get_menu()

        # 매출 계산
        df["단가"] = df["메뉴"].map(prices).fillna(0)
        df["매출"] = df["수량"] * df["단가"]

        # 시간대별 매출 합계
        sales_by_hour = df.groupby("시간대")["매출"].sum()

        # 모든 시간대를 포함하기 위해 0~23시 초기화
        all_hours = pd.Series(0, index=range(24))
        sales_by_hour = all_hours.add(sales_by_hour, fill_value=0)

        # 그래프 그리기
        plt.figure(figsize=(12, 6))
        sales_by_hour.plot(kind="bar", color="lightblue", alpha=0.8, edgecolor="black")
        plt.title("Sales by Hour", fontsize=16)
        plt.xlabel("hours", fontsize=14)
        plt.ylabel("sales", fontsize=14)
        plt.xticks(range(24), [f"{hour}" for hour in range(24)], rotation=0)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()

        # 그래프 표시
        plt.show()

    def show_fire_alert(self):
        title = "화재경보"
        msg = "화재가 발생했습니다!\n테이블에 알립니다."
        QMessageBox.warning(self, title, msg)

    def call_robot(self):
        title = "알림"
        msg = "로봇을 호출했습니다."

        QMessageBox.information(self, title, msg)

    def next_page(self):
        if self.parent():
            parent_stack = self.parent()
            parent_stack.setCurrentIndex(1)

    def add_orders_from_db(self):
        # DB 연결
        db_instance = db()

        # 주방에서 보여줄 주문 데이터 가져오기 (완료되지 않은 주문들)
        kitchen_orders = db_instance.get_kitchen()
        # print(f'비교1: {kitchen_orders}')

        # orders_dict를 만들어서 같은 table_num을 가진 주문들을 그룹화
        orders_dict = {}
        for order in kitchen_orders:
            # kitchen SQL 쿼리 결과는 (order_num, table_num, menu_name, count) 형식
            order_num, table_num, menu_name, count = order

            # 테이블 번호가 딕셔너리에 없으면 초기화
            if order_num not in orders_dict:
                orders_dict[order_num] = {"table_num": table_num, "orders": []}

            # 메뉴 이름과 수량을 포맷팅하여 추가
            orders_dict[order_num]["orders"].append(f"{menu_name} {count}")

        # print(f'비교2: {orders_dict}')

        # 각 테이블의 주문을 GUI에 표시
        for order_num, order_info in orders_dict.items():
            # OrderBox 생성 (order_num을 사용)
            box = self.create_order_box(order_info["table_num"], order_num)

            # 해당 테이블의 모든 주문 추가
            for order in order_info["orders"]:
                box.add_order(order)

    def refresh_list(self):

        for i in range(len(self.order_boxes))[::-1]:
            self.delete_order_box(self.order_boxes[i])

        self.add_orders_from_db()
        # db_instance = db()
        # # 주방에서 보여줄 주문 데이터 가져오기 (완료되지 않은 주문들)
        # kitchen_orders = db_instance.get_kitchen()
        # orders_dict = {}
        # # print(len(kitchen_orders))
        # for order in kitchen_orders:
        #     # kitchen SQL 쿼리 결과는 (order_num, table_num, menu_name, count) 형식
        #     order_num, table_num, menu_name, count = order

        #     # 테이블 번호가 딕셔너리에 없으면 초기화
        #     if order_num not in orders_dict:
        #         orders_dict[order_num] = {"table_num": table_num, "orders": []}

        #     # 메뉴 이름과 수량을 포맷팅하여 추가
        #     orders_dict[order_num]["orders"].append(f"{menu_name} {count}")

        # for order_num, order_info in orders_dict.items():
        #     # OrderBox 생성 (order_num을 사용)
        #     box = self.create_order_box(order_info["table_num"], order_num)

        #     # 해당 주문번호의 모든 주문 추가
        #     for order in order_info["orders"]:
        #         box.add_order(order)
