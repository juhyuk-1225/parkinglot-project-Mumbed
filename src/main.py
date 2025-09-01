"""
주차 관리 시스템
"""
from enum import Enum
import datetime
import json
import os


class Action(Enum):
    ENTER = "1.입차"
    LEAVE = "2.출차"
    CHECK = "3.주차 현황 조회"
    GUEST = "4.정기권 구매"
    EXIT = "5.시스템 종료"


class ParkingImage(Enum):
    ABLE = "🅿️"
    DISABLE = "🚗"


class ParkingSpec(Enum):
    FLOOR = 3
    ROW = 10
    COL = 10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # src/
DATA_FILE = os.path.join(BASE_DIR, "..", "parking_data.json")

# 3차원 배열 [floor][row][col]
parking_state = []
user_db = {}
user_history_db = {}


def save_data_to_file(user_db, user_history_db, filename=DATA_FILE):
    data = {
        "user_db": user_db,
        "user_history_db": user_history_db,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_data_from_file(filename=DATA_FILE):
    if not os.path.exists(filename):
        return {}, {}
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("user_db", {}), data.get("user_history_db", {})


def init_parking_state():
    global parking_state, user_db, user_history_db

    # JSON 파일에서 데이터 불러오기
    user_db_loaded, user_history_db_loaded = load_data_from_file()

    if user_db_loaded:
        user_db.update(user_db_loaded)
        user_history_db.update(user_history_db_loaded)
        print("저장된 데이터에서 차량 정보를 불러왔습니다.")
    else:
        # 난수 기반 초기 생성 코드 제거: 빈 상태로 초기화만 수행
        user_db.clear()
        user_history_db.clear()
        print("저장된 데이터가 없습니다. 현재 차량 데이터는 비어있습니다.")

    # user_db 기준으로 parking_state 초기화
    parking_state = [
        [
            [ParkingImage.ABLE for _ in range(ParkingSpec.COL.value)]
            for _ in range(ParkingSpec.ROW.value)
        ]
        for _ in range(ParkingSpec.FLOOR.value)
    ]

    for car_info in user_db.values():
        f = car_info["floor"] - 1
        pos = car_info["position_num"] - 1
        r, c = divmod(pos, ParkingSpec.COL.value)
        parking_state[f][r][c] = ParkingImage.DISABLE


def get_parking_number(row, col):
    """ 주차 번호 계산 """
    return (row - 1) * ParkingSpec.COL.value + col


def is_parking_able(floor, parking_number):
    floor_idx = floor - 1
    pos_idx = parking_number - 1
    r, c = divmod(pos_idx, ParkingSpec.COL.value)
    return parking_state[floor_idx][r][c] == ParkingImage.ABLE


def view_current_parking_state():
    """ 주차 현황 조회"""
    for f in range(ParkingSpec.FLOOR.value - 1, -1, -1):
        print("[" + str(f + 1) + "F]")
        view_floor_parking_state(f + 1)
        print()


def view_floor_parking_state(floor, highlight=None):
    print(f"\n=== {floor}층 주차 현황 ===")
    for r in range(ParkingSpec.ROW.value + 1):  # + 1 열 번호 자리
        if r == 0:
            row_display = "\t".join(str(c + 1) for c in range(ParkingSpec.COL.value))
            print("\t" + row_display)
            continue
        row_elems = []
        for c in range(ParkingSpec.COL.value):
            if highlight and (r - 1, c) == highlight:
                row_elems.append("🚙")  # 강조 자리만 🚙로 출력
            else:
                row_elems.append(parking_state[floor - 1][r - 1][c].value)
        print(f"{r}\t" + "\t".join(row_elems))


def enter(car_number):
    """ 차량 입차 """
    if car_number in user_db:
        print("이미 입차된 차량입니다.")
        return

    while True:
        for f in range(ParkingSpec.FLOOR.value):
            empty = 0
            for r in range(ParkingSpec.ROW.value):
                for c in range(ParkingSpec.COL.value):
                    if parking_state[f][r][c] == ParkingImage.ABLE:
                        empty += 1
            print(f"{f + 1}층 : 빈자리 {empty}개")

        floor = int(input(f"원하는 층을 입력하세요 (1~{ParkingSpec.FLOOR.value}): "))
        if floor < 1 or floor > ParkingSpec.FLOOR.value:
            print("잘못된 층 입력입니다.")
            continue

        view_floor_parking_state(floor)

        row = int(input(f"원하는 행(1~{ParkingSpec.ROW.value}): "))
        col = int(input(f"원하는 열(1~{ParkingSpec.COL.value}): "))

        if row < 1 or row > ParkingSpec.ROW.value or col < 1 or col > ParkingSpec.COL.value:
            print("잘못된 좌석 입력입니다.")
            continue

        if parking_state[floor - 1][row - 1][col - 1] == ParkingImage.ABLE:
            parking_state[floor - 1][row - 1][col - 1] = ParkingImage.DISABLE
            user_db[car_number] = {
                "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "end_time": "",
                "is_guest": True,
                "floor": floor,
                "position_num": (row - 1) * ParkingSpec.COL.value + col,
            }
            save_data_to_file(user_db, user_history_db)

            view_floor_parking_state(floor, highlight=(row - 1, col - 1))
            print(f"{car_number} 차량이 {floor}층 ({row},{col}) 자리에 입차되었습니다.")
            break
        else:
            print("이미 사용 중인 자리입니다. 다시 선택해주세요.")


def payment(car_number):
    entry = user_db[car_number]
    start = datetime.datetime.strptime(entry['start_time'], "%Y-%m-%d %H:%M")
    end = datetime.datetime.now()
    duration = int((end - start).total_seconds() // 60)  # 분

    if duration <= 20:
        fee = 0
    else:
        fee = 5000
        if duration > 60:
            extra = duration - 60
            fee += ((extra + 29) // 30) * 500
        if fee > 20000:
            fee = 20000
        if not entry['is_guest']:
            fee = fee // 2

    return fee, end.strftime("%Y-%m-%d %H:%M")


def leave(car_number):
    if car_number not in user_db:
        print("등록된 차량이 아닙니다. 다시 시도하세요.")
        return
    entry = user_db[car_number]
    fee, end_time = payment(car_number)
    print(f"차량번호: {car_number}, 주차요금: {fee}원")

    floor_idx = entry['floor'] - 1
    pos_idx = entry['position_num'] - 1
    r, c = divmod(pos_idx, ParkingSpec.COL.value)

    view_floor_parking_state(entry['floor'], highlight=(r, c))

    parking_state[floor_idx][r][c] = ParkingImage.ABLE

    # 출차 시 기록 user_history_db에 추가 (옵션)
    if car_number not in user_history_db:
        user_history_db[car_number] = []
    user_history_db[car_number].append({
        "start_time": entry["start_time"],
        "end_time": end_time,
        "is_guest": entry["is_guest"],
        "floor": entry["floor"],
        "position_num": entry["position_num"],
        "payment": fee,
    })

    del user_db[car_number]

    save_data_to_file(user_db, user_history_db)

    view_current_parking_state()


def action_filter(user_input):
    for act in Action:
        if user_input in act.value.split(".") or user_input == act.value:
            return act


def make_is_guest():
    print("안녕하세요 정기권 구매 페이지입니다. 입차 신청 후 이용해주시길 바랍니다.")
    car_num = input('차량 번호를 입력해주세요.\n')
    if car_num in user_db:
        guest_time = input('구매하실 정기권 기간을 입력해주세요. (한달 : 1, 1년 : 2)')
        entry = user_db[car_num]  

        start_dt = datetime.datetime.strptime(entry['start_time'], "%Y-%m-%d %H:%M")

        if guest_time == "1":
            end_dt = start_dt + datetime.timedelta(days=30)  
            print('한달 정기권 가격은 월/10만원 입니다.\n')
            card = input('카드를 넣고 enter를 눌러주세요.')
            if card == "":
                user_db[car_num]["is_guest"] = True
                print(f'감사합니다. 정기권 기간은 {start_dt.strftime("%Y-%m-%d")} ~ {end_dt.strftime("%Y-%m-%d")} 입니다.')
            else:
                print('결제가 완료되지 않았습니다.')
        elif guest_time == "2":
            end_dt = start_dt + datetime.timedelta(days=365) 
            print('1년 정기권 가격은 60만원 (월/5만원) 입니다.')
            card = input('카드를 넣고 enter를 눌러주세요.')
            if card == "":
                user_db[car_num]["is_guest"] = True
                print(f'감사합니다. 정기권 기간은 {start_dt.strftime("%Y-%m-%d")} ~ {end_dt.strftime("%Y-%m-%d")} 입니다.')
            else:
                print('결제가 완료되지 않았습니다.')
    else:
        print('입차 신청 후 이용해주시길 바랍니다.')


def main():
    init_parking_state()

    action = None
    print("안녕하세요 삼각편대 주차 타워 시스템 입니다.")
    while action != Action.EXIT:
    
        print("원하는 작업을 선택하세요:(입차:1, 출차:2, 주차장 현황:3, 정기권 구매:4, 시스템 종료:5)")
        user_input = input("입력: ").strip()
        action = action_filter(user_input)

        if action is None:
            print("잘못된 입력입니다. 다시 시도하세요.")
            continue

        if action == Action.ENTER:
            car_number = input("차량 번호를 입력하세요: ").strip()
            enter(car_number)
        elif action == Action.LEAVE:
            print("현재 입차 중인 차량 목록:")
            for car in user_db:
                print("-", car)
            car_number = input("차량 번호를 입력하세요: ").strip()
            leave(car_number)
        elif action == Action.CHECK:
            view_current_parking_state()
        elif action == Action.GUEST:
            make_is_guest()
        elif action == Action.EXIT:
            print("시스템을 종료합니다.")
        else:
            print("알 수 없는 작업입니다.")

main()

if __name__ == "__main__":
    main()
