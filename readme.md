## 테이블 오더 & 로봇 내비게이션 시스템

### 기록

| 기간 | 내용 | 폴더 |
| --- | --- | --- |
| 2024.11.12 ~ 2024.11.18 | 서비스(음식배달,정찰경찰 등) 로봇 및 관제 시스템 개발 | table_msgs, table_order |

### 기술 스택

| 분류 | 기술 |
| --- | --- |
| 개발 환경 | Ubuntu 22.04 |
| 개발 언어 | Python |
| 통신 프로토콜 | ROS2 |
| UI | PyQt5 |
| 데이터베이스 | SQLite3 |
| 디자인 및 프로토타이핑 도구 | Figma |
| 시뮬레이션 및 시각화 도구 | gazebo, rviz |

### 결과물

[그룹E-2_2주차_주행-1_산출물.pdf](https://github.com/user-attachments/files/18392405/E-2_2._.-1_.pdf)

### 실행 방법

<aside>

1. Install TurtleBot3 Packages
    
    [https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/](https://emanual.robotis.com/docs/en/platform/turtlebot3/quick-start/)
    
2. Install Simulation Package
    
    [https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/#install-simulation-package](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/#install-simulation-package)
    
</aside>

```python
# gazebo
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

# navi
ros2 launch turtlebot3_navigation2 navigation2.launch.py

# kitchen 
ros2 run table_order kitchen

# table
ros2 run table_order table 

# navigation_robot
ros2 run table_order robot
