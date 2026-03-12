# 添加好友功能 Implementation Plan

> **For Antigravity:** REQUIRED WORKFLOW: Use `.agent/workflows/execute-plan.md` to execute this plan task-by-task in single-flow mode.

**Goal:** 实现一个轻量化、无需注册的用户系统：在本地生成 UUID 作为隐性账号，并通过短口令/二维码互相加好友，查看对方一天的饮食热量。

**Architecture:** 
后端使用 Python 内置 sqlite3 作为极其轻量的存储方案（存放 `users`、`friends`、`diet_records`），减少运维压力。前端借助 Pinia 进行设备 ID 及口令管理，提供基于 Glassmorphism 风格的“身份卡”及扫描组件，保持“一拍即合”的核心交互特质。

**Tech Stack:** FastAPI, SQLite, Vue 3, Pinia, uni.scanCode, qrccode (小程序/H5生成库)

---

### Task 1: 建立后端数据库基础配置及表结构

**Files:**
- Create: `backend/utils/db.py`
- Modify: `backend/main.py`

**Step 1: Write `backend/utils/db.py`**

```python
import sqlite3
import os
import random
import string
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "lifelens.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                device_id TEXT PRIMARY KEY,
                short_code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friends (
                user_id_1 TEXT,
                user_id_2 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id_1, user_id_2)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diet_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                main_name TEXT,
                total_calories INTEGER,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def generate_short_code():
    return ''.join(random.choices(string.digits, k=6))

def get_or_create_user(device_id: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id, short_code FROM users WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        
        # Check collision and generate
        for _ in range(10):
            code = generate_short_code()
            try:
                cursor.execute("INSERT INTO users (device_id, short_code) VALUES (?, ?)", (device_id, code))
                conn.commit()
                return {"device_id": device_id, "short_code": code}
            except sqlite3.IntegrityError:
                continue
        raise ValueError("Failed to generate unique short code")
```

**Step 2: Initialize DB in FastAPI Lifecycle**

Modify `backend/main.py` near `lifespan`:
```python
from utils.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Initialize the DB
    _migrate_legacy_webp_thumbnails()
    # ...
```

---

### Task 2: 分配/校验用户的 API

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/test_api.py`

**Step 1: Add endpoints**

In `backend/main.py`:
```python
from pydantic import BaseModel
from utils.db import get_or_create_user

class InitRequest(BaseModel):
    device_id: str

@app.post("/api/v1/user/init")
async def init_user(req: InitRequest):
    try:
        user_info = get_or_create_user(req.device_id)
        return {"code": 200, "data": user_info}
    except Exception as e:
        return _error_response(str(e), 500)
