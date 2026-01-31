<template>
  <view class="overlay-container" :class="{ visible: visible }">
    <!-- Backdrop -->
    <view class="backdrop" @tap="$emit('close')" v-if="visible"></view>

    <!-- Bottom Sheet -->
    <view class="bottom-sheet" :class="{ 'slide-up': visible, 'danger-border': result?.total_traffic_light === 'red' }">
      <!-- Drag Handle -->
      <view class="sheet-handle-bar">
        <view class="sheet-handle"></view>
      </view>

      <!-- Loading State -->
      <view class="loading-state" v-if="loading">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在分析...</text>
        <AIThoughtViewer
          :visible="true"
          :stage="stage"
          :healthConditions="healthConditions"
          :isEmbedded="true"
        />
      </view>

      <!-- Result Content -->
      <scroll-view scroll-y class="sheet-content" v-if="!loading && result">
        <!-- Header Section -->
        <view class="result-header">
          <view class="title-row">
            <text class="dish-name">{{ result.main_name || result.items[0]?.name || '识别结果' }}</text>
            <view class="traffic-badge" :class="result.total_traffic_light || result.items[0]?.traffic_light">
              {{ getTrafficLightLabel(result.total_traffic_light || result.items[0]?.traffic_light) }}
            </view>
          </view>

          <view class="nutrition-row">
            <view class="nutrition-item">
              <view v-if="result.total_traffic_light === 'red'" class="danger-dot"></view>
              <text class="nutri-value" :class="{ 'text-danger': result.total_traffic_light === 'red' }">
                {{ result.total_calories || result.items[0]?.calories || 0 }}
              </text>
              <text class="nutri-unit">kcal</text>
              <text class="nutri-label">热量</text>
              <text v-if="result.total_traffic_light === 'red'" class="warning-icon">⚠️</text>
            </view>
            <view class="nutrition-divider"></view>
            <view class="nutrition-tags">
              <text
                v-for="tag in result.items[0]?.nutrition_tags"
                :key="tag"
                class="tag-chip"
              >{{ tag }}</text>
            </view>
          </view>
        </view>

        <!-- Health Warning Section -->
        <view class="section-container" v-if="result.warning_message">
          <view class="warning-alert-card" :class="result.total_traffic_light">
            <text class="warning-icon-large">⚠️</text>
            <view class="warning-content">
              <view class="warning-title">健康预警</view>
              <text class="warning-text">{{ result.warning_message }}</text>
            </view>
          </view>
        </view>

        <!-- AI Analysis Section -->
        <view class="section-container">
          <view class="section-title">AI 分析</view>
          <view class="analysis-card">
            <view class="analysis-text summary">
              {{ result.total_analysis.summary }}
            </view>
            <view class="analysis-divider"></view>
            <view class="suggestion-row">
              <text class="suggestion-icon">💡</text>
              <text class="analysis-text suggestion">
                {{ result.total_analysis.suggestion }}
              </text>
            </view>
          </view>
        </view>

        <!-- Thought Process (Expandable/Optional) -->
        <view class="section-container" v-if="result.thought_process">
          <view class="section-title small">识别逻辑</view>
          <view class="thought-text">{{ result.thought_process }}</view>
        </view>

        <!-- Action Buttons -->
        <view class="action-area button-group">
          <button class="btn-secondary" @tap="$emit('discard')">不保存</button>
          <button class="btn-primary" :class="{ 'btn-danger': result.total_traffic_light === 'red' }" @tap="handleSave">
            {{ result.total_traffic_light === 'red' ? '仍要保存' : '保存并关闭' }}
          </button>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import AIThoughtViewer from './AIThoughtViewer.vue';

const props = defineProps({
  visible: Boolean,
  loading: Boolean,
  result: Object,
  stage: Number,
  healthConditions: Array
});

const emit = defineEmits(['save', 'discard']);

const handleSave = () => {
  emit('save');
};

const getTrafficLightLabel = (color) => {
  const map = {
    'green': '推荐',
    'yellow': '适量',
    'red': '少吃'
  };
  return map[color] || '未知';
};
</script>

<style lang="scss" scoped>
.overlay-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  pointer-events: none;
  visibility: hidden;
  transition: visibility 0.3s;

  &.visible {
    pointer-events: auto;
    visibility: visible;
  }
}

.backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  opacity: 0;
  animation: fadeIn 0.3s forwards;
}

@keyframes fadeIn {
  to { opacity: 1; }
}

.bottom-sheet {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: #FFFFFF;
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  display: flex;
  flex-direction: column;
  max-height: 85vh;
  padding-bottom: env(safe-area-inset-bottom);

  &.slide-up {
    transform: translateY(0);
  }

  &.danger-border {
    border: 2px solid #FF3B30;
    box-shadow: 0 -4px 30px rgba(255, 59, 48, 0.2);
  }
}

