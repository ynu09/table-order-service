import sys
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Subscriber(Node):
    def __init__(self):
        super().__init__('node')

        self.subscription = self.create_subscription(
            String,
            'message',
            self.subscription_callback,
            10
            )

        self.setupUi()
        
    def setupUi(self):
        self.app = QApplication()
        self.window = QMainWindow()

        if not self.window.objectName():
            self.window.setObjectName(u"MainWindow")
        self.window.resize(375, 310)
        self.centralwidget = QWidget(self.window)
        self.centralwidget.setObjectName(u"centralwidget")
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(60, 90, 256, 192))
        self.window.setCentralWidget(self.centralwidget)

    def subscription_callback(self, msg):
        message = msg.data
        self.textBrowser.append(message)
        self.get_logger().info(f'message: {message}')

    def run(self):
        self.ros_thread = threading.Thread(target=self.run_ros, daemon=True)
        self.ros_thread.start()

        self.window.show()
        sys.exit(self.app.exec_())

    def run_ros(self):
        rclpy.spin(self)
    

def main():
    rclpy.init()
    node = Subscriber()
    node.run()

    try:
        rclpy.shutdown()
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()