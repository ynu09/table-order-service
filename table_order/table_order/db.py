import sqlite3
import json
import time


class db:
    def __init__(self) -> None:
        # 데이터베이스에 연결 (파일이 없으면 새로 생성)
        with open("src/table_order/table_order/sql.json") as sql_fp:
            self.sqls = json.load(sql_fp)
        self.conn = sqlite3.connect("src/table_order/table_order/db.db")

        # 커서 생성
        self.cursor = self.conn.cursor()

    def clear(self):
        # 모든 테이블 이름 조회
        tables = self.runsql("SELECT name FROM sqlite_master WHERE type='table'")

        # 각 테이블 삭제
        for table in tables:
            self.runsql(f"DROP TABLE {table[0]}")

    def init_scheme(self):
        # 테이블 생성 SQL 구문 실행
        self.runsql(self.sqls["foreign_keys_on"])
        self.runsql(self.sqls["create_table_table"])
        self.runsql(self.sqls["create_table_menu"])
        self.runsql(self.sqls["create_table_paymentstatus"])
        self.runsql(self.sqls["create_table_orders"])
        self.runsql(self.sqls["create_table_log"])

    def runsql(self, sql: str):
        try:
            # sql 실행
            self.cursor.execute(sql)

            # 변경사항 저장
            self.conn.commit()
            rows = self.cursor.fetchall()

        except Exception as e:
            print("[error][sql]", e)
            return None

        return rows

    # 마지막 주문번호 읽기
    def __get_max_order_num(self):
        max_order_num = self.runsql(self.sqls["max_order_num"])[0][0]
        max_order_num = int(max_order_num) if type(max_order_num) != type(None) else -1
        return max_order_num

    # 테이블 열 이름 읽기
    def get_column(self, table_name: str):
        return self.runsql(self.sqls["table_columns"].format(table_name))

    # 주문 추가
    def add_order(self, table_num, menus: list):
        # 이전 주문번호 + 1
        new_order_num = self.__get_max_order_num() + 1

        # 테이블 번호 설정
        self.runsql(
            self.sqls["add_table_num_to_orders"].format(new_order_num, table_num)
        )

        print(menus)
        # 주문 추가
        for name, count in menus.items():
            sql = self.sqls["oreder_new"].format(new_order_num, name=name, count=count)
            self.runsql(sql)

        # 결제테이블에 주문 추가
        self.runsql(self.sqls["add_orders_not_payed"].format(new_order_num))

        return new_order_num

    def get_menu(self):
        with open("src/table_order/table_order/menus.json") as menu_fp:
            menus = json.load(menu_fp)
        return menus

    # 메뉴 테이블 생성
    def init_menu(self):
        with open("src/table_order/table_order/menus.json") as menu_fp:
            menus = json.load(menu_fp)
        for name, price in menus.items():
            self.runsql(self.sqls["init_menu"].format(name, price))

    # 아직 나가지 않은 주문 확인
    def get_orders_not_finished(self):
        return self.runsql(self.sqls["orders_not_finished"])

    # 주문 나갔다고 설정
    def set_order_finished(self, orders_num):
        self.runsql(self.sqls["set_orders_finished"].format(orders_num))

    # 결제 안된 주문 확인
    def get_orders_not_payed(self):
        return self.runsql(self.sqls["orders_not_payed"])

    # 결제 했다고 설정
    def set_order_payed(self, orders_num):
        self.runsql(self.sqls["set_orders_payed"].format(orders_num))
        self.runsql(self.sqls["del_tableinfo"].format(orders_num))

    # 주문목록 창에서 필요한 데이터 확인
    def get_kitchen(self):
        return self.runsql(self.sqls["kitchen"])

    # 로그 추가
    def log(self, message: str, level: int = 0):
        # info : 0
        # Warning : 1
        # error : 2
        # debug : 3
        # fatal : 4
        self.runsql(self.sqls["log"].format(level, message))

    # 설정 레벨 이상 로그 읽기
    def read_log(self, level: int = 0):
        return self.runsql(self.sqls["read_log"].format(level))

    # 시간 범위 로그 읽기("2024-11-14 16:00:00", "2024-11-15 16:01:00")
    def read_log_from_to(self, from_, to_):
        return self.runsql(self.sqls["read_log_from_to"].format(from_, to_))

    # 연결 종료
    # self.conn.close()


