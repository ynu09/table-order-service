# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import random

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
import sys
from std_msgs.msg import String

from table_msgs.srv import MenuOrder


class TableNode(Node):
    def __init__(self):
        rclpy.init()
        super().__init__("table_node")
        self.args = sys.argv[1:]
        self.callback_group = ReentrantCallbackGroup()
        self.futures = []

        self.subscription = self.create_subscription(
            String,
            "fire",
            self.listener_callback,
            10,
            # qos_profile=QoSProfile(
            #     reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
            #     # reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
            #     history=QoSHistoryPolicy.KEEP_LAST,  # 최신 값만 저장
            #     # history=QoSHistoryPolicy.KEEP_ALL,    #전부 저장해놓고 나중에라도 다시 전송
            #     depth=100,
            #     # durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
            #     durability=QoSDurabilityPolicy.VOLATILE,  # 구독 전 데이터 유지 안함
            # ),
            # callback_group=self.callback_group,
        )
        self.subscription  # prevent unused variable warning
        self.recv = ""

        # Service: Client ; Menu 선언
        self.menu_order_client = self.create_client(
            MenuOrder,
            "menu_order",
            callback_group=self.callback_group,
            # qos_profile=QoSProfile(
            #     # reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
            #     reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
            #     # history=QoSHistoryPolicy.KEEP_LAST,  # 최신 값만 저장
            #     history=QoSHistoryPolicy.KEEP_ALL,  # 전부 저장해놓고 나중에라도 다시 전송
            #     # depth=100,
            #     durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
            #     # durability=QoSDurabilityPolicy.VOLATILE, # 구독 전 데이터 유지 안함
            # ),
        )

        # Wait for a service server
        while not self.menu_order_client.wait_for_service(timeout_sec=1):
            self.get_logger().warning("The menu_order service not available.")

        # 5초마다 timer_callback 호출 ; 주기적으로 서비스 요청을 보내기 위한 타이머
        # self.timer = self.create_timer(
        #     5.0, self.timer_callback, callback_group=self.callback_group  # 5초마다 요청
        # )

    def timer_callback(self):
        # 타이머에서 서비스 요청 보내기 ; 서비스가 준비되었는지 확인
        if self.menu_order_client.service_is_ready():
            self.send_request()

    def listener_callback(self, msg):
        self.recv = ""
        self.get_logger().info("recieved: [%s]" % msg.data)
        self.recv = msg.data

    # Service: Client ; Menu 콜백함수 (메뉴 수량 전달)
    def send_request(self):
        print("send_request start")
        service_request = MenuOrder.Request()
        # 주문한 메뉴 개수 변수에 저장
        service_request.count_menu = random.randint(
            1, 4
        )  # 서비스 요청값 ; 메뉴 개수 임의 선택
        future = self.menu_order_client.call_async(service_request)
        self.futures.append(future)
        future.add_done_callback(self.response_callback)
        print("send_request end")

    def response_callback(self, future):

        print("response_callback start")
        try:
            response = future.result()
            self.get_logger().info(
                "Service Response: 예상 준비 시간 %d분" % response.count_time
            )
        except Exception as e:
            self.get_logger().error("Service call failed: %r" % (e,))
        finally:
            # future 객체 제거
            if future in self.futures:
                self.futures.remove(future)
        print("response_callback end")

    def destroy_node(self):
        # 모든 pending futures 취소
        for future in self.futures:
            if not future.done():
                future.cancel()
        self.futures.clear()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = TableNode()
    rclpy.spin(minimal_subscriber)

    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
