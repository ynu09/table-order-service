"""
kitchen 관리자 페이지 ; 확인완
"""

import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from collections import deque
from PyQt5.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
)
from PyQt5.QtCore import pyqtSignal


class OrderBox(QGroupBox):
    delete_requested = pyqtSignal(object)  # 삭제 요청 시그널

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.orders = []  # 주문 목록 저장
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # 스크롤 영역에 들어갈 위젯
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # 삭제 버튼
        delete_btn = QPushButton("주문 완료")
        delete_btn.clicked.connect(self.request_delete)
        layout.addWidget(delete_btn)

        self.setLayout(layout)
        self.setMinimumSize(150, 200)  # 최소 크기 설정

    def add_order(self, order_text):
        """주문 추가"""
        self.orders.append(order_text)
        order_label = QLabel(order_text)
        self.content_layout.addWidget(order_label)

    def request_delete(self):
        """주문 완료 버튼 클릭 시 삭제 요청 시그널 발생"""
        self.delete_requested.emit(self)

    def get_orders(self):
        """현재 주문 목록 반환"""
        return self.orders


class MenuManager:
    def __init__(self):
        self.menu_file = "src/table_order/table_order/menus.json"
        self.load_menu()

    def load_menu(self):
        """
        이후에 json 파일을 데이터베이스로 변경
        """
        try:
            with open(self.menu_file, "r", encoding="utf-8") as f:
                self.menu_data = json.load(f)
        except FileNotFoundError:
            self.menu_data = {
                "면_짜장면": 8000,
                "면_짬뽕": 8000,
                "면_우동": 1000,
                "밥_짜장밥": 8000,
                "밥_짬뽕밥": 3000,
                "밥_볶음밥": 8000,
                "요리_탕수육": 8000,
                "요리_깐풍기": 8000,
                "요리_라조육": 8000,
                "음료_코카콜라": 2000,
                "음료_사이다": 2000,
                "음료_제로콜라": 2500,
                "직원호출_물": 0,
                "직원호출_물티슈": 0,
                "직원호출_휴지": 0,
            }
            self.save_menu()

    def save_menu(self):
        with open(self.menu_file, "w", encoding="utf-8") as f:
            json.dump(self.menu_data, f, ensure_ascii=False, indent=2)


