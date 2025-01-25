import sys
import threading
import time
from datetime import datetime

import rclpy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from rclpy.node import Node
from std_msgs.msg import String

from .table_node import TableNode
from .db import db
from table_msgs.srv import MenuOrder


class ThreadFire(QThread):
    set_window_index = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def run(self):
        self.node_table = TableNode()
        while True:
            try:
                rclpy.spin_once(self.node_table, timeout_sec=2)
                if (
                    self.node_table.recv != ""
                    and float(self.node_table.recv.split(" ")[-1]) > time.time()
                ):
                    # window.setCurrentIndex(1)
                    self.set_window_index.emit(1)
                else:
                    # window.setCurrentIndex(0)
                    self.set_window_index.emit(0)
            finally:
                pass
        node_sub.destroy_node()

    def stop(self):
        # #debugpy.debug_this_thread()
        self.quit()
        self.wait(5000)


thread_table_node = ThreadFire()
thread_table_node.start()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # clicked 시그널을 정의

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # clicked 시그널 발생

    def connectClicked(self, func):
        self.clicked = func


class OrderHistoryDialog(QDialog):
    def __init__(self, order_history, parent=None):
        super().__init__(parent)
        self.order_history = order_history
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("주문 내역")
        self.setFixedSize(400, 600)
        self.setStyleSheet(
            "QDialog {background-color: #404040;}QLabel {color: #333333;}QPushButton {font-size: 14px;padding: 8px;border-radius: 4px;}"
        )

        main_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea {border: none;background-color: #F5F5F5;border-radius: 8px;}"
        )

        content_widget = QWidget()
        content_layout = QVBoxLayout()

        total_sum = 0  # 전체 주문의 총 합계

        # 모든 주문을 담을 큰 박스
        orders_widget = QWidget()
        orders_widget.setStyleSheet(
            "QWidget {background-color: white;border-radius: 8px;}"
        )
        orders_layout = QVBoxLayout()

        for order_time, items in self.order_history:
            # 주문 시간 표시
            time_widget = QWidget()
            time_widget.setStyleSheet("background-color: #E8E8E8; border-radius: 4px;")
            time_layout = QHBoxLayout()
            time_label = QLabel(f"주문 시간: {order_time}")
            time_label.setFont(QFont("Arial", 12, QFont.Bold))
            time_label.setStyleSheet("color: #333333;")
            time_layout.addWidget(time_label)
            time_widget.setLayout(time_layout)
            orders_layout.addWidget(time_widget)

            # 주문 항목들을 담을 컨테이너
            items_container = QWidget()
            items_container.setStyleSheet(
                "QWidget {background-color: #F8F8F8;border-radius: 4px;margin: 4px;}"
            )
            items_layout = QVBoxLayout()

            # 주문 항목들
            order_total = 0
            for item_name, (quantity, price) in items.items():
                item_widget = QWidget()
                item_layout = QHBoxLayout()

                name_label = QLabel(item_name)
                name_label.setFont(QFont("Arial", 11))
                name_label.setStyleSheet("color: #333333;")

                quantity_label = QLabel(f"X{quantity}")
                quantity_label.setFont(QFont("Arial", 11))
                quantity_label.setStyleSheet("color: #333333;")

                item_total = quantity * price
                order_total += item_total
                price_label = QLabel(f"{item_total:,}원")
                price_label.setFont(QFont("Arial", 11))
                price_label.setStyleSheet("color: #333333;")

                item_layout.addWidget(name_label)
                item_layout.addWidget(quantity_label)
                item_layout.addWidget(price_label)
                item_widget.setLayout(item_layout)
                items_layout.addWidget(item_widget)

            total_sum += order_total  # 전체 합계에 더하기

            items_container.setLayout(items_layout)
            orders_layout.addWidget(items_container)

            # 구분선 추가
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("background-color: #CCCCCC;")
            orders_layout.addWidget(line)

        orders_widget.setLayout(orders_layout)
        content_layout.addWidget(orders_widget)

        # 총 합계 표시
        total_widget = QWidget()
        total_widget.setStyleSheet(
            "QWidget {background-color: #E8E8E8;border-radius: 4px;margin-top: 10px;}"
        )
        total_layout = QHBoxLayout()
        total_label = QLabel("전체 합계:")
        total_label.setFont(QFont("Arial", 14, QFont.Bold))
        total_label.setStyleSheet("color: #333333;")
        total_price_label = QLabel(f"{total_sum:,}원")
        total_price_label.setFont(QFont("Arial", 14, QFont.Bold))
        total_price_label.setStyleSheet("color: #333333;")
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        total_layout.addWidget(total_price_label)
        total_widget.setLayout(total_layout)
        content_layout.addWidget(total_widget)

        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)

        main_layout.addWidget(scroll)

        # 닫기 버튼
        close_button = QPushButton("닫기")
        close_button.setStyleSheet(
            "QPushButton {background-color: #32CD32;color: white;border: none;}QPushButton:hover {background-color: #28A428;}"
        )
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

        self.setLayout(main_layout)


