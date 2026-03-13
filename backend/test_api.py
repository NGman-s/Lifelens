import json
import uuid

import requests

API_BASE_URL = "http://localhost:8080/api/v1"


def _init_user(user_id: str):
    response = requests.post(
        f"{API_BASE_URL}/user/init",
        json={"user_id": user_id},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def _add_friend(user_id: str, friend_code: str):
    response = requests.post(
        f"{API_BASE_URL}/friends/add",
        headers={"X-User-Id": user_id},
        json={"friend_code": friend_code},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def _save_record(user_id: str):
    response = requests.post(
        f"{API_BASE_URL}/diet-records",
        headers={"X-User-Id": user_id},
        json={
            "main_name": "手工烟雾测试沙拉",
            "total_calories": 360,
            "total_traffic_light": "green",
            "summary": "一份用于好友功能烟雾测试的示例饮食记录。",
            "image_url": "/uploads/smoke-test.jpg",
            "image_expires_at": "2026-04-11T00:00:00Z",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def _get_feed(user_id: str):
    response = requests.get(
        f"{API_BASE_URL}/friends/feed",
        headers={"X-User-Id": user_id},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def test_friend_feature_smoke():
    alice_id = str(uuid.uuid4())
    bob_id = str(uuid.uuid4())

    print("1. 初始化两个用户...")
    alice = _init_user(alice_id)
    bob = _init_user(bob_id)
    print(json.dumps({"alice": alice, "bob": bob}, indent=2, ensure_ascii=False))

    print("2. Alice 添加 Bob 为好友...")
    add_result = _add_friend(alice["user_id"], bob["friend_code"])
    print(json.dumps(add_result, indent=2, ensure_ascii=False))

    print("3. Alice 保存一条饮食记录...")
    record_result = _save_record(alice["user_id"])
    print(json.dumps(record_result, indent=2, ensure_ascii=False))

    print("4. Bob 拉取好友动态...")
    feed = _get_feed(bob["user_id"])
    print(json.dumps(feed, indent=2, ensure_ascii=False))

    if feed["items"]:
        print("Smoke test success: Bob 看到了 Alice 的今日动态。")
    else:
        print("Smoke test failed: Bob 的动态列表为空。")


if __name__ == "__main__":
    try:
        test_friend_feature_smoke()
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