```

**Step 2: Basic smoke test**
Write a quick check in `test_api.py` to hit `/api/v1/user/init`. Verify it returns 200 and a 6-digit `short_code`.
Commit.

---

### Task 3: 扩充后端好友及动态体系

**Files:**
- Modify: `backend/utils/db.py`
- Modify: `backend/main.py`

**Step 1: Add Friend & Read Feed logic in `utils/db.py`**

```python
def add_friend_by_code(my_device_id: str, friend_code: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM users WHERE short_code = ?", (friend_code,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("好友口令无效")
        friend_id = row['device_id']
        if friend_id == my_device_id:
            raise ValueError("不能添加自己为好友")
            
        # Add to friends list bidirectionally or check if exists
        try:
            cursor.execute("INSERT OR IGNORE INTO friends (user_id_1, user_id_2) VALUES (?, ?)", (my_device_id, friend_id))
            cursor.execute("INSERT OR IGNORE INTO friends (user_id_1, user_id_2) VALUES (?, ?)", (friend_id, my_device_id))
            conn.commit()
            return {"friend_id": friend_id}
        except Exception:
            raise ValueError("添加好友失败")

def get_friends_feed(device_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.user_id_2 as friend_id, u.short_code, d.main_name, d.total_calories, d.image_url, d.created_at
            FROM friends f
            JOIN users u ON f.user_id_2 = u.device_id
            LEFT JOIN diet_records d ON f.user_id_2 = d.device_id AND date(d.created_at) = date('now')
            WHERE f.user_id_1 = ?
            ORDER BY d.created_at DESC NULLS LAST
        ''', (device_id,))
        rows = cursor.fetchall()
        friends = {}
        for row in rows:
            fid = row['friend_id']
            if fid not in friends:
                friends[fid] = {"short_code": row["short_code"], "records": []}
            if row['main_name']:
                friends[fid]["records"].append({
                    "main_name": row["main_name"],
                    "total_calories": row["total_calories"],
                    "image_url": row["image_url"],
                    "time": row["created_at"]
                })
        return list(friends.values())
```

**Step 2: Adding Endpoints to `backend/main.py`**

```python
from utils.db import add_friend_by_code, get_friends_feed

class AddFriendRequest(BaseModel):
    my_device_id: str
    friend_code: str

@app.post("/api/v1/friends/add")
async def add_friend(req: AddFriendRequest):
    try:
        result = add_friend_by_code(req.my_device_id, req.friend_code)
        return {"code": 200, "data": result}
    except ValueError as e:
        return _error_response(str(e), 400)

@app.get("/api/v1/friends/feed")
async def get_feed(device_id: str):
    try:
        data = get_friends_feed(device_id)
        return {"code": 200, "data": data}
    except Exception as e:
        return _error_response(str(e), 500)
```

**Step 3: Update `analyze_vision`**
In `backend/main.py` `analyze_vision`:
Extract `device_id` from `user_context` (assuming frontend will send it inside). Or add it as a new Form parameter `device_id`. If `device_id` is present, record the analysis:
```python
def record_diet_analysis(device_id, main_name, total_calories, image_url):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO diet_records (device_id, main_name, total_calories, image_url) VALUES (?, ?, ?, ?)",
            (device_id, main_name, total_calories, image_url)
        )
        conn.commit()
```
Insert it right before `return JSONResponse`. Commit.

---

### Task 4: 前端状态管理及生命周期 (Pinia)

**Files:**
- Create: `frontend/src/store/user.js`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/utils/request.js`

**Step 1: Write User Store**
`frontend/src/store/user.js`:
```javascript
import { defineStore } from 'pinia';
import { request } from '../utils/request';

// helper to gen uuid
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

export const useUserStore = defineStore('user', {
    state: () => ({
        deviceId: '',
        shortCode: '',
    }),
    actions: {
        async initUser() {
            let id = uni.getStorageSync('lifelens_device_id');
            if (!id) {
                id = generateUUID();
                uni.setStorageSync('lifelens_device_id', id);
            }
            this.deviceId = id;
            try {
                const res = await request('/api/v1/user/init', 'POST', { device_id: id });
                if (res.code === 200) {
                    this.shortCode = res.data.short_code;
                }
            } catch (err) {
                console.error("User init err", err);
            }
        }
    }
});
```

**Step 2: Init Store on App Launch**
`frontend/src/App.vue`:
```javascript
<script setup>
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from './store/user'

onLaunch(() => {
  const userStore = useUserStore();
  userStore.initUser();
  console.log('App Launch')
})
</script>
```

**Step 3: Make Request Utils support form-data device_id**
Ensure when uploading the image (`uni.uploadFile`), it passes `device_id: userStore.deviceId` as part of formData so the backend can link the picture.
Commit.

---

### Task 5: 友邻之窗 (UI 页面开发)

**Files:**
- Create: `frontend/src/pages/friends/index.vue`
- Modify: `frontend/src/pages.json`

**Step 1: Scaffold specific page & UI styling**
Set up the Vue file with Glassmorphism ID Card (showing short code from pinia), a "+" Add Friend input field, and a Feed List iterating over friend data.

**Step 2: API calls for Feed**
```javascript
import { request } from '../../utils/request';
// ...
async function fetchFeed() {
    const res = await request(`/api/v1/friends/feed?device_id=${userStore.deviceId}`, 'GET');
    if (res.code === 200) {
        friendsFeed.value = res.data;
    }
}
```

**Step 3: Add friend by code**
```javascript
async function addFriend() {
    const res = await request('/api/v1/friends/add', 'POST', {
        my_device_id: userStore.deviceId,
        friend_code: inputCode.value
    });
    if (res.code === 200) {
        uni.showToast({ title: '添加成功' });
        fetchFeed();
    }
}
```

**Step 4: Update Routing**
Add `pages/friends/index` to `frontend/src/pages.json`.
From the `index.vue` main page, add a sleek floating action button or sidebar entry to navigate to `/pages/friends/index`.
Commit.

---

### Task 6: 增强与验证二维码加好友能力

**Files:**
- Modify: `frontend/src/pages/friends/index.vue`
- Add QR code component if needed (Or simply ask user to scan short code). For MVP speed, uni.scanCode provides native camera parsing.

**Step 1: Scan QR Feature**
```javascript
function scanToAdd() {
    uni.scanCode({
        success: function (res) {
            // Suppose the QR code just contains the 6-digit short code conceptually
            inputCode.value = res.result;
            addFriend();
        }
    });
}
```

**Step 2: Render QR**
Add a lightweight Vue QR generator or just display the `shortCode` cleanly in large text with "扫一扫" or "输入口令" text under it.
(To keep it minimal, you can skip external QR libraries and rely on input code, but implementing QR is preferred for true Option C experience).

**Step 3: Verification & Polish**
Run the H5 instance, check if the Glassmorphism friend card displays nicely, confirm if two separate browser sessions can add each other and see each other's uploaded meals from the SQLite DB.
Commit all.
