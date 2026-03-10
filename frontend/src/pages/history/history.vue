<template>
  <view class="page-container">
    <view class="content-wrapper">
      <view class="header">
        <text class="title-large">饮食记录</text>
        <view class="clear-btn" @tap="handleClear">
          <text class="clear-text">清空</text>
        </view>
      </view>

      <view class="chart-card">
        <TrendChart :data="weeklyStats" />
      </view>

      <view class="history-list">
        <view v-if="history.length === 0" class="empty-state">
          <text class="empty-icon">📝</text>
          <text class="empty-text">暂无记录</text>
        </view>

        <view v-for="entry in history" :key="entry.id" class="history-card" @longpress="handleLongPress(entry)">
          <image
            :src="getHistoryImageSrc(entry)"
            mode="aspectFill"
            class="card-image"
            @error="handleImageError(entry.id)"
          ></image>
          <view class="card-content">
            <view class="card-header">
              <text class="card-title">{{ entry.result?.main_name || entry.result?.items?.[0]?.name || '未知菜品' }}</text>
              <text class="card-time">{{ formatDate(entry.timestamp) }}</text>
            </view>
            <view class="card-summary">{{ entry.result?.total_analysis?.summary || '暂无分析摘要' }}</view>
            <view class="card-footer">
              <view class="traffic-dot" :class="entry.result?.total_traffic_light || entry.result?.items?.[0]?.traffic_light"></view>
              <text class="calories-text">{{ entry.result?.total_calories || entry.result?.items?.[0]?.calories || 0 }} kcal</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <BottomNav current="history" />
  </view>
</template>

<script setup>
import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import TrendChart from '@/components/TrendChart.vue';
import BottomNav from '@/components/BottomNav.vue';
import { useUserStore } from '@/store/user';
import { resolveImageUrl } from '@/utils/request';
import historyPlaceholder from '@/static/history-placeholder.svg';

const userStore = useUserStore();
const { history, weeklyStats } = storeToRefs(userStore);
const unavailableImages = ref({});

const formatDate = (isoString) => {
  const date = new Date(isoString);
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
};

const isImageExpired = (entry) => {
  const expiresAt = entry.result?.image_expires_at;
  if (!expiresAt) {
    return false;
  }

  const expiresAtMs = new Date(expiresAt).getTime();
  return Number.isFinite(expiresAtMs) && expiresAtMs <= Date.now();
};

const normalizeHistoryImagePath = (path = '') => path.replace(/\.webp($|\?)/i, '.jpg$1');

const getHistoryImageSrc = (entry) => {
  if (!entry.image || unavailableImages.value[entry.id] || isImageExpired(entry)) {
    return historyPlaceholder;
  }
  return resolveImageUrl(normalizeHistoryImagePath(entry.image));
};

const handleImageError = (entryId) => {
  unavailableImages.value = {
    ...unavailableImages.value,
    [entryId]: true
  };
};

const handleClear = () => {
  uni.showModal({
    title: '清空记录',
    content: '确定要删除所有饮食记录吗？此操作无法撤销。',
    confirmColor: '#FF3B30',
    success: (res) => {
      if (res.confirm) {
        userStore.clearHistory();
      }
    }
  });
};

const handleLongPress = (entry) => {
  uni.showActionSheet({
    itemList: ['删除此记录'],
    itemColor: '#FF3B30',
    success: (res) => {
      if (res.tapIndex === 0) {
        userStore.deleteHistoryEntry(entry.id);
        uni.showToast({
          title: '已删除',
          icon: 'none'
        });
      }
    }
  });
};
</script>

<style lang="scss" scoped>
.page-container {
  min-height: 100vh;
  padding-bottom: calc(50px + env(safe-area-inset-bottom));
}

.content-wrapper {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-top: calc(env(safe-area-inset-top) + 20px);
}

.clear-btn {
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 14px;
}

.clear-text {
  font-size: 13px;
  color: #FF3B30;
  font-weight: 500;
}

.chart-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.03);
}

.history-card {
  background: #fff;
  border-radius: 16px;
  padding: 12px;
  margin-bottom: 16px;
  display: flex;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.card-image {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  background: #f5f5f7;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  margin-left: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}

.card-time {
  font-size: 12px;
  color: #86868b;
}

.card-summary {
  font-size: 13px;
  color: #48484a;
  margin: 4px 0;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
}

.traffic-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;

  &.green { background: #34C759; }
  &.yellow { background: #FF9500; }
  &.red { background: #FF3B30; }
}

.calories-text {
  font-size: 12px;
  font-weight: 500;
  color: #86868b;
}

.empty-state {
  padding-top: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  color: #86868b;
  font-size: 15px;
}
</style>
