import sys
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class NODE(Node):
    def __init__(self, runner):
        super().__init__('node')
        self.runner = runner

    def input_gui(self):
        self.gui = self.runner.gui

        self.subscription = self.create_subscription(
            String,
            'message',
            self.subscription_callback,
            10
            )

    def subscription_callback(self, msg):
        message = msg.data
        self.gui.textBrowser.append(message)
        self.get_logger().info(f'message: {message}')




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
        self.window.resize(375, 310)
        self.centralwidget = QWidget(self.window)
        self.centralwidget.setObjectName(u"centralwidget")
        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setGeometry(QRect(60, 90, 256, 192))
        self.window.setCentralWidget(self.centralwidget)


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