class SettingsDialog(QDialog):
    def __init__(self, menu_manager, parent=None):
        super().__init__(parent)
        self.menu_manager = menu_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("설정")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()

        # 탭 위젯 생성
        tab_widget = QTabWidget()

        # 메뉴 관리 탭
        menu_tab = QWidget()
        menu_layout = QHBoxLayout()

        # 왼쪽: 카테고리 목록
        category_group = QGroupBox("카테고리")
        category_layout = QVBoxLayout()

        self.category_list = QListWidget()
        self.category_list.addItems(self.menu_manager.menu_data.keys())
        self.category_list.currentItemChanged.connect(self.on_category_changed)

        category_layout.addWidget(self.category_list)

        # 카테고리 관리 버튼
        category_btn_layout = QHBoxLayout()
        add_category_btn = QPushButton("카테고리 추가")
        del_category_btn = QPushButton("카테고리 삭제")
        add_category_btn.clicked.connect(self.add_category)
        del_category_btn.clicked.connect(self.delete_category)

        category_btn_layout.addWidget(add_category_btn)
        category_btn_layout.addWidget(del_category_btn)
        category_layout.addLayout(category_btn_layout)

        category_group.setLayout(category_layout)

        # 오른쪽: 메뉴 목록
        menu_group = QGroupBox("메뉴")
        menu_right_layout = QVBoxLayout()

        self.menu_list = QListWidget()
        menu_right_layout.addWidget(self.menu_list)

        # 메뉴 관리 버튼
        menu_btn_layout = QHBoxLayout()
        add_menu_btn = QPushButton("메뉴 추가")
        edit_menu_btn = QPushButton("메뉴 수정")
        del_menu_btn = QPushButton("메뉴 삭제")

        add_menu_btn.clicked.connect(self.add_menu)
        edit_menu_btn.clicked.connect(self.edit_menu)
        del_menu_btn.clicked.connect(self.delete_menu)

        menu_btn_layout.addWidget(add_menu_btn)
        menu_btn_layout.addWidget(edit_menu_btn)
        menu_btn_layout.addWidget(del_menu_btn)

        menu_right_layout.addLayout(menu_btn_layout)
        menu_group.setLayout(menu_right_layout)

        # 레이아웃 구성
        menu_layout.addWidget(category_group)
        menu_layout.addWidget(menu_group)
        menu_tab.setLayout(menu_layout)

        # 탭 추가
        tab_widget.addTab(menu_tab, "메뉴 관리")

        # 저장 버튼
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_changes)

        layout.addWidget(tab_widget)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        # 초기 메뉴 로드
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)

    def on_category_changed(self, current, previous):
        self.menu_list.clear()
        if current:
            category = current.text()
            self.menu_list.addItems(self.menu_manager.menu_data[category])

    def add_category(self):
        category, ok = QInputDialog.getText(
            self, "카테고리 추가", "카테고리 이름을 입력하세요:"
        )
        if ok and category:
            if category not in self.menu_manager.menu_data:
                self.menu_manager.menu_data[category] = []
                self.category_list.addItem(category)
            else:
                QMessageBox.warning(self, "경고", "이미 존재하는 카테고리입니다.")

    def delete_category(self):
        current = self.category_list.currentItem()
        if current:
            reply = QMessageBox.question(
                self,
                "확인",
                f'"{current.text()}" 카테고리를 삭제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                category = current.text()
                del self.menu_manager.menu_data[category]
                self.category_list.takeItem(self.category_list.row(current))

    def add_menu(self):
        current_category = self.category_list.currentItem()
        if current_category:
            menu_name, ok = QInputDialog.getText(
                self, "메뉴 추가", "메뉴 이름을 입력하세요:"
            )
            if ok and menu_name:
                category = current_category.text()
                if menu_name not in self.menu_manager.menu_data[category]:
                    self.menu_manager.menu_data[category].append(menu_name)
                    self.menu_list.addItem(menu_name)
                else:
                    QMessageBox.warning(self, "경고", "이미 존재하는 메뉴입니다.")

    def edit_menu(self):
        current_category = self.category_list.currentItem()
        current_menu = self.menu_list.currentItem()
        if current_category and current_menu:
            old_name = current_menu.text()
            new_name, ok = QInputDialog.getText(
                self,
                "메뉴 수정",
                "새로운 메뉴 이름을 입력하세요:",
                QLineEdit.Normal,
                old_name,
            )
            if ok and new_name:
                category = current_category.text()
                idx = self.menu_manager.menu_data[category].index(old_name)
                self.menu_manager.menu_data[category][idx] = new_name
                current_menu.setText(new_name)

    def delete_menu(self):
        current_category = self.category_list.currentItem()
        current_menu = self.menu_list.currentItem()
        if current_category and current_menu:
            reply = QMessageBox.question(
                self,
                "확인",
                f'"{current_menu.text()}" 메뉴를 삭제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                category = current_category.text()
                menu_name = current_menu.text()
                self.menu_manager.menu_data[category].remove(menu_name)
                self.menu_list.takeItem(self.menu_list.row(current_menu))

    def save_changes(self):
        self.menu_manager.save_menu()
        QMessageBox.information(self, "알림", "변경사항이 저장되었습니다.")
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.menu_manager = MenuManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("주문 관리 시스템")
        self.setGeometry(100, 100, 800, 600)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)

        # 상단 설정 버튼
        settings_layout = QHBoxLayout()
        settings_btn = QPushButton("⚙ 설정")
        settings_btn.clicked.connect(self.show_settings)
        settings_layout.addWidget(settings_btn)
        settings_layout.addStretch()
        main_layout.addLayout(settings_layout)

        # 주문 박스들을 담을 그리드 레이아웃
        self.grid_layout = QGridLayout()

        # 8개의 OrderBox 생성
        self.order_boxes = []
        for i in range(8):
            box = OrderBox(f"주문번호{i+1}")
            box.delete_requested.connect(self.delete_order_box)  # 삭제 시그널 연결
            self.order_boxes.append(box)
            self.grid_layout.addWidget(box, i // 4, i % 4)

        main_layout.addLayout(self.grid_layout)

        # 하단 로봇 호출 버튼
        robot_btn = QPushButton("로봇호출")
        robot_btn.setStyleSheet(
            """
            QPushButton {
                background-color: yellow;
                padding: 10px;
                font-weight: bold;
            }
        """
        )
        robot_btn.clicked.connect(self.call_robot)
        main_layout.addWidget(robot_btn)

    def show_settings(self):
        dialog = SettingsDialog(self.menu_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            # 설정이 변경되었을 때 필요한 업데이트 수행
            pass

    def delete_order_box(self, box):
        # 박스를 그리드 레이아웃에서 제거
        self.grid_layout.removeWidget(box)
        # 박스 숨기기
        box.hide()
        # 박스를 리스트에서 제거
        self.order_boxes.remove(box)
        # 박스 삭제
        box.deleteLater()

        # 나머지 박스들 재정렬
        self.rearrange_boxes()

    def rearrange_boxes(self):
        # 기존 박스들을 모두 그리드에서 제거
        for box in self.order_boxes:
            self.grid_layout.removeWidget(box)

        # 남아있는 박스들을 순서대로 재배치
        for i, box in enumerate(self.order_boxes):
            # 박스 제목 업데이트
            box.setTitle(f"주문번호{i+1}")
            # 새로운 위치에 박스 배치
            self.grid_layout.addWidget(box, i // 4, i % 4)

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("설정")
        dialog.setModal(True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("설정 내용을 여기에 추가하세요"))

        dialog.setLayout(layout)
        dialog.exec_()

    def call_robot(self):
        QMessageBox.information(self, "알림", "로봇을 호출했습니다.")

    def add_sample_orders(self):
        # 테스트용 샘플 주문 추가
        sample_orders = {
            0: ["짜장면 1", "짬뽕밥 1", "코카콜라 1"],
            1: ["탕수육 1", "볶음밥 2", "짬뽕 2"],
            2: ["깐풍기 2", "짜장면 1", "제로콜라 1"],
            3: ["파인빈 1", "파인빈 1", "사이다 2"],
            4: ["짬뽕 1", "짜장면 1", "라조육 2"],
            5: ["짬뽕 1", "짬뽕 1", "사이다 2"],
        }

        for box_idx, orders in sample_orders.items():
            for order in orders:
                if box_idx < len(
                    self.order_boxes
                ):  # 박스가 존재하는 경우에만 주문 추가
                    self.order_boxes[box_idx].add_order(order)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.add_sample_orders()
    sys.exit(app.exec_())
