import sys
import threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from std_msgs.msg import String

class NODE(Node):
    def __init__(self, runner):
        super().__init__('node')
        self.runner = runner

    def input_gui(self):
        self.gui = self.runner.gui

        qos_profile = QoSProfile(depth=5)
        self.message_publisher = self.create_publisher(String, 'message', qos_profile)

    def publish_message(self, message):
        msg = String()
        msg.data = message
        self.message_publisher.publish(msg)
        self.get_logger().info(f'Published message: {message}')


# MainPage
class GUI():
    def __init__(self, runner):
        self.runner = runner
        self.node = self.runner.node
        self.setupUi()
        
    def setupUi(self):
        self.app = QApplication()
        self.window = QMainWindow()

        if not self.window.objectName():
            self.window.setObjectName(u"MainWindow")
        self.window.resize(361, 332)
        self.centralwidget = QWidget(self.window)
        self.centralwidget.setObjectName(u"centralwidget")
        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setGeometry(QRect(30, 20, 131, 31))
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(200, 20, 81, 31))
        self.pushButton.clicked.connect(self.button_clicked)
        self.window.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self.window)
        self.statusbar.setObjectName(u"statusbar")
        self.window.setStatusBar(self.statusbar)

    def button_clicked(self):
        self.message = self.lineEdit.text()
        self.node.publish_message(self.message)
        self.lineEdit.clear()

        
class RUNNER():
    def __init__(self):
        self.node = NODE(self)
        self.gui = GUI(self)
        self.node.input_gui()
        
    def run(self):
        self.ros_thread = threading.Thread(target=self.run_node, daemon=True)
        self.ros_thread.start()

        self.gui.window.show()
        sys.exit(self.gui.app.exec_())
        
    def run_node(self):
        try:
            rclpy.spin(self.node)
        finally:
            self.node.destroy_node()


def main():
    rclpy.init()
    runner = RUNNER()
    
    try:
        runner.run()
    finally:
        rclpy.shutdown()
    
    
if __name__ == '__main__':
    main()