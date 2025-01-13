import sys
import threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile


from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from std_msgs.msg import String

class Publisher(Node):
    def __init__(self):
        super().__init__('node')

        qos_profile = QoSProfile(depth=5)
        self.message_publisher = self.create_publisher(String, 'message', qos_profile)

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
        self.publish_message()
        self.lineEdit.clear()


    def publish_message(self):
        msg = String()
        msg.data = self.message
        self.message_publisher.publish(msg)
        self.get_logger().info(f'Published message: {self.message}')


    def run(self):
        self.ros_thread = threading.Thread(target=self.run_ros, daemon=True)
        self.ros_thread.start()
        
        self.window.show()
        sys.exit(self.app.exec_())
        
    def run_ros(self):
        rclpy.spin(self)
        
        
def main():
    rclpy.init()
    node = Publisher()
    node.run()
    
    try:
        rclpy.shutdown()
    finally:
        node.destroy_node()
    
if __name__ == '__main__':
    main()

