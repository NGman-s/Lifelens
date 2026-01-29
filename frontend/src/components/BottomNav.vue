<template>
  <view class="bottom-nav-placeholder"></view>
  <view class="bottom-nav">
    <view
      class="nav-item"
      :class="{ active: current === 'history' }"
      @tap="navTo('/pages/history/history')"
    >
      <view class="icon-container">
        <!-- 历史图标: 使用 uni-icons 替换 SVG -->
        <uni-icons
          type="calendar"
          :size="26"
          :color="current === 'history' ? '#007aff' : '#86868b'"
        ></uni-icons>
      </view>
      <text class="nav-label">历史</text>
    </view>

    <view
      class="nav-item"
      :class="{ active: current === 'home' }"
      @tap="navTo('/pages/index/index')"
    >
      <view class="icon-container">
        <!-- 识别图标: 使用 uni-icons 替换 SVG -->
        <uni-icons
          type="camera-filled"
          :size="28"
          :color="current === 'home' ? '#007aff' : '#86868b'"
        ></uni-icons>
      </view>
      <text class="nav-label">识别</text>
    </view>

    <view
      class="nav-item"
      :class="{ active: current === 'profile' }"
      @tap="navTo('/pages/profile/profile')"
    >
      <view class="icon-container">
        <!-- 我的图标: 使用 uni-icons 替换 SVG -->
        <uni-icons
          type="person"
          :size="26"
          :color="current === 'profile' ? '#007aff' : '#86868b'"
        ></uni-icons>
      </view>
      <text class="nav-label">我的</text>
    </view>
  </view>
</template>

<script setup>
import { defineProps } from 'vue';

const props = defineProps({
  current: {
    type: String,
    default: 'home'
  }
});

const navTo = (url) => {
  // Use redirectTo to avoid building up a large history stack for tab navigation
  // But check if it's the current page first
  const pages = getCurrentPages();
  const currentPage = pages[pages.length - 1];
  if ('/' + currentPage.route === url) return;

  uni.redirectTo({
    url,
    fail: (err) => {
      console.error('Nav failed', err);
    }
  });
};
</script>

<style lang="scss" scoped>
.bottom-nav-placeholder {
  height: calc(50px + env(safe-area-inset-bottom));
  width: 100%;
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: calc(50px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 999;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  color: #86868b; /* Inactive color */
  transition: all 0.2s ease;

  &.active {
    color: #007aff; /* Active color (Apple Blue) */
  }

  &:active {
    opacity: 0.7;
  }
}

.icon-container {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
}

.nav-icon {
  width: 100%;
  height: 100%;
}

.nav-label {
  font-size: 10px;
  font-weight: 500;
}
</style>
