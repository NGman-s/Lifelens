import { defineStore } from 'pinia';
import Api from '@/utils/request';

const defaultProfile = {
  age: 25,
  gender: 'male',
  height: 170,
  weight: 65,
  activity_level: 'sedentary',
  goal: 'muscle_gain',
  health_conditions: []
};

const STORAGE_KEYS = {
  profile: 'user_profile',
  history: 'diet_history',
  userId: 'lifelens_user_id',
  friendCode: 'lifelens_friend_code',
  qrPayload: 'lifelens_qr_payload',
  qrImageDataUrl: 'lifelens_qr_image_data_url'
};

const ALLOWED_GENDERS = ['male', 'female'];

const normalizeProfile = (profile = {}) => ({
  ...profile,
  gender: ALLOWED_GENDERS.includes(profile.gender) ? profile.gender : defaultProfile.gender
});

const generateUuid = () =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const random = Math.floor(Math.random() * 16);
    const value = char === 'x' ? random : ((random & 0x3) | 0x8);
    return value.toString(16);
  });

const getStorageValue = (key, fallback) => {
  const value = uni.getStorageSync(key);
  return value === '' || value === undefined || value === null ? fallback : value;
};

const clonePayload = (value) => JSON.parse(JSON.stringify(value));

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: normalizeProfile({ ...defaultProfile, ...getStorageValue(STORAGE_KEYS.profile, {}) }),
    history: getStorageValue(STORAGE_KEYS.history, []),
    userId: getStorageValue(STORAGE_KEYS.userId, ''),
    friendCode: getStorageValue(STORAGE_KEYS.friendCode, ''),
    qrPayload: getStorageValue(STORAGE_KEYS.qrPayload, ''),
    qrImageDataUrl: getStorageValue(STORAGE_KEYS.qrImageDataUrl, ''),
    friendsFeed: [],
    totalFriends: 0,
    friendFeatureReady: false
  }),
  getters: {
    weeklyStats: (state) => {
      const days = [];
      const now = new Date();

      for (let i = 6; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const dateStr = `${year}-${month}-${day}`;
        const label = `${d.getMonth() + 1}/${d.getDate()}`;
        days.push({ fullDate: dateStr, label, calories: 0 });
      }

      const dayMap = new Map(days.map((day) => [day.fullDate, day]));
      state.history.forEach((entry) => {
        const entryTime = new Date(entry.timestamp);
        const year = entryTime.getFullYear();
        const month = String(entryTime.getMonth() + 1).padStart(2, '0');
        const day = String(entryTime.getDate()).padStart(2, '0');
        const entryDateStr = `${year}-${month}-${day}`;
        const dayStat = dayMap.get(entryDateStr);

        if (!dayStat || !entry.result) {
          return;
        }

        if (entry.result.total_calories) {
          dayStat.calories += (parseInt(entry.result.total_calories, 10) || 0);
          return;
        }

        (entry.result.items || []).forEach((item) => {
          dayStat.calories += (parseInt(item.calories, 10) || 0);
        });
      });

      return days;
    }
  },
  actions: {
    updateProfile(newProfile) {
      this.profile = normalizeProfile({ ...this.profile, ...newProfile });
      uni.setStorageSync(STORAGE_KEYS.profile, this.profile);
    },
    addHistoryEntry(entry) {
      const newEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        ...entry
      };
      this.history.unshift(newEntry);
      if (this.history.length > 50) {
        this.history.pop();
      }
      uni.setStorageSync(STORAGE_KEYS.history, this.history);
    },
    clearHistory() {
      this.history = [];
      uni.setStorageSync(STORAGE_KEYS.history, []);
    },
    deleteHistoryEntry(id) {
      const index = this.history.findIndex((entry) => entry.id === id);
      if (index !== -1) {
        this.history.splice(index, 1);
        uni.setStorageSync(STORAGE_KEYS.history, this.history);
      }
    },
    _persistFriendIdentity(payload) {
      this.userId = payload.user_id || this.userId;
      this.friendCode = payload.friend_code || '';
      this.qrPayload = payload.qr_payload || '';
      this.qrImageDataUrl = payload.qr_image_data_url || '';
      this.friendFeatureReady = Boolean(this.userId && this.friendCode && this.qrImageDataUrl);

      uni.setStorageSync(STORAGE_KEYS.userId, this.userId);
      uni.setStorageSync(STORAGE_KEYS.friendCode, this.friendCode);
      uni.setStorageSync(STORAGE_KEYS.qrPayload, this.qrPayload);
      uni.setStorageSync(STORAGE_KEYS.qrImageDataUrl, this.qrImageDataUrl);
    },
    _buildRecordPayload(result = {}) {
      return {
        main_name: String(result.main_name || result.items?.[0]?.name || '未知菜品'),
        total_calories: parseInt(result.total_calories, 10) || 0,
        total_traffic_light: String(result.total_traffic_light || result.items?.[0]?.traffic_light || 'yellow').toLowerCase(),
        summary: String(result.total_analysis?.summary || '暂无分析摘要'),
        image_url: String(result.image_url || ''),
        image_expires_at: String(result.image_expires_at || '')
      };
    },
    async initFriendIdentity(forceRefresh = false) {
      let userId = forceRefresh ? '' : this.userId;
      if (!userId) {
        userId = getStorageValue(STORAGE_KEYS.userId, '');
      }
      if (!userId) {
        userId = generateUuid();
      }

      this.userId = userId;
      uni.setStorageSync(STORAGE_KEYS.userId, userId);

      try {
        const res = await Api.request({
          url: '/api/v1/user/init',
          method: 'POST',
          header: {
            'content-type': 'application/json'
          },
          data: {
            user_id: userId
          }
        });

        if (res?.code !== 200 || !res.data) {
          throw {
            message: res?.message || '初始化身份失败，请稍后重试',
            traceId: res?.trace_id || ''
          };
        }

        this._persistFriendIdentity(res.data);
        return clonePayload(res.data);
      } catch (error) {
        this.friendFeatureReady = false;
        throw error;
      }
    },
    async refreshFriendIdentity() {
      return this.initFriendIdentity(false);
    },
    async addFriendByCode(friendCode) {
      if (!this.friendFeatureReady) {
        await this.initFriendIdentity();
      }

      const res = await Api.request({
        url: '/api/v1/friends/add',
        method: 'POST',
        header: {
          'content-type': 'application/json'
        },
        data: {
          friend_code: String(friendCode || '').trim()
        }
      });

      if (res?.code !== 200 || !res.data) {
        throw {
          message: res?.message || '添加好友失败，请稍后重试',
          traceId: res?.trace_id || ''
        };
      }

      return clonePayload(res.data);
    },
    async fetchFriendsFeed() {
      if (!this.friendFeatureReady) {
        await this.initFriendIdentity();
      }

      const res = await Api.request({
        url: '/api/v1/friends/feed',
        method: 'GET'
      });

      if (res?.code !== 200 || !res.data) {
        throw {
          message: res?.message || '获取好友动态失败，请稍后重试',
          traceId: res?.trace_id || ''
        };
      }

      this.totalFriends = Number(res.data.total_friends || 0);
      this.friendsFeed = Array.isArray(res.data.items) ? clonePayload(res.data.items) : [];
      return clonePayload(res.data);
    },
    async syncDietRecord(result) {
      if (!this.friendFeatureReady) {
        await this.initFriendIdentity();
      }

      const payload = this._buildRecordPayload(result);
      const res = await Api.request({
        url: '/api/v1/diet-records',
        method: 'POST',
        header: {
          'content-type': 'application/json'
        },
        data: payload
      });

      if (res?.code !== 200 || !res.data) {
        throw {
          message: res?.message || '同步好友动态失败，请稍后重试',
          traceId: res?.trace_id || ''
        };
      }

      return clonePayload(res.data);
    }
  }
});
