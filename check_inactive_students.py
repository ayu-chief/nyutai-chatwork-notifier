import requests
from datetime import datetime, timedelta
import os

NYUTAI_TOKEN = os.environ["NYUTAI_TOKEN"]
CHATWORK_TOKEN = os.environ["CHATWORK_TOKEN"]
CHATWORK_ROOM_ID = os.environ["CHATWORK_ROOM_ID"]

BASE_URL = "https://site1.nyutai.com/api/chief/v1"
HEADERS = {"Api-Token": NYUTAI_TOKEN}
CHATWORK_HEADERS = {"X-ChatWorkToken": CHATWORK_TOKEN}

# 今日から過去14日
date_from = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

# 生徒一覧
res = requests.get(f"{BASE_URL}/students", headers=HEADERS)
students = res.json().get("data", [])

inactive = []

for student in students:
    user_id = student["id"]
    name = student["name"]

    res2 = requests.get(
        f"{BASE_URL}/entrance_and_exits",
        headers=HEADERS,
        params={"user_id": user_id, "date_from": date_from}
    )
    records = res2.json().get("data", [])

    if len(records) == 0:
        inactive.append(name)

if inactive:
    body = "[info][title]2週間以上入退記録がない生徒[/title]\n" + "\n".join(inactive) + "[/info]"
    chat_res = requests.post(
        f"https://api.chatwork.com/v2/rooms/{CHATWORK_ROOM_ID}/messages",
        headers=CHATWORK_HEADERS,
        data={"body": body}
    )
    print("通知を送信しました")
else:
    print("2週間以上記録のない生徒はいません")
