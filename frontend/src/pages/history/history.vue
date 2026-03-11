<template>
  <view class="page-container">
    <scroll-view
      class="page-scroll"
      scroll-y
      :scroll-top="historyScrollTop"
      :scroll-y="!detailVisible"
      @scroll="handleHistoryScroll"
    >
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
          <view v-if="historyViewModels.length === 0" class="empty-state">
            <text class="empty-icon">📝</text>
            <text class="empty-text">暂无记录</text>
          </view>

          <view
            v-for="entry in historyViewModels"
            :key="entry.id"
            class="history-card"
            :class="{ 'text-only': !entry.imageAvailable }"
            @tap="openDetail(entry.id)"
            @longpress.stop="handleLongPress(entry.id)"
          >
            <image
              v-if="entry.imageAvailable"
              :src="entry.imageSrc"
              mode="aspectFill"
              class="card-image"
              lazy-load
              @error="handleImageError(entry.id)"
            ></image>

            <view class="card-content" :class="{ 'no-image': !entry.imageAvailable }">
              <view class="card-header">
                <text class="card-title">{{ entry.title }}</text>
                <text class="card-time">{{ entry.timeLabel }}</text>
              </view>

              <view v-if="!entry.imageAvailable" class="text-only-badge">
                <text class="text-only-badge-text">仅文本存档</text>
              </view>

              <view class="card-summary">{{ entry.summary }}</view>

              <view class="card-footer">
                <view class="card-footer-main">
                  <view class="traffic-dot" :class="entry.trafficLight"></view>
                  <text class="calories-text">{{ entry.calories }} kcal</text>
                </view>
                <text class="detail-link">点击查看详情</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <HistoryDetailSheet
      :visible="detailVisible"
      :entry="activeEntry"
      :image-src="activeEntry?.imageSrc || ''"
      :image-available="Boolean(activeEntry?.imageAvailable)"
      :scroll-top="detailScrollTop"
      @close="closeDetail"
      @image-error="handleActiveEntryImageError"
    />

    <BottomNav current="history" />
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import TrendChart from '@/components/TrendChart.vue';
import BottomNav from '@/components/BottomNav.vue';
import HistoryDetailSheet from '@/components/HistoryDetailSheet.vue';
import { useUserStore } from '@/store/user';
import { resolveImageUrl } from '@/utils/request';

const userStore = useUserStore();
const { history, weeklyStats } = storeToRefs(userStore);

const unavailableImages = ref({});
const detailVisible = ref(false);
const activeEntryId = ref('');
const historyScrollTop = ref(0);
const detailScrollTop = ref(0);

const formatDate = (isoString) => {
  const date = new Date(isoString);
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
};

const getEntryResult = (entry) => entry?.result || {};
const getPrimaryItem = (entry) => getEntryResult(entry).items?.[0] || {};

const normalizeTrafficLight = (value) => {
  const trafficLight = String(value || 'yellow').toLowerCase();
  return ['green', 'yellow', 'red'].includes(trafficLight) ? trafficLight : 'yellow';
};

const isImageExpired = (entry) => {
  const expiresAt = getEntryResult(entry).image_expires_at;
  if (!expiresAt) {
    return false;
  }

  const expiresAtMs = new Date(expiresAt).getTime();
  return Number.isFinite(expiresAtMs) && expiresAtMs <= Date.now();
};

const normalizeHistoryImagePath = (path = '') => path.replace(/\.webp($|\?)/i, '.jpg$1');

const markImageUnavailable = (entryId) => {
  if (!entryId || unavailableImages.value[entryId]) {
    return;
  }

  unavailableImages.value = {
    ...unavailableImages.value,
    [entryId]: true
  };
};

const historyViewModels = computed(() =>
  history.value.map((entry) => {
    const result = getEntryResult(entry);
    const primaryItem = getPrimaryItem(entry);
    const imageAvailable = Boolean(entry?.image) && !unavailableImages.value[entry.id] && !isImageExpired(entry);

    return {
      ...entry,
      result,
      primaryItem,
      title: result.main_name || primaryItem.name || '未知菜品',
      summary: result.total_analysis?.summary || '暂无分析摘要',
      calories: result.total_calories || primaryItem.calories || 0,
      trafficLight: normalizeTrafficLight(result.total_traffic_light || primaryItem.traffic_light),
      timeLabel: formatDate(entry.timestamp),
      imageAvailable,
      imageSrc: imageAvailable ? resolveImageUrl(normalizeHistoryImagePath(entry.image)) : ''
    };
  })
);

