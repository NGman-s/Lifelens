<template>
  <view class="page-shell">
    <view class="page-bg page-bg-top"></view>
    <view class="page-bg page-bg-bottom"></view>

    <view class="content-wrapper">
      <view class="header">
        <view>
          <text class="title-large">好友</text>
          <text class="header-subtitle">看看朋友今天吃了什么</text>
        </view>
        <view class="header-pill">
          <text class="header-pill-text">{{ totalFriends }} 位好友</text>
        </view>
      </view>

      <view class="identity-card">
        <view class="identity-card-glow"></view>
        <view class="identity-card-header">
          <view>
            <text class="identity-label">我的身份卡</text>
            <text class="identity-caption">扫一扫或输入口令，就能看到我的今日饮食</text>
          </view>
          <view class="identity-status">
            <view class="status-dot" :class="{ online: friendFeatureReady }"></view>
            <text class="identity-status-text">{{ friendFeatureReady ? '已就绪' : '待初始化' }}</text>
          </view>
        </view>

        <view class="identity-hero">
          <view class="qr-frame">
            <image v-if="qrImageDataUrl" :src="qrImageDataUrl" mode="aspectFit" class="qr-image"></image>
            <view v-else class="qr-placeholder">
              <text class="qr-placeholder-text">身份卡生成中</text>
            </view>
          </view>
          <view class="code-panel">
            <text class="code-label">6 位好友口令</text>
            <text class="friend-code">{{ friendCode || '------' }}</text>
            <text class="code-hint">优先推荐口令直连，扫码是平台增强能力</text>
          </view>
        </view>

        <view class="identity-actions">
          <view class="identity-action" @tap="handleCopyCode">
            <uni-icons type="paperplane" :size="16" color="#0f172a"></uni-icons>
            <text class="identity-action-text">复制口令</text>
          </view>
          <view class="identity-action primary" @tap="handleRefreshIdentity">
            <uni-icons type="reload" :size="16" color="#ffffff"></uni-icons>
            <text class="identity-action-text primary">刷新身份卡</text>
          </view>
        </view>

        <view class="identity-metrics">
          <view class="metric-chip">
            <text class="metric-value">{{ totalFriends }}</text>
            <text class="metric-label">已连接好友</text>
          </view>
          <view class="metric-chip">
            <text class="metric-value">{{ feedViewModels.length }}</text>
            <text class="metric-label">今日动态</text>
          </view>
        </view>
      </view>

      <view class="action-card">
        <view class="section-head">
          <view>
            <text class="section-title">添加好友</text>
            <text class="section-subtitle">输入 6 位口令，或者当面对着二维码扫一扫</text>
          </view>
        </view>

        <view class="code-input-shell">
          <input
            v-model="inputCode"
            class="code-input"
            type="text"
            maxlength="6"
            placeholder="输入好友口令"
            confirm-type="done"
            @confirm="handleAddFriend"
          />
          <view class="add-button" :class="{ disabled: addingFriend }" @tap="handleAddFriend">
            <text class="add-button-text">{{ addingFriend ? '添加中...' : '添加好友' }}</text>
          </view>
        </view>

        <view class="secondary-actions">
          <view v-if="canScanCode" class="secondary-action" @tap="handleScanCode">
            <uni-icons type="scan" :size="16" color="#2563eb"></uni-icons>
            <text class="secondary-action-text">扫码添加</text>
          </view>
          <view v-else class="secondary-tip">
            <uni-icons type="info" :size="16" color="#94a3b8"></uni-icons>
            <text class="secondary-tip-text">当前 H5 不支持扫码，请输入 6 位口令</text>
          </view>
        </view>
      </view>

      <view class="feed-card">
        <view class="section-head">
          <view>
            <text class="section-title">今日好友动态</text>
            <text class="section-subtitle">按时间倒序展示好友今天保存过的饮食记录</text>
          </view>
          <view class="refresh-badge" @tap="refreshFeed">
            <uni-icons type="reload" :size="14" color="#475569"></uni-icons>
            <text class="refresh-badge-text">刷新</text>
          </view>
        </view>

        <view v-if="initializing || loadingFeed" class="loading-state">
          <view class="loading-spinner"></view>
          <text class="loading-text">正在加载好友动态...</text>
        </view>

        <view v-else-if="errorMessage" class="error-state">
          <text class="error-title">好友功能暂时不可用</text>
          <text class="error-text">{{ errorMessage }}</text>
          <view class="error-button" @tap="initializePage">
            <text class="error-button-text">重新加载</text>
          </view>
        </view>

        <view v-else-if="feedViewModels.length === 0" class="empty-state">
          <text class="empty-icon">{{ totalFriends > 0 ? '🕊️' : '🤝' }}</text>
          <text class="empty-title">{{ totalFriends > 0 ? '好友今天还没发动态' : '还没有好友' }}</text>
          <text class="empty-text">
            {{ totalFriends > 0 ? '可以先把你的身份卡发给朋友，等他们保存饮食后这里会自动更新。' : '先复制口令或展示二维码，把第一位朋友加进来。' }}
          </text>
        </view>

        <view v-else class="feed-list">
          <view
            v-for="item in feedViewModels"
            :key="item.id"
            class="feed-item"
            :class="{ 'text-only': !item.imageAvailable }"
          >
            <image
              v-if="item.imageAvailable"
              :src="item.imageSrc"
              mode="aspectFill"
              class="feed-image"
              lazy-load
              @error="handleImageError(item.id)"
            ></image>

            <view class="feed-content" :class="{ 'no-image': !item.imageAvailable }">
              <view class="feed-meta">
                <view class="friend-pill">
                  <text class="friend-pill-text">好友 {{ item.friend_code }}</text>
                </view>
                <text class="feed-time">{{ item.timeLabel }}</text>
              </view>

              <text class="feed-title">{{ item.main_name }}</text>
              <text class="feed-summary">{{ item.summary }}</text>

              <view v-if="!item.imageAvailable" class="text-only-badge">
                <text class="text-only-badge-text">仅文本动态</text>
              </view>

              <view class="feed-footer">
                <view class="feed-footer-main">
                  <view class="traffic-dot" :class="item.total_traffic_light"></view>
                  <text class="feed-calories">{{ item.total_calories }} kcal</text>
                </view>
                <text class="feed-status">{{ item.trafficLabel }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <BottomNav current="friends" />
  </view>
</template>

<script setup>
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app';
import BottomNav from '@/components/BottomNav.vue';
import { useUserStore } from '@/store/user';
import { formatRequestError, resolveImageUrl } from '@/utils/request';

const userStore = useUserStore();
const {
  friendCode,
  qrImageDataUrl,
  friendsFeed,
  totalFriends,
  friendFeatureReady
} = storeToRefs(userStore);

const inputCode = ref('');
const initializing = ref(true);
const loadingFeed = ref(false);
const addingFriend = ref(false);
const errorMessage = ref('');
const unavailableImages = ref({});
const canScanCode = ref(true);

// #ifdef H5
canScanCode.value = false;
// #endif

const normalizeTrafficLight = (value) => {
  const normalized = String(value || 'yellow').toLowerCase();
  return ['green', 'yellow', 'red'].includes(normalized) ? normalized : 'yellow';
};

const getTrafficLabel = (value) => {
  const traffic = normalizeTrafficLight(value);
  if (traffic === 'green') return '推荐';
  if (traffic === 'red') return '少吃';
  return '适量';
};

const formatTime = (isoString) => {
  const date = new Date(isoString);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${month}/${day} ${hours}:${minutes}`;
};

const isImageExpired = (item) => {
  const expiresAt = item.image_expires_at;
  if (!expiresAt) {
    return false;
  }

  const expiresAtMs = new Date(expiresAt).getTime();
  return Number.isFinite(expiresAtMs) && expiresAtMs <= Date.now();
};

const markImageUnavailable = (id) => {
  if (!id || unavailableImages.value[id]) {
    return;
  }

  unavailableImages.value = {
    ...unavailableImages.value,
    [id]: true
  };
};

const feedViewModels = computed(() =>
  friendsFeed.value.map((item) => {
    const imageAvailable = Boolean(item.image_url) && !unavailableImages.value[item.id] && !isImageExpired(item);

    return {
      ...item,
      total_traffic_light: normalizeTrafficLight(item.total_traffic_light),
      trafficLabel: getTrafficLabel(item.total_traffic_light),
      timeLabel: formatTime(item.recorded_at),
      imageAvailable,
      imageSrc: imageAvailable ? resolveImageUrl(item.image_url) : ''
    };
  })
);

const parseFriendCode = (rawValue) => {
  const normalized = String(rawValue || '').trim();
  const prefixedMatch = normalized.match(/^lifelens:add:(\d{6})$/i);
  if (prefixedMatch) {
    return prefixedMatch[1];
  }

  const plainMatch = normalized.match(/^(\d{6})$/);
  return plainMatch ? plainMatch[1] : '';
};

const initializePage = async () => {
  initializing.value = true;
  errorMessage.value = '';

  try {
    await userStore.initFriendIdentity();
    await userStore.fetchFriendsFeed();
  } catch (error) {
    console.warn('Failed to initialize friends page', error);
    errorMessage.value = formatRequestError(error, '好友功能初始化失败，请稍后重试');
  } finally {
    initializing.value = false;
    loadingFeed.value = false;
  }
};

const refreshFeed = async () => {
  loadingFeed.value = true;
  errorMessage.value = '';

  try {
    await userStore.fetchFriendsFeed();
  } catch (error) {
    console.warn('Failed to refresh friend feed', error);
    errorMessage.value = formatRequestError(error, '刷新好友动态失败，请稍后重试');
  } finally {
    loadingFeed.value = false;
  }
};

const handleRefreshIdentity = async () => {
  loadingFeed.value = true;
  errorMessage.value = '';

  try {
    await userStore.refreshFriendIdentity();
    await userStore.fetchFriendsFeed();
    uni.showToast({
      title: '身份卡已刷新',
      icon: 'none'
    });
  } catch (error) {
    console.warn('Failed to refresh identity card', error);
    errorMessage.value = formatRequestError(error, '刷新身份卡失败，请稍后重试');
  } finally {
    loadingFeed.value = false;
  }
};

const handleCopyCode = () => {
  if (!friendCode.value) {
    uni.showToast({
      title: '口令暂未生成',
      icon: 'none'
    });
    return;
  }

  uni.setClipboardData({
    data: friendCode.value,
    success: () => {
      uni.showToast({
        title: '口令已复制',
        icon: 'none'
      });
    }
  });
};

const handleAddFriend = async () => {
  const parsedCode = parseFriendCode(inputCode.value);
  if (!parsedCode) {
    uni.showToast({
      title: '请输入有效的 6 位好友口令',
      icon: 'none'
    });
    return;
  }

  addingFriend.value = true;
  try {
    const result = await userStore.addFriendByCode(parsedCode);
    inputCode.value = '';
    await userStore.fetchFriendsFeed();
    uni.showToast({
      title: result.created ? '添加成功' : '你们已经是好友了',
      icon: 'none'
    });
  } catch (error) {
    console.warn('Failed to add friend', error);
    uni.showToast({
      title: formatRequestError(error, '添加好友失败，请稍后重试'),
      icon: 'none',
      duration: 3000
    });
  } finally {
    addingFriend.value = false;
  }
};

const handleScanCode = () => {
  if (!canScanCode.value) {
    uni.showToast({
      title: '当前环境不支持扫码，请输入口令',
      icon: 'none'
    });
    return;
  }

  // #ifndef H5
  uni.scanCode({
    scanType: ['qrCode'],
    success: async (res) => {
      const parsedCode = parseFriendCode(res.result);
      if (!parsedCode) {
        uni.showToast({
          title: '无法识别好友口令',
          icon: 'none'
        });
        return;
      }

      inputCode.value = parsedCode;
      await handleAddFriend();
    },
    fail: (error) => {
      if (String(error?.errMsg || '').includes('cancel')) {
        return;
      }
      uni.showToast({
        title: '扫码失败，请稍后重试',
        icon: 'none'
      });
    }
  });
  // #endif
};

const handleImageError = (id) => {
  markImageUnavailable(id);
};

onShow(() => {
  initializePage();
});

onPullDownRefresh(async () => {
  try {
    await refreshFeed();
  } finally {
    uni.stopPullDownRefresh();
  }
});
</script>

<style lang="scss" scoped>
.page-shell {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background: linear-gradient(180deg, #eef4ff 0%, #f6f7fb 32%, #f5f5f7 100%);
}

.page-bg {
  position: absolute;
  border-radius: 999px;
  opacity: 0.42;
  pointer-events: none;
}

.page-bg-top {
  width: 180px;
  height: 180px;
  top: -40px;
  right: -30px;
  background: radial-gradient(circle, rgba(125, 169, 255, 0.34) 0%, rgba(125, 169, 255, 0) 72%);
}

.page-bg-bottom {
  width: 220px;
  height: 220px;
  bottom: 120px;
  left: -60px;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.22) 0%, rgba(147, 197, 253, 0) 74%);
}

.content-wrapper {
  position: relative;
  z-index: 1;
  padding: 20px;
  padding-bottom: 28px;
}

.header {
  padding-top: calc(env(safe-area-inset-top) + 20px);
  margin-bottom: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.header-subtitle {
  display: block;
  margin-top: -4px;
  font-size: 13px;
  color: #6b7280;
}

.header-pill {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.header-pill-text {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.identity-card,
.action-card,
.feed-card {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  margin-bottom: 18px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
}

.identity-card {
  padding: 22px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98) 0%, rgba(238, 245, 255, 0.98) 100%);
}

.identity-card-glow {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 110px;
  height: 110px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0) 72%);
}

.identity-card-header,
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.identity-label,
.section-title {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.identity-caption,
.section-subtitle {
  display: block;
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: #64748b;
}

.identity-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 999px;
  background: #ffffff;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
}

.identity-status-text {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.identity-hero {
  display: flex;
  gap: 18px;
  align-items: center;
  margin: 22px 0 18px;
}

.qr-frame {
  width: 124px;
  height: 124px;
  border-radius: 20px;
  padding: 14px;
  background: #ffffff;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
  flex-shrink: 0;
}

.qr-image,
.qr-placeholder {
  width: 100%;
  height: 100%;
}

.qr-placeholder {
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  display: flex;
  justify-content: center;
  align-items: center;
}

.qr-placeholder-text {
  font-size: 12px;
  color: #64748b;
}

.code-panel {
  flex: 1;
  min-width: 0;
}

.code-label {
  display: block;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: #64748b;
  text-transform: uppercase;
}

.friend-code {
  display: block;
  margin-top: 10px;
  font-size: 40px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.18em;
  color: #0f172a;
}

.code-hint {
  display: block;
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.5;
  color: #475569;
}

.identity-actions,
.identity-metrics,
.secondary-actions,
.feed-list {
  display: flex;
  gap: 12px;
}

.identity-actions,
.identity-metrics {
  margin-top: 14px;
}

.identity-action,
.metric-chip,
.refresh-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 16px;
  background: #ffffff;
}

.identity-action {
  flex: 1;
}

.identity-action.primary {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
}

.identity-action-text,
.metric-label,
.refresh-badge-text {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.identity-action-text.primary {
  color: #ffffff;
}

.metric-chip {
  flex: 1;
  flex-direction: column;
  align-items: flex-start;
}

.metric-value {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.action-card,
.feed-card {
  padding: 20px;
}

.code-input-shell {
  margin-top: 18px;
  display: flex;
  gap: 12px;
}

.code-input {
  flex: 1;
  height: 52px;
  padding: 0 16px;
  border-radius: 18px;
  background: #f8fafc;
  font-size: 18px;
  color: #0f172a;
  letter-spacing: 0.12em;
}

.add-button,
.error-button {
  min-width: 112px;
  padding: 0 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  display: inline-flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.16);
}

.add-button.disabled {
  opacity: 0.6;
}

.add-button-text,
.error-button-text {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
}

.secondary-actions {
  margin-top: 14px;
  align-items: center;
}

.secondary-action,
.secondary-tip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 14px;
  background: #eff6ff;
}

.secondary-action-text {
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
}

.secondary-tip {
  background: #f8fafc;
}

.secondary-tip-text {
  font-size: 13px;
  color: #64748b;
}

.feed-card {
  min-height: 240px;
}

.loading-state,
.error-state,
.empty-state {
  padding: 36px 12px 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.loading-spinner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 3px solid rgba(148, 163, 184, 0.25);
  border-top-color: #2563eb;
  animation: spin 1s linear infinite;
}

.loading-text,
.error-title,
.empty-title {
  margin-top: 14px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.error-text,
.empty-text {
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}

.empty-icon {
  font-size: 42px;
}

.error-button {
  margin-top: 16px;
}

.feed-list {
  flex-direction: column;
  margin-top: 18px;
}

.feed-item {
  display: flex;
  align-items: stretch;
  padding: 12px;
  border-radius: 20px;
  background: linear-gradient(145deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.feed-item.text-only {
  padding: 16px;
}

.feed-image {
  width: 88px;
  height: 88px;
  border-radius: 16px;
  background: #e2e8f0;
  flex-shrink: 0;
}

.feed-content {
  flex: 1;
  min-width: 0;
  margin-left: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.feed-content.no-image {
  margin-left: 0;
}

.feed-meta,
.feed-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.friend-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  background: #eef2ff;
}

.friend-pill-text {
  font-size: 12px;
  font-weight: 700;
  color: #3730a3;
}

.feed-time {
  font-size: 12px;
  color: #94a3b8;
}

.feed-title {
  margin-top: 12px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.feed-summary {
  margin: 8px 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}

.text-only-badge {
  margin-bottom: 10px;
}

.text-only-badge-text {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
  font-weight: 700;
}

.feed-footer-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.traffic-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.traffic-dot.green {
  background: #22c55e;
}

.traffic-dot.yellow {
  background: #f59e0b;
}

.traffic-dot.red {
  background: #ef4444;
}

.feed-calories,
.feed-status {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 380px) {
  .identity-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .qr-frame {
    width: 100%;
    height: 180px;
  }

  .friend-code {
    font-size: 34px;
    letter-spacing: 0.14em;
  }

  .code-input-shell {
    flex-direction: column;
  }

  .add-button {
    min-height: 52px;
  }
}
</style>
