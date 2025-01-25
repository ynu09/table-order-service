import json
import re

import rclpy
import rclpy.time
from geometry_msgs.msg import Point, Quaternion
from nav2_msgs.action import NavigateToPose
from nav2_msgs.srv import SetInitialPose
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from rclpy.action import ActionClient
from rclpy.action.client import GoalStatus  # 정의된 상태값 상수들 있음
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from rclpy.time import Time  # 상단에 import 추가
from std_msgs.msg import String
from tf2_ros import *
from tf2_ros import (
    Buffer,
    ConnectivityException,
    ExtrapolationException,
    LookupException,
    TransformListener,
)

from table_msgs.srv import MenuOrder
from .db import db


class RobotNavi(Node):

    def __init__(self):
        rclpy.init()
        super().__init__("robot_navi")  # 노드명

        self.num = 9
        self.callback_group = ReentrantCallbackGroup()

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.init_pose = [-2.0, -0.5, 0.0, 1.0]  # pose:x,y orient:z,w

        self.goal_poses = [
            [1.2, 0.8],  # table1
            [1.2, -0.2],  # table2
            [1.2, -1.5],  # table3
            [0.0, 0.8],  # table4
            [0.0, -0.2],  # table5
            [0.0, -1.5],  # table6
            [-1.2, 0.9],  # table7
            [-1.2, -0.2],  # table8
            [-1.2, -1.5],  # table9
            [-2.0, -0.5],  # kitchen
        ]

        # Navigation clients (서비스)
        self.set_initial_pose_service_client = self.create_client(
            SetInitialPose,
            "/set_initial_pose",
            qos_profile=QoSProfile(
                reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
                # reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
                history=QoSHistoryPolicy.KEEP_LAST,  # 최신 값만 저장
                # history=QoSHistoryPolicy.KEEP_ALL,    #전부 저장해놓고 나중에라도 다시 전송
                depth=100,
                # durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
                durability=QoSDurabilityPolicy.VOLATILE,  # 구독 전 데이터 유지 안함
            ),
        )

        # 액션
        self.navigate_to_pose_action_client = ActionClient(
            self,
            NavigateToPose,
            "navigate_to_pose",
            # goal_service_qos_profile=QoSProfile(
            #     # reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
            #     reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
            #     # history=QoSHistoryPolicy.KEEP_LAST,   #최신 값만 저장
            #     history=QoSHistoryPolicy.KEEP_ALL,  # 전부 저장해놓고 나중에라도 다시 전송
            #     # depth=5,
            #     durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
            #     # durability=QoSDurabilityPolicy.VOLATILE, # 구독 전 데이터 유지 안함
            # ),
            # feedback_sub_qos_profile=QoSProfile(
            #     reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
            #     # reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
            #     history=QoSHistoryPolicy.KEEP_LAST,  # 최신 값만 저장
            #     # history=QoSHistoryPolicy.KEEP_ALL,    #전부 저장해놓고 나중에라도 다시 전송
            #     depth=100,
            #     # durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
            #     durability=QoSDurabilityPolicy.VOLATILE,  # 구독 전 데이터 유지 안함
            # ),
            # result_service_qos_profile=QoSProfile(
            #     # reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
            #     reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
            #     # history=QoSHistoryPolicy.KEEP_LAST,   #최신 값만 저장
            #     history=QoSHistoryPolicy.KEEP_ALL,  # 전부 저장해놓고 나중에라도 다시 전송
            #     # depth=5,
            #     durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
            #     # durability=QoSDurabilityPolicy.VOLATILE, # 구독 전 데이터 유지 안함
            # ),
        )

        self.fire_alert_publisher = self.create_publisher(
            String,
            "fire",
            qos_profile=QoSProfile(
                reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
                # reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
                history=QoSHistoryPolicy.KEEP_LAST,  # 최신 값만 저장
                # history=QoSHistoryPolicy.KEEP_ALL,    #전부 저장해놓고 나중에라도 다시 전송
                depth=100,
                # durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
                durability=QoSDurabilityPolicy.VOLATILE,  # 구독 전 데이터 유지 안함
            ),
        )

        # Topic2: Subscriber ; Battery 선언
        # self.no_battery_subscriber = self.create_subscription(
        #     String,
        #     "no_battery",
        #     self.get_no_battery,
        #     100,
        #     # callback_group=self.callback_group,
        # )

        # Service: Server ; Menu 선언
        # self.menu_order_server = self.create_service(
        #     MenuOrder,  # srv 타입
        #     "menu_order",  # 서비스명
        #     self.get_menu_order,  # 콜백함수 (서비스 클라이언트-서비스 요청 있을 때마다)
        #     callback_group=self.callback_group,  # 멀티 스레드 병렬 콜백함수 실행
        #     qos_profile=QoSProfile(
        #         # reliability=QoSReliabilityPolicy.BEST_EFFORT,  # 속도 중점
        #         reliability=QoSReliabilityPolicy.RELIABLE,  # 유실 방지
        #         # history=QoSHistoryPolicy.KEEP_LAST,  # 최신 값만 저장
        #         history=QoSHistoryPolicy.KEEP_ALL,  # 전부 저장해놓고 나중에라도 다시 전송
        #         # depth=5,
        #         durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,  # 구독 전 메세지 유지
        #         # durability=QoSDurabilityPolicy.VOLATILE, # 구독 전 데이터 유지 안함
        #     ),
        # )
        print("robot node init end")

    # Service: Server ; Menu 콜백함수 (준비 예상시간)
    def get_menu_order(self, request, response):
        print("get_menu_order start")
        # request
        self.data = json.loads(str(request.data).replace("'", '"'))
        print(self.data)

        # response
        self.table_num = int(self.data["table"])
        self.count, self.eta = self.calculate_predict_time(self.data["menu"])
        # 연산 결과값 저장
        response.minute = self.eta

        # 화면 표시
        self.get_logger().info(
            "[테이블 %d] : 메뉴 %d개 준비시간 %d분 정도 소요됩니다."
            % (self.table_num, self.count, self.eta)
        )
        print("get_menu_order end")
        db_conn = db()
        db_conn.add_order(self.table_num, self.data["menu"])
        return response

    # 메뉴 준비 예상시간 계산 (개당 5분)
    def calculate_predict_time(self, menu):
        ret = 0
        print("cal:", menu)
        for _, count in menu.items():

            ret += count
        return ret, ret * 5

    # 초기 입력값 주기
    def set_initial_pose(self, x, y, z, w):
        db_conn = db()
        req = SetInitialPose.Request()
        req.pose.header.frame_id = "map"
        req.pose.pose.pose.position = Point(x=x, y=y, z=0.0)
        req.pose.pose.pose.orientation = Quaternion(x=0.0, y=0.0, z=z, w=w)
        req.pose.pose.covariance = [
            0.1,
            0.0,
            0.0,
            0.0,
            0.0,
            0.1,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.1,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.01,
        ]

        future = self.set_initial_pose_service_client.call_async(req)

        # 초기 위치 설정 성공 여부
        if future.result() is not None:
            message = "초기 위치 설정 성공"
            db_conn.log(message)

        return future.result()

    def navigate_to_pose_send_goal(self, i):
        db_conn = db()
        wait_count = 1
        while not self.navigate_to_pose_action_client.wait_for_server(timeout_sec=0.1):
            if wait_count > 3:
                message = "배송요청 서버에 접속할 수 없습니다."
                # self.gui.textBrowser.append(message)
                db_conn.log(message, 1)
                return False
            wait_count += 1

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.pose.position.x = self.goal_poses[i][0]
        goal_msg.pose.pose.position.y = self.goal_poses[i][1]
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0

        self.send_goal_future = self.navigate_to_pose_action_client.send_goal_async(
            goal_msg, feedback_callback=self.navigate_to_pose_action_feedback
        )
        self.send_goal_future.add_done_callback(self.navigate_to_pose_action_goal)

        return True

    def navigate_to_pose_action_goal(self, future):
        db_conn = db()
        goal_handle = future.result()
        if not goal_handle.accepted:
            message = "갈 수 없는 목적지입니다."
            # self.gui.textBrowser.append(message)
            db_conn.log(message, 1)
            return

        message = "목적지가 수락되었습니다."
        # self.gui.textBrowser.append(message)
        db_conn.log(message)
        self.action_result_future = goal_handle.get_result_async()
        self.action_result_future.add_done_callback(self.navigate_to_pose_action_result)

    def navigate_to_pose_action_feedback(self, feedback_msg):
        db_conn = db()
        action_feedback = str(feedback_msg.feedback)
        # self.get_logger().info("Action feedback: {0}".format(action_feedback))
        # Regular expressions to extract the required values
        estimated_time_pattern = r"estimated_time_remaining=builtin_interfaces\.msg\.Duration\(sec=(\d+), nanosec=(\d+)\)"
        current_pose_pattern = r"current_pose=geometry_msgs\.msg\.PoseStamped\(.*?position=geometry_msgs\.msg\.Point\(x=([-+]?[0-9]*\.?[0-9]+), y=([-+]?[0-9]*\.?[0-9]+), z=([-+]?[0-9]*\.?[0-9]+)\)"
        distance_remaining_pattern = r"distance_remaining=([-+]?[0-9]*\.?[0-9]+)"
        number_of_recoveries_pattern = r"number_of_recoveries=(\d+)"

        # Extract estimated_time_remaining
        estimated_time_match = re.search(estimated_time_pattern, action_feedback)
        if estimated_time_match:
            estimated_time_sec = int(estimated_time_match.group(1))
            estimated_time_nsec = int(estimated_time_match.group(2))
        else:
            estimated_time_sec = estimated_time_nsec = None

        # Extract current_pose
        current_pose_match = re.search(current_pose_pattern, action_feedback, re.DOTALL)
        if current_pose_match:
            current_pose_x = float(current_pose_match.group(1))
            current_pose_y = float(current_pose_match.group(2))
            current_pose_z = float(current_pose_match.group(3))
        else:
            current_pose_x = current_pose_y = current_pose_z = None

        # Extract distance_remaining
        distance_remaining_match = re.search(
            distance_remaining_pattern, action_feedback
        )
        distance_remaining = (
            float(distance_remaining_match.group(1))
            if distance_remaining_match
            else None
        )

        # Extract number_of_recoveries
        number_of_recoveries_match = re.search(
            number_of_recoveries_pattern, action_feedback
        )
        number_of_recoveries = (
            int(number_of_recoveries_match.group(1))
            if number_of_recoveries_match
            else None
        )

        # Output results
        db_conn.log(
            f"이동중: 현재위치:({current_pose_x:.2f}, {current_pose_y:.2}, {current_pose_z:.2}), 남은시간:{estimated_time_sec}초, 남은거리:{distance_remaining:.2}, 복구행동:{number_of_recoveries}",
            3,
        )

    def navigate_to_pose_action_result(self, future):
        db_conn = db()
        # GoalStatus
        # STATUS_UNKNOWN (0): 알 수 없는 상태
        # STATUS_ACCEPTED (1): 작업이 수락됨
        # STATUS_EXECUTING (2): 실행 중
        # STATUS_SUCCEEDED (4): 작업이 성공적으로 완료됨
        # STATUS_ABORTED (5): 작업이 중단됨
        # STATUS_CANCELED (6): 작업이 취소됨

        # 액션 목표 달성 시
        action_status = future.result().status
        if action_status == GoalStatus.STATUS_SUCCEEDED:
            message = "목적지에 도착했습니다."
            db_conn.log(message)

            # 도착 위치 출력
            try:
                # 현재 로봇의 위치 얻기
                transform = self.tf_buffer.lookup_transform(
                    "map",
                    "base_link",
                    Time().to_msg(),
                    rclpy.duration.Duration(seconds=1.0),
                )

                current_x = transform.transform.translation.x
                current_y = transform.transform.translation.y

                arrival_message = f"도착 좌표 x: {current_x:.2f}, y: {current_y:.2f}"
                db_conn.log(arrival_message, 3)

                # 가장 가까운 테이블 찾기
                min_distance = float("inf")
                closest_table = -1

                for i, pos in enumerate(self.goal_poses):
                    # 유클리드 거리 계산
                    distance = (
                        (current_x - pos[0]) ** 2 + (current_y - pos[1]) ** 2
                    ) ** 0.5

                    if distance < min_distance:
                        min_distance = distance
                        closest_table = i

                # 일정 거리 이내(예: 0.5m)에 있는 경우에만 테이블 도착 메시지 출력
                if min_distance <= 0.5:  # 거리 임계값 (미터 단위)
                    if closest_table + 1 == 10:
                        table_message = f"주방에 도착했습니다."
                    else:
                        table_message = f"{closest_table + 1}번 테이블에 도착했습니다."
                    # self.gui.textBrowser.append(table_message)
                    db_conn.log(table_message)

            except (
                tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException,
            ) as e:
                db_conn.log(f"목적지에 갈 수 없습니다. {str(e)}", 1)
        else:
            message = f"배송을 실패했습니다.({action_status})"
            db_conn.log(message, 1)
            # self.gui.textBrowser.append(message)