.sheet-handle-bar {
  width: 100%;
  height: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.sheet-handle {
  width: 36px;
  height: 5px;
  background: #E5E5EA;
  border-radius: 3px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #E5E5EA;
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 17px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 8px;
}

.loading-sub {
  font-size: 13px;
  color: #86868B;
}

/* Result Content */
.sheet-content {
  flex: 1;
  width: 100%;
  overflow-y: auto;
}

.result-header {
  padding: 10px 24px 24px;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.dish-name {
  font-size: 28px;
  font-weight: 700;
  color: #1D1D1F;
  line-height: 1.2;
  flex: 1;
  margin-right: 12px;
}

.traffic-badge {
  padding: 6px 12px;
  border-radius: 100px;
  font-size: 13px;
  font-weight: 600;
  color: #FFF;
  flex-shrink: 0;

  &.green { background-color: #34C759; }
  &.yellow { background-color: #FF9500; }
  &.red { background-color: #FF3B30; }
}

.nutrition-row {
  display: flex;
  align-items: center;
}

.nutrition-item {
  display: flex;
  align-items: baseline;
}

.nutri-value {
  font-size: 24px;
  font-weight: 700;
  color: #1D1D1F;
  margin-right: 2px;

  &.text-danger {
    color: #FF3B30;
  }
}

.danger-dot {
  width: 10px;
  height: 10px;
  background-color: #FF3B30;
  border-radius: 50%;
  margin-right: 8px;
  animation: pulse-red 1.5s infinite;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
}

.warning-icon {
  margin-left: 8px;
  font-size: 18px;
}

.nutri-unit {
  font-size: 13px;
  color: #86868B;
  margin-right: 6px;
}

.nutri-label {
  font-size: 13px;
  color: #86868B;
}

.nutrition-divider {
  width: 1px;
  height: 20px;
  background: #E5E5EA;
  margin: 0 16px;
}

.nutrition-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-chip {
  padding: 4px 10px;
  background: #F2F2F7;
  color: #636366;
  font-size: 12px;
  border-radius: 6px;
  font-weight: 500;
}

/* Analysis Section */
.section-container {
  padding: 0 24px 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 12px;

  &.small {
    font-size: 13px;
    color: #86868B;
  }
}

.analysis-card {
  background: #F5F5F7;
  border-radius: 16px;
  padding: 16px;
}

/* Warning Alert Card */
.warning-alert-card {
  display: flex;
  padding: 16px;
  border-radius: 16px;
  margin-bottom: 8px;
  align-items: flex-start;

  &.red {
    background-color: #FFF2F2;
    border: 1px solid #FF3B30;
    .warning-icon-large { color: #FF3B30; }
    .warning-title { color: #FF3B30; }
  }

  &.yellow {
    background-color: #FFF9F2;
    border: 1px solid #FF9500;
    .warning-icon-large { color: #FF9500; }
    .warning-title { color: #FF9500; }
  }
}

.warning-icon-large {
  font-size: 24px;
  margin-right: 12px;
  margin-top: -2px;
}

.warning-content {
  flex: 1;
}

.warning-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}

.warning-text {
  font-size: 14px;
  line-height: 1.4;
  color: #1D1D1F;
}

.analysis-text {
  font-size: 15px;
  line-height: 1.5;
  color: #1D1D1F;

  &.summary {
    font-weight: 500;
  }

  &.suggestion {
    color: #48484A;
  }
}

.analysis-divider {
  height: 1px;
  background: #E5E5EA;
  margin: 12px 0;
}

.suggestion-row {
  display: flex;
  align-items: flex-start;
}

.suggestion-icon {
  margin-right: 8px;
  font-size: 16px;
}

.thought-text {
  font-size: 13px;
  line-height: 1.5;
  color: #86868B;
  background: #F9F9F9;
  padding: 12px;
  border-radius: 8px;
}

/* Action Area */
.action-area {
  padding: 0 24px 24px;
}

.button-group {
  display: flex;
  gap: 16px;
}

.btn-secondary {
  flex: 1;
  height: 50px;
  line-height: 50px;
  font-size: 17px;
  background-color: #F2F2F7;
  color: #007AFF;
  border-radius: 14px; /* Matches iOS default button radius often */
  font-weight: 600;
  border: none;

  &:active {
    opacity: 0.7;
    background-color: #E5E5EA;
  }
}

.btn-primary {
  flex: 2;
  height: 50px;
  line-height: 50px;
  font-size: 17px;
  border-radius: 14px;

  &.btn-danger {
    background-color: #FF3B30 !important;
    color: #FFF;
  }
}
</style>
