import requests
from datetime import datetime, timedelta
import os
from collections import defaultdict

# 環境変数（GitHub Secretsに登録済み）
NYUTAI_TOKEN = os.environ["NYUTAI_TOKEN"]
CHATWORK_TOKEN = os.environ["CHATWORK_TOKEN"]
CHATWORK_ROOM_ID = os.environ["CHATWORK_ROOM_ID"]

BASE_URL = "https://site1.nyutai.com/api/chief/v1"
HEADERS = {"Api-Token": NYUTAI_TOKEN}
CHATWORK_HEADERS = {"X-ChatWorkToken": CHATWORK_TOKEN}

# 学年ID → 学年名 マップ（表示順に並べたいので順番付き）
grade_map = {
    11: "小学1年生", 12: "小学2年生", 13: "小学3年生", 14: "小学4年生",
    15: "小学5年生", 16: "小学6年生", 21: "中学1年生", 22: "中学2年生", 23: "中学3年生",
    31: "高校1年生", 32: "高校2年生", 33: "高校3年生", 60: "社会人", 99: "その他",
    71: "年少組", 72: "年中組", 73: "年長組"
}

# 過去14日間の起点日
date_from = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

# 生徒一覧を取得
res = requests.get(f"{BASE_URL}/students", headers=HEADERS)
students = res.json().get("data", [])

# 学年ごとに未記録生徒をまとめる
inactive_by_grade = defaultdict(list)

for student in students:
    user_id = student["id"]
    name = student["name"]
    grade_id = student.get("grade_id", 99)

    # 入退室記録を取得
    res2 = requests.get(
        f"{BASE_URL}/entrance_and_exits",
        headers=HEADERS,
        params={"user_id": user_id}
    )
    records = res2.json().get("data", [])

    if not records:
        last_date_str = "記録なし"
        last_date = datetime.min
    else:
        latest = max(records, key=lambda r: r["entrance_time"] or r["exit_time"])
        last_time = latest.get("entrance_time") or latest.get("exit_time")
        last_date = datetime.strptime(last_time[:10], "%Y-%m-%d")
        last_date_str = last_date.strftime("%Y/%m/%d")

    # 最終記録日が14日前より古い場合、リストに追加
    if last_date < datetime.now() - timedelta(days=14):
        grade_label = grade_map.get(grade_id, "不明")
        inactive_by_grade[grade_id].append(f"- {name}（最終記録日：{last_date_str}）")

# メッセージ組み立て
if inactive_by_grade:
    lines = ["[info][title]2週間以上入退記録がない生徒[/title]"]
    for gid in sorted(inactive_by_grade.keys()):
        grade_label = grade_map.get(gid, "不明")
        lines.append(f"■ {grade_label}")
        lines.extend(inactive_by_grade[gid])
        lines.append("")  # 空行
    lines.append("[/info]")
    body = "\n".join(lines)

    # Chatwork通知
    chat_res = requests.post(
        f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages",
        headers=CHATWORK_HEADERS,
        data={"body": body}
    )
    print("通知を送信しました")
else:
    print("2週間以上記録のない生徒はいません")