def main():
    db_new = db()
    # db_new.init_menu()
    # res = new_db.init_scheme()
    # new_db.order_new([{"name":"면_짜장면", "count":2}])
    # new_db.order_new([{"name":"면_짜장면", "count":3},{"name":"면_짬뽕", "count":3}])
    # new_db.order_new([{"name":"면_짜장면", "count":3},{"name":"면_짬뽕", "count":3},{"name":"콜라", "count":30}])
    # print(res)
    # print(new_db.read_table("Orders"))

    # db_new.clear()
    db_new.init_scheme()
    db_new.init_menu()

    # db_new.log("test")
    # db_new.log("test0", 0)
    # db_new.log("test1", 1)
    # db_new.log("test2", 2)
    # db_new.log("test3", 3)
    # print("db_new.read_log()", db_new.read_log())
    # print("db_new.read_log(0)", db_new.read_log(0))
    # print("db_new.read_log(1)", db_new.read_log(1))
    # print("db_new.read_log(2)", db_new.read_log(2))
    # print("db_new.read_log(3)", db_new.read_log(3))

    # oreder_num = db_new.add_order(
    #     table_num=4,
    #     menus=[
    #         {"name": "밥_볶음밥", "count": 4},
    #         {"name": "밥_짜장밥", "count": 4},
    #         {"name": "음료_사이다", "count": 4},
    #     ],
    # )
    # oreder_num = db_new.add_order(
    #     table_num=3,
    #     menus=[
    #         {"name": "면_짜장면", "count": 3},
    #         {"name": "면_짬뽕", "count": 3},
    #         {"name": "음료_코카콜라", "count": 3},
    #     ],
    # )
    # oreder_num = db_new.add_order(
    #     table_num=13,
    #     menus=[
    #         {"name": "요리_탕수육", "count": 3},
    #         {"name": "요리_라조육", "count": 3},
    #         {"name": "음료_제로콜라", "count": 3},
    #     ],
    # )
    # db_new.log("test")
    # print(db_new.read_log_from_to("2024-11-14 16:00:00", "2024-11-15 16:01:00"))

    from pprint import pprint

    # pprint(db_new.runsql("select * from Orders"))
    # # print(db_new.get_orders_not_finished(1))

    # # print(db_new.set_order_payed(1))
    # # print(db_new.get_kitchen())
    # # print(db_new.set_order_payed(2))

    # import pandas as pd
    # import matplotlib.pyplot as plt
    # from collections import defaultdict
    # from datetime import datetime

    # data = db_new.runsql("select * from Orders")

    # # 데이터프레임으로 변환
    # df = pd.DataFrame(data, columns=["ID", "OrderID", "메뉴", "수량", "시간", "상태"])
    # df["시간"] = pd.to_datetime(df["시간"])  # 시간 변환
    # df["시간대"] = df["시간"].dt.hour  # 시간대 추출

    # # 메뉴 가격 정의 (없는 항목은 0으로 처리)
    # prices = {
    #     "밥_볶음밥": 8000,
    #     "밥_짜장밥": 7000,
    #     "음료_사이다": 1500,
    #     "면_짜장면": 6000,
    #     "면_짬뽕": 7000,
    #     "음료_코카콜라": 1500,
    #     "요리_탕수육": 15000,
    #     "요리_라조육": 17000,
    #     "음료_제로콜라": 2000,
    #     "면_우동": 6500,
    #     "직원호출_물": 500,
    #     "직원호출_물티슈": 0,  # 물티슈는 매출로 계산하지 않음
    #     "면_짜장면": 6000,
    #     "면_짬뽕": 7000,
    #     "음료_제로콜라": 2000,
    #     "코카콜라": 1500,
    #     "음료_사이다": 1500,
    # }

    # # 매출 계산
    # df["단가"] = df["메뉴"].map(prices).fillna(0)
    # df["매출"] = df["수량"] * df["단가"]

    # # 시간대별 매출 합계
    # sales_by_hour = df.groupby("시간대")["매출"].sum()

    # # 모든 시간대를 포함하기 위해 0~23시 초기화
    # all_hours = pd.Series(0, index=range(24))
    # sales_by_hour = all_hours.add(sales_by_hour, fill_value=0)

    # # 그래프 그리기
    # plt.figure(figsize=(12, 6))
    # sales_by_hour.plot(kind="bar", color="lightblue", alpha=0.8, edgecolor="black")
    # plt.title("시간대별 매출", fontsize=16)
    # plt.xlabel("시간대 (0~23시)", fontsize=14)
    # plt.ylabel("매출 (원)", fontsize=14)
    # plt.xticks(range(24), [f"{hour}시" for hour in range(24)], rotation=0)
    # plt.grid(axis="y", linestyle="--", alpha=0.7)
    # plt.tight_layout()

    # # 그래프 표시
    # plt.show()

    # import sqlite3

    # db_new.runsql("delete from Orders")
    # # 데이터 정의
    # data = [
    #     (0, "밥_볶음밥", 4, "2024-11-14 11:11:11", 1),
    #     (0, "밥_짜장밥", 4, "2024-11-14 11:11:11", 1),
    #     (0, "음료_사이다", 4, "2024-11-14 11:11:11", 1),
    #     (1, "면_짜장면", 3, "2024-11-14 11:11:11", 1),
    #     (1, "면_짬뽕", 3, "2024-11-14 11:11:11", 1),
    #     (1, "음료_코카콜라", 3, "2024-11-14 11:11:11", 1),
    #     (2, "요리_탕수육", 3, "2024-11-14 12:11:11", 1),
    #     (2, "요리_라조육", 3, "2024-11-14 12:11:11", 1),
    #     (2, "음료_제로콜라", 3, "2024-11-14 12:11:11", 1),
    #     (3, "음료_사이다", 2, "2024-11-14 12:11:11", 1),
    #     (3, "음료_코카콜라", 2, "2024-11-14 12:11:11", 1),
    #     (4, "면_짜장면", 1, "2024-11-14 12:11:11", 0),
    #     (4, "면_짬뽕", 1, "2024-11-14 12:11:11", 0),
    #     (4, "음료_코카콜라", 1, "2024-11-14 12:11:11", 0),
    #     (5, "면_짬뽕", 1, "2024-11-14 12:11:11", 0),
    #     (5, "면_짜장면", 1, "2024-11-14 12:11:11", 0),
    #     (6, "면_우동", 1, "2024-11-14 12:11:11", 0),
    #     (6, "면_짬뽕", 1, "2024-11-14 13:11:11", 0),
    #     (6, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (7, "면_우동", 1, "2024-11-14 13:11:11", 0),
    #     (7, "면_짬뽕", 1, "2024-11-14 13:11:11", 0),
    #     (7, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (8, "면_우동", 11, "2024-11-14 13:11:11", 1),
    #     (9, "음료_제로콜라", 11, "2024-11-14 13:11:11", 0),
    #     (10, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (10, "직원호출_물", 2, "2024-11-14 13:11:11", 0),
    #     (11, "직원호출_물티슈", 1, "2024-11-14 13:11:11", 1),
    #     (12, "음료_제로콜라", 2, "2024-11-14 13:11:11", 1),
    #     (13, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (14, "면_우동", 1, "2024-11-14 13:11:11", 0),
    #     (14, "면_짬뽕", 1, "2024-11-14 13:11:11", 0),
    #     (15, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (15, "면_우동", 11, "2024-11-14 13:11:11", 1),
    #     (16, "음료_제로콜라", 11, "2024-11-14 13:11:11", 0),
    #     (16, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (17, "직원호출_물", 2, "2024-11-14 13:11:11", 0),
    #     (17, "직원호출_물티슈", 1, "2024-11-14 13:11:11", 1),
    #     (18, "음료_제로콜라", 2, "2024-11-14 13:11:11", 1),
    #     (18, "면_우동", 1, "2024-11-14 12:11:11", 0),
    #     (19, "면_짬뽕", 1, "2024-11-14 13:11:11", 0),
    #     (19, "면_짜장면", 1, "2024-11-14 13:11:11", 0),
    #     (20, "면_우동", 1, "2024-11-14 14:11:11", 0),
    #     (20, "면_짬뽕", 1, "2024-11-14 14:11:11", 0),
    #     (21, "면_짜장면", 1, "2024-11-14 14:11:11", 0),
    #     (21, "면_우동", 11, "2024-11-14 14:11:11", 1),
    #     (22, "음료_제로콜라", 11, "2024-11-14 14:11:11", 0),
    #     (22, "면_짜장면", 1, "2024-11-14 14:11:11", 0),
    #     (23, "직원호출_물", 2, "2024-11-14 14:11:11", 0),
    #     (23, "직원호출_물티슈", 1, "2024-11-14 14:11:11", 1),
    #     (24, "음료_제로콜라", 2, "2024-11-14 14:11:11", 1),
    #     (24, "면_우동", 1, "2024-11-14 15:11:11", 0),
    #     (25, "면_짬뽕", 1, "2024-11-14 15:11:11", 0),
    #     (25, "면_짜장면", 1, "2024-11-14 15:11:11", 0),
    #     (26, "면_우동", 1, "2024-11-14 15:11:11", 0),
    #     (26, "면_짬뽕", 1, "2024-11-14 15:11:11", 0),
    #     (27, "면_짜장면", 1, "2024-11-14 15:11:11", 0),
    #     (27, "면_우동", 11, "2024-11-14 15:11:11", 1),
    #     (28, "음료_제로콜라", 11, "2024-11-14 15:11:11", 0),
    #     (28, "면_짜장면", 1, "2024-11-14 15:11:11", 0),
    #     (29, "직원호출_물", 2, "2024-11-14 15:11:11", 0),
    #     (29, "직원호출_물티슈", 1, "2024-11-14 15:11:11", 1),
    #     (30, "음료_제로콜라", 2, "2024-11-14 15:11:11", 1),
    #     (30, "면_우동", 1, "2024-11-14 16:11:11", 0),
    #     (31, "면_짬뽕", 1, "2024-11-14 16:11:11", 0),
    #     (31, "면_짜장면", 1, "2024-11-14 16:11:11", 0),
    #     (32, "면_우동", 1, "2024-11-14 16:11:11", 0),
    #     (32, "면_짬뽕", 1, "2024-11-14 17:11:11", 0),
    #     (33, "면_짜장면", 1, "2024-11-14 17:11:11", 0),
    #     (33, "면_우동", 11, "2024-11-14 17:11:11", 1),
    #     (34, "음료_제로콜라", 11, "2024-11-14 17:11:11", 0),
    #     (34, "면_짜장면", 1, "2024-11-14 17:11:11", 0),
    #     (35, "직원호출_물", 2, "2024-11-14 17:11:11", 0),
    #     (35, "직원호출_물티슈", 1, "2024-11-14 17:11:11", 1),
    #     (36, "음료_제로콜라", 2, "2024-11-14 17:11:11", 1),
    #     (36, "면_우동", 1, "2024-11-14 18:11:11", 0),
    #     (37, "면_짬뽕", 1, "2024-11-14 18:11:11", 0),
    #     (37, "면_짜장면", 1, "2024-11-14 18:11:11", 0),
    #     (38, "면_우동", 1, "2024-11-14 18:11:11", 0),
    #     (38, "면_짬뽕", 1, "2024-11-14 18:11:11", 0),
    #     (39, "면_짜장면", 1, "2024-11-14 18:11:11", 0),
    #     (39, "면_우동", 11, "2024-11-14 18:11:11", 1),
    #     (40, "음료_제로콜라", 11, "2024-11-14 18:11:11", 0),
    #     (40, "면_짜장면", 1, "2024-11-14 18:11:11", 0),
    #     (41, "직원호출_물", 2, "2024-11-14 18:11:11", 0),
    #     (41, "직원호출_물티슈", 1, "2024-11-14 18:11:11", 1),
    #     (42, "음료_제로콜라", 2, "2024-11-14 18:11:11", 1),
    #     (42, "면_우동", 1, "2024-11-14 19:11:11", 0),
    #     (43, "면_짬뽕", 1, "2024-11-14 19:11:11", 0),
    #     (43, "면_짜장면", 1, "2024-11-14 19:11:11", 0),
    #     (44, "면_우동", 1, "2024-11-14 19:11:11", 0),
    #     (44, "면_짬뽕", 1, "2024-11-14 19:11:11", 0),
    #     (45, "면_짜장면", 1, "2024-11-14 19:11:11", 0),
    #     (45, "면_우동", 11, "2024-11-14 19:11:11", 1),
    #     (46, "음료_제로콜라", 11, "2024-11-14 19:11:11", 0),
    #     (46, "면_짜장면", 1, "2024-11-14 19:11:11", 0),
    #     (47, "직원호출_물", 2, "2024-11-14 19:11:11", 0),
    #     (47, "직원호출_물티슈", 1, "2024-11-14 19:11:11", 1),
    #     (48, "음료_제로콜라", 2, "2024-11-14 19:11:11", 1),
    #     (48, "면_우동", 1, "2024-11-14 19:11:11", 0),
    #     (49, "면_짬뽕", 1, "2024-11-14 19:11:11", 0),
    #     (49, "면_짜장면", 1, "2024-11-14 19:11:11", 0),
    #     (50, "면_우동", 1, "2024-11-14 19:11:11", 0),
    #     (50, "면_짬뽕", 1, "2024-11-14 19:11:11", 0),
    #     (51, "면_짜장면", 1, "2024-11-14 19:11:11", 0),
    #     (51, "면_우동", 11, "2024-11-14 19:11:11", 1),
    #     (52, "음료_제로콜라", 11, "2024-11-14 19:11:11", 0),
    #     (52, "면_짜장면", 1, "2024-11-14 19:11:11", 0),
    #     (53, "직원호출_물", 2, "2024-11-14 19:11:11", 0),
    #     (53, "직원호출_물티슈", 1, "2024-11-14 19:11:11", 1),
    #     (54, "음료_제로콜라", 2, "2024-11-14 19:11:11", 1),
    #     (54, "면_우동", 1, "2024-11-14 20:11:11", 0),
    #     (55, "면_짬뽕", 1, "2024-11-14 20:11:11", 0),
    #     (55, "면_짜장면", 1, "2024-11-14 20:11:11", 0),
    #     (56, "면_우동", 1, "2024-11-14 20:11:11", 0),
    #     (56, "면_짬뽕", 1, "2024-11-14 20:11:11", 0),
    #     (57, "면_짜장면", 1, "2024-11-14 20:11:11", 0),
    #     (57, "면_우동", 11, "2024-11-14 20:11:11", 1),
    #     (58, "음료_제로콜라", 11, "2024-11-14 20:11:11", 0),
    #     (58, "면_짜장면", 1, "2024-11-14 20:11:11", 0),
    #     (59, "직원호출_물", 2, "2024-11-14 20:11:11", 0),
    #     (59, "직원호출_물티슈", 1, "2024-11-14 20:11:11", 1),
    #     (60, "음료_제로콜라", 2, "2024-11-14 20:11:11", 1),
    #     (60, "면_우동", 1, "2024-11-14 20:11:11", 0),
    #     (61, "면_짬뽕", 1, "2024-11-14 20:11:11", 0),
    #     (61, "면_짜장면", 1, "2024-11-14 20:11:11", 0),
    #     (62, "면_우동", 1, "2024-11-14 20:11:11", 0),
    #     (62, "면_짬뽕", 1, "2024-11-14 20:11:11", 0),
    #     (63, "면_짜장면", 1, "2024-11-14 20:11:11", 0),
    #     (63, "면_우동", 11, "2024-11-14 20:11:11", 1),
    #     (64, "음료_제로콜라", 11, "2024-11-14 20:11:11", 0),
    #     (64, "면_짜장면", 1, "2024-11-14 20:11:11", 0),
    #     (65, "직원호출_물", 2, "2024-11-14 20:11:11", 0),
    #     (65, "직원호출_물티슈", 1, "2024-11-14 20:11:11", 1),
    #     (66, "음료_제로콜라", 2, "2024-11-14 20:11:11", 1),
    # ]

    # # SQLite 데이터베이스 파일 이름
    # db_name = "src/table_order/table_order/db.db"

    # # SQLite에 데이터 저장
    # def save_to_db(data, db_name):
    #     # 데이터베이스 연결
    #     conn = sqlite3.connect(db_name)
    #     cursor = conn.cursor()

    #     # 데이터 삽입
    #     cursor.executemany(
    #         """
    #     INSERT INTO Orders ( orders_num, name, count, orders_time, finish)
    #     VALUES (?, ?, ?, ?, ?)
    #     """,
    #         data,
    #     )

    #     # 커밋 및 닫기
    #     conn.commit()
    #     conn.close()

    # # 함수 호출
    # save_to_db(data, db_name)

    # print("데이터가 성공적으로 저장되었습니다.")
    db_new.runsql("delete from Log")


if __name__ == "__main__":
    main()
