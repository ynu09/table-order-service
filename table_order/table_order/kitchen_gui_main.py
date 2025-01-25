import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .kitchen_gui_order import MainPage
from .kitchen_gui_navi import SecondPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("주문 관리 시스템")
        self.setGeometry(100, 100, 800, 800)

        # 스택 위젯 생성
        self.stack_widget = QStackedWidget()
        self.setCentralWidget(self.stack_widget)

        # 첫 번째 페이지 (메인 페이지)
        self.main_page = MainPage()
        self.stack_widget.addWidget(self.main_page)

        # 두 번째 페이지
        self.second_page = SecondPage(self)
        self.stack_widget.addWidget(self.second_page)


def main(argv=None):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)