class CartDialog(QDialog):
    order_confirmed = pyqtSignal(dict, TableNode)  # 주문 확인 시그널
    items_updated = pyqtSignal(dict)  # 장바구니 업데이트 시그널 추가

    def __init__(self, cart_items, menu_data, parent=None):
        super().__init__(parent)
        self.cart_items = cart_items.copy()
        db_conn = db()
        self.menudata = db_conn.get_menu()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("주문서")
        self.setFixedSize(400, 600)
        self.setStyleSheet(
            "QDialog {background-color: #404040;}QLabel {color: black;}QPushButton {font-size: 14px;padding: 8px;border-radius: 4px;}"
        )

        layout = QVBoxLayout()

        # 장바구니 아이콘과 텍스트를 포함하는 상단 위젯
        top_widget = QWidget()
        top_widget.setStyleSheet("background-color: white; border-radius: 8px;")
        top_layout = QHBoxLayout()

        cart_icon = QLabel()
        try:
            pixmap = QPixmap("src/table_order/table_order/img/cart.png")
            scaled_pixmap = pixmap.scaled(
                24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            cart_icon.setPixmap(scaled_pixmap)
        except:
            cart_icon.setText("🛒")

        cart_text = QLabel("장바구니")
        cart_text.setFont(QFont("Arial", 12))

        top_layout.addWidget(cart_icon)
        top_layout.addWidget(cart_text)
        top_layout.addStretch()
        top_widget.setLayout(top_layout)

        # 메인 컨텐츠 영역 (스크롤 영역으로 변경)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea {background-color: white;border-radius: 8px;border: none;}"
        )

        content_widget = QWidget()
        content_widget.setStyleSheet(
            "QWidget {background-color: white;border-radius: 8px;}QLabel {font-size: 12px;}"
        )
        content_layout = QVBoxLayout()

        # 주문 항목들
        total_price = 0

        # 장바구니 아이템 표시
        for item_name, quantity in self.cart_items.items():
            item_widget = QWidget()
            item_layout = QHBoxLayout()

            # 메뉴 이름
            name_label = QLabel(item_name)
            name_label.setFont(QFont("Arial", 12))

            # 수량
            quantity_label = QLabel(f"X{quantity}")
            quantity_label.setFont(QFont("Arial", 12))

            # 가격
            print()
            price = [
                i for i in self.menudata.items() if i[0].split("_")[-1] == item_name
            ][0][1]
            item_total = quantity * price
            total_price += item_total
            price_label = QLabel(f"{item_total:,}원")
            price_label.setFont(QFont("Arial", 12))

            # 삭제 버튼 추가
            remove_button = QPushButton("X")
            remove_button.setFixedSize(30, 30)
            remove_button.setStyleSheet(
                "QPushButton {background-color: transparent;border: none;padding: 0px;}QPushButton:hover {background-color: #FFE6E6;border-radius: 15px;}"
            )
            remove_button.clicked.connect(
                lambda checked, name=item_name: self.remove_item(name)
            )

            item_layout.addWidget(name_label)
            item_layout.addWidget(quantity_label)
            item_layout.addWidget(price_label)
            item_layout.addWidget(remove_button)
            item_widget.setLayout(item_layout)
            content_layout.addWidget(item_widget)

        content_layout.addStretch()

        # 총 가격 표시
        self.total_widget = QWidget()
        total_layout = QHBoxLayout()
        total_label = QLabel("합계:")
        total_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_price_label = QLabel(f"{total_price:,}원")
        self.total_price_label.setFont(QFont("Arial", 14, QFont.Bold))
        total_layout.addWidget(total_label)
        total_layout.addStretch()
        total_layout.addWidget(self.total_price_label)
        self.total_widget.setLayout(total_layout)

        content_layout.addWidget(self.total_widget)
        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)

        # 주문하기 버튼
        order_button = QPushButton("주문하기")
        order_button.setStyleSheet(
            "QPushButton {background-color: #32CD32;color: white;border: none;}QPushButton:hover {background-color: #28A428;}"
        )
        order_button.clicked.connect(self.confirm_order)

        layout.addWidget(top_widget)
        layout.addWidget(scroll)
        layout.addWidget(order_button)

        if self.layout():
            QWidget().setLayout(self.layout())
        self.setLayout(layout)

    def remove_item(self, item_name):
        # 장바구니에서 아이템 제거
        if item_name in self.cart_items:
            del self.cart_items[item_name]
            self.init_ui()

    def confirm_order(self):
        global thread_table_node
        print("confirm_order start")
        # 주문 확인
        if self.cart_items:
            self.order_confirmed.emit(self.cart_items, thread_table_node.node_table)
            self.accept()
        else:
            self.reject()
        print("confirm_order end")


class KoreanRestaurantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # 메뉴 데이터
        self.db_conn = db()
        self.menudata = self.db_conn.get_menu()
        self.menu_data = {}
        self.futures = []
        self.categories = list(
            dict.fromkeys([item[0].split("_")[0] for item in self.menudata.items()])
        )
        self.category_buttons = {}
        self.staff_call_active = False
        self.cart_items = {}  # Dictionary to store cart items
        self.order_history = []  # List to store order history
        self.last_category = self.categories[0]
        self.styles = [
            "QFrame {background-color: #EEEEEE;border-radius: 15px;border: none;}",
            "QFrame {background-color: white;border-radius: 10px;border: none;}",
            "QPushButton {background-color: #FF6B00;color: white;border-radius: 5px;padding: 5px;margin-top: 5px;width: 60px;}QPushButton:hover {background-color: #FF8533;}",
            "background-color: #404040;",
            "background-color: #808080; color: white;",
            "QPushButton {background-color: #808080;color: white;border-radius: 5px;font-size: 14px;}QPushButton:hover {background-color: #696969;}",
            "QPushButton {background-color: white;border-radius: 25px;background-image: url('src/table_order/table_order/img/cart.png');background-position: center;background-repeat: no-repeat;}QPushButton:hover {background-color: #F0F0F0;}",
            "QPushButton {background-color: #D3D3D3;border-radius: 5px;font-size: 14px;}",
            "QPushButton {background-color: #D3D3D3;border-radius: 5px;font-size: 14px;}",
            "background-color: #FF6B00; color: white;",
            "background-color: #808080; color: white;",
            "QPushButton {background-color: #FF6B00;border-radius: 5px;font-size: 14px;color: white;}"
            "QPushButton {background-color: #D3D3D3;border-radius: 5px;font-size: 14px;}",
            "QTextEdit {background-color: #FFFFFF;border-radius: 5px;font-size: 20px;color: #333333;}",
        ]
        self.cart_ui = CartDialog(self.cart_items, self)
        # self.cart_ui.show()
        self.cart_ui.setVisible(False)
        self.update_ui()
        # self.init_ui()

    def update_ui(self):
        self.menudata = self.db_conn.get_menu()
        self.categories = list(
            dict.fromkeys([item[0].split("_")[0] for item in self.menudata.items()])
        )
        # self.category_buttons = {}
        self.staff_call_active = False
        self.menu_data = {}
        # self.cart_items = {}  # Dictionary to store cart items
        # self.order_history = []  # List to store order history
        self.init_ui()

    def init_ui(self):
        # 기본 설정
        self.setWindowTitle("E2반점 Menu")
        self.setStyleSheet(self.styles[3])

        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)

        # 왼쪽 메뉴 패널
        left_panel = QWidget()
        left_panel.setMaximumWidth(200)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # 카테고리 버튼들
        for category in self.categories:
            btn = QPushButton(category)
            btn.setFixedHeight(80)
            btn.setFixedWidth(200)
            btn.setFont(QFont("Arial", 12))
            btn.setStyleSheet(self.styles[4])
            btn.clicked.connect(lambda checked, cat=category: self.show_category(cat))
            self.category_buttons[category] = btn
            left_layout.addWidget(btn)
        left_layout.addStretch()

        # 스택 위젯 (각 카테고리별 메뉴 페이지)
        self.stack = QStackedWidget()

        for key, price in self.menudata.items():
            category, name = key.split("_")  # 카테고리와 이름으로 분리
            img_path = f"src/table_order/table_order/img/{key}.png"

            # 카테고리가 아직 없으면 빈 리스트로 초기화
            if category not in self.menu_data:
                self.menu_data[category] = []

            # 이름과 가격을 포함하는 딕셔너리를 리스트에 추가
            self.menu_data[category].append(
                {"name": name, "price": str(price) + "원", "image": img_path}
            )

        # 각 카테고리 페이지 생성
        for category, items in self.menu_data.items():
            page = QWidget()
            page_layout = QHBoxLayout()
            grid_layout = QGridLayout()
            # page_layout.setSpacing(20)

            cnt = 0
            for item in items:
                item_widget = self.create_menu_item(item)
                grid_layout.addWidget(item_widget, cnt // 4, cnt % 4)
                cnt += 1

            # 카트 레이아웃
            cart_list = QTextEdit()
            # cart_list.setPlaceholderText("Enter multiple lines of text here...")
            cart_list.setReadOnly(True)
            cart_list.setStyleSheet(self.styles[12])
            cart_list.setText(
                "\n".join(
                    [f"{key} - {value}개" for key, value in self.cart_items.items()]
                )
            )

            # 왼쪽과 오른쪽을 main_layout에 추가
            page_layout.addLayout(grid_layout)  # 오른쪽에 QTextEdit 추가
            page_layout.addWidget(cart_list)  # 오른쪽에 QTextEdit 추가

            page.setLayout(page_layout)
            self.stack.addWidget(page)

        # 하단 버튼 영역
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout()

        # 주문내역 버튼
        history_button = QPushButton("주문내역")
        history_button.setFixedSize(120, 50)
        history_button.setStyleSheet(self.styles[5])
        history_button.clicked.connect(self.show_order_history)

        # 장바구니 버튼
        cart_button = QPushButton()
        cart_button.setFixedSize(50, 50)
        cart_button.setStyleSheet(self.styles[6])

        cart_button.clicked.connect(self.show_cart)

        # 직원호출
        # self.call_button = QPushButton("직원호출")
        # self.call_button.setFixedSize(120, 50)
        # self.call_button.setStyleSheet(self.styles[7])
        # self.call_button.clicked.connect(self.show_staff_call_items)

        bottom_layout.addWidget(history_button)  # 주문내역 버튼 추가
        bottom_layout.addStretch()
        bottom_layout.addWidget(cart_button)
        # bottom_layout.addWidget(self.call_button)
        bottom_panel.setLayout(bottom_layout)

        # 오른쪽 패널에 스택과 하단 버튼 추가
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.stack)
        right_layout.addWidget(bottom_panel)
        right_panel.setLayout(right_layout)

        # 메인 레이아웃에 패널 추가
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)

        # 기본 카테고리 설정
        self.show_category(self.last_category)

        # 창 크기 설정
        self.setGeometry(100, 100, 1200, 800)

    def create_menu_item(self, item_data):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # 바깥쪽 프레임 (회색 테두리)
        outer_frame = QFrame()
        outer_frame.setFixedSize(220, 220)
        outer_frame.setStyleSheet(self.styles[0])

        # 안쪽 프레임 (흰색 배경)
        inner_frame = QFrame(outer_frame)
        inner_frame.setFixedSize(200, 200)
        inner_frame.move(10, 10)
        inner_frame.setStyleSheet(self.styles[1])

        # 이미지 라벨을 클릭 가능하게 만들기
        image_label = ClickableLabel(inner_frame)
        image_label.setFixedSize(180, 180)
        image_label.move(10, 10)

        try:
            pixmap = QPixmap(item_data["image"])
            scaled_pixmap = pixmap.scaled(
                180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignCenter)
        except:
            image_label.setText("이미지 없음")
            image_label.setAlignment(Qt.AlignCenter)

        # 이미지 클릭 시 장바구니에 추가하는 기능 연결
        # image_label.clicked.connect(
        #     lambda: self.add_to_cart(
        #         item_data["name"],
        #         int(item_data["price"].replace(",", "").replace("원", "")),
        #     )
        # )

        # 메뉴명
        name_label = QLabel(item_data["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setStyleSheet("QLabel {color: white;margin-top: 15px;}")
        name_label.setAlignment(Qt.AlignCenter)

        # 가격
        price_label = QLabel(item_data["price"])
        price_label.setFont(QFont("Arial", 12))
        price_label.setStyleSheet("QLabel {color: white;margin-top: 5px;}")
        price_label.setAlignment(Qt.AlignCenter)

        # 담기 버튼 추가
        add_button = QPushButton("담기")
        add_button.setStyleSheet(self.styles[2])
        add_button.clicked.connect(lambda: self.add_to_cart(item_data["name"]))

        layout.addWidget(outer_frame)
        layout.addWidget(name_label)
        layout.addWidget(price_label)
        layout.addWidget(add_button)  # 담기 버튼 추가
        layout.setSpacing(0)

        widget.setLayout(layout)
        return widget

    def add_to_cart(self, item_name):
        # 장바구니에 아이템 추가
        if item_name in self.cart_items:
            quantity = self.cart_items[item_name]
            self.cart_items[item_name] = quantity + 1
        else:
            self.cart_items[item_name] = 1
        self.update_ui()
        # 알림 메시지 표시
        # msg = QMessageBox()
        # msg.setIcon(QMessageBox.Information)
        # msg.setText(f"{item_name}이(가) 장바구니에 추가되었습니다.")
        # msg.setWindowTitle("장바구니 알림")
        # msg.exec_()

    def show_order_history(self):
        # 주문 내역 대화상자 표시
        if self.order_history:
            history_dialog = OrderHistoryDialog(self.order_history, self)
            history_dialog.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("주문 내역이 없습니다.")
            msg.setWindowTitle("알림")
            msg.exec_()

    def show_cart(self):
        # 장바구니 대화상자 표시
        if self.cart_items:
            self.cart_ui = CartDialog(self.cart_items, self)
            self.cart_ui.order_confirmed.connect(self.process_order)
            self.cart_ui.show()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("장바구니가 비어 있습니다.")
            msg.setWindowTitle("알림")
            msg.exec_()

    def response_callback(self, future):
        db_conn = db()
        print("response_callback start")
        try:
            response = future.result()
            # self.get_logger().info(
            #     "Service Response: 예상 준비 시간 %d분" % response.count_time
            # )
            # db_conn.log()

        except Exception as e:
            # db_conn.log(, 2)

            # 주문 실패 메시지
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("[테이블 %s] 주문 실패" % sys.argv[1])
            msg.setWindowTitle("주문 실패")
            msg.exec_()

        finally:

            # 주문 완료 메시지
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                "[테이블 %s] 예상 준비 시간 %d분" % (sys.argv[1], response.minute)
            )
            msg.setWindowTitle("주문 완료")
            msg.exec_()

            # future 객체 제거
            if future in self.futures:
                self.futures.remove(future)
        print("response_callback end")

    def process_order(self, cart_items, table_node: TableNode):
        db_conn = db()
        print("process_order start")
        # 주문 처리 및 주문 내역 저장
        # 현재 시간과 함께 주문 내역 저장
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.order_history.append((current_time, cart_items))

        # 주문 서비스 클라이언트 여기
        # print(cart_items)
        # print(table_node.menu_order_client)

        while not table_node.menu_order_client.wait_for_service(timeout_sec=1):
            # self.get_logger().warning("The menu_order service not available.")
            db_conn.log("The menu_order service not available.", 1)

        if table_node.menu_order_client.service_is_ready():
            #     self.send_request()

            # # Service: Client ; Menu 콜백함수 (메뉴 수량 전달)
            # def send_request(self):
            print("send_request start")
            service_request = MenuOrder.Request()
            # 주문한 메뉴 개수 변수에 저장
            print(str({"table": table_node.args[0], "menu": cart_items}))

            # service_request.count_menu = random.randint(
            #     1, 4
            # )  # 서비스 요청값 ; 메뉴 개수 임의 선택
            service_request.data = str(
                {"table": table_node.args[0], "menu": cart_items}
            )
            future = table_node.menu_order_client.call_async(service_request)
            table_node.futures.append(future)
            future.add_done_callback(self.response_callback)
            print("send_request end")

        # 주문 완료 메시지
        # msg = QMessageBox()
        # msg.setIcon(QMessageBox.Information)
        # msg.setText("주문이 완료되었습니다.")
        # msg.setWindowTitle("주문 완료")
        # msg.exec_()

        # 장바구니 초기화
        self.cart_items = {}
        self.update_ui()

    def show_category(self, category):
        self.last_category = category
        # 직원호출 상태 초기화
        self.staff_call_active = False
        # self.call_button.setStyleSheet(self.styles[8])

        # 버튼 스타일 업데이트
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.setStyleSheet(self.styles[9])
            else:
                btn.setStyleSheet(self.styles[10])

        # 해당 카테고리 페이지 표시
        category_index = list(self.menu_data.keys()).index(category)
        self.stack.setCurrentIndex(category_index)

    def show_staff_call_items(self):
        # 직원호출 버튼 클릭시 물/물티슈 페이지 표시
        # 직원호출 상태 토글
        self.staff_call_active = not self.staff_call_active

        # 직원호출 버튼 스타일 업데이트
        # if self.staff_call_active:
        #     self.call_button.setStyleSheet(self.styles[11])
        # else:
        #     self.call_button.setStyleSheet(self.styles[12])

        # '직원호출' 카테고리의 인덱스를 찾아서 해당 페이지 표시
        category_index = list(self.menu_data.keys()).index("직원호출")
        self.stack.setCurrentIndex(category_index)

        # 모든 카테고리 버튼 스타일 초기화
        for btn in self.category_buttons.values():
            btn.setStyleSheet(self.styles[13])


class FireAlertWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.styles = [
            "background-color: #808080; color: white;",
            "background-color: black;" "color: red;",
        ]

        # 창 설정
        self.setWindowTitle("경고")
        self.setGeometry(100, 100, 400, 200)  # 창 크기와 위치 설정
        self.setStyleSheet(self.styles[0])  # 배경색을 검은색으로 설정

        # "화재발생" 라벨 설정
        label = QLabel("화재발생", self)
        label.setAlignment(Qt.AlignCenter)  # 텍스트를 중앙 정렬
        label.setFont(QFont("Arial", 24, QFont.Bold))  # 글꼴, 크기, 굵기 설정
        label.setStyleSheet(self.styles[1])  # 글자 색을 빨간색으로 설정

        # 레이아웃 설정
        self.setCentralWidget(label)


class MainWindow(QMainWindow):
    global thread_table_node

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("주문 관리 시스템 테이블" + str(sys.argv[1]))
        self.stack_widget = QStackedWidget()
        self.setCentralWidget(self.stack_widget)

        self.p1 = KoreanRestaurantGUI()
        self.stack_widget.addWidget(self.p1)

        self.p2 = FireAlertWindow()
        self.stack_widget.addWidget(self.p2)

        thread_table_node.set_window_index.connect(self.stack_widget.setCurrentIndex)


def main(argv=None):
    # rclpy.init()

    # thread = threading.Thread(target=thread_fire)
    # thread.start()

    app = QApplication(sys.argv)
    window = MainWindow()

    window.show()
    ret = app.exec_()

    rclpy.shutdown()

    exit(ret)


if __name__ == "__main__":
    main(sys.argv)