const activeEntry = computed(() => historyViewModels.value.find((entry) => entry.id === activeEntryId.value) || null);

const openDetail = (entryId) => {
  activeEntryId.value = entryId;
  detailScrollTop.value = 0;
  detailVisible.value = true;
};

const closeDetail = () => {
  detailVisible.value = false;
  detailScrollTop.value = 0;
  activeEntryId.value = '';
};

const handleHistoryScroll = (event) => {
  historyScrollTop.value = event?.detail?.scrollTop || 0;
};

const handleImageError = (entryId) => {
  markImageUnavailable(entryId);
};

const handleActiveEntryImageError = () => {
  if (!activeEntry.value?.id) {
    return;
  }

  markImageUnavailable(activeEntry.value.id);
};

const handleClear = () => {
  uni.showModal({
    title: '清空记录',
    content: '确定要删除所有饮食记录吗？此操作无法撤销。',
    confirmColor: '#FF3B30',
    success: (res) => {
      if (res.confirm) {
        closeDetail();
        userStore.clearHistory();
      }
    }
  });
};

const handleLongPress = (entryId) => {
  uni.showActionSheet({
    itemList: ['删除此记录'],
    itemColor: '#FF3B30',
    success: (res) => {
      if (res.tapIndex === 0) {
        if (activeEntryId.value === entryId) {
          closeDetail();
        }
        userStore.deleteHistoryEntry(entryId);
        uni.showToast({
          title: '已删除',
          icon: 'none'
        });
      }
    }
  });
};

watch(
  history,
  (entries) => {
    if (!activeEntryId.value) {
      return;
    }

    const exists = entries.some((entry) => entry.id === activeEntryId.value);
    if (!exists) {
      closeDetail();
    }
  },
  { deep: true }
);
</script>

<style lang="scss" scoped>
.page-container {
  height: 100vh;
  overflow: hidden;
}

.page-scroll {
  height: calc(100vh - 50px - env(safe-area-inset-bottom));
}

.content-wrapper {
  min-height: 100%;
  padding: 20px;
  padding-bottom: 24px;
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
  color: #ff3b30;
  font-weight: 500;
}

.chart-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
}

.history-card {
  display: flex;
  align-items: stretch;
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 18px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.94), transparent 36%),
    linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
  transition: transform 0.16s ease, box-shadow 0.16s ease;

  &:active {
    transform: scale(0.985);
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
  }

  &.text-only {
    padding: 16px;
  }
}

.card-image {
  width: 84px;
  height: 84px;
  border-radius: 14px;
  background: #eef2f7;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  min-width: 0;
  margin-left: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  &.no-image {
    margin-left: 0;
  }
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  flex: 1;
  min-width: 0;
  font-size: 16px;
  font-weight: 600;
  color: #172033;
  line-height: 1.35;
}

.card-time {
  flex-shrink: 0;
  font-size: 12px;
  color: #8e96a3;
}

.text-only-badge {
  margin-top: 8px;
}

.text-only-badge-text {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #fff4e8;
  color: #c56f32;
  font-size: 12px;
  font-weight: 600;
}

.card-summary {
  margin: 8px 0 10px;
  font-size: 13px;
  line-height: 1.5;
  color: #4d5a70;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  overflow: hidden;
}

.history-card.text-only .card-summary {
  -webkit-line-clamp: 2;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-footer-main {
  display: flex;
  align-items: center;
  min-width: 0;
}

.traffic-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;

  &.green {
    background: #34c759;
  }

  &.yellow {
    background: #ff9500;
  }

  &.red {
    background: #ff3b30;
  }
}

.calories-text {
  font-size: 12px;
  font-weight: 500;
  color: #7b8796;
}

.detail-link {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  color: #5a6b84;
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
