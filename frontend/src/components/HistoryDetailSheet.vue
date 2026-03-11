<template>
  <view class="overlay-container" :class="{ visible }">
    <view v-if="visible" class="backdrop" @click="emit('close')"></view>

    <view
      class="bottom-sheet"
      :class="{
        'slide-up': visible,
        'danger-border': trafficLight === 'red'
      }"
    >
      <view class="sheet-handle-bar">
        <view class="sheet-handle"></view>
      </view>

      <scroll-view
        v-if="entry"
        scroll-y
        class="sheet-content"
        :scroll-top="innerScrollTop"
        @scroll="handleScroll"
      >
        <view class="detail-header">
          <view class="meta-row">
            <text class="meta-label">历史记录详情</text>
            <text class="record-time">{{ formatDetailDate(entry.timestamp) }}</text>
          </view>

          <view class="title-row">
            <text class="dish-name">{{ displayName }}</text>
            <view class="traffic-badge" :class="trafficLight">
              {{ getTrafficLightLabel(trafficLight) }}
            </view>
          </view>

          <view class="nutrition-row">
            <view class="nutrition-item">
              <text class="nutri-value" :class="{ 'text-danger': trafficLight === 'red' }">
                {{ totalCalories }}
              </text>
              <text class="nutri-unit">kcal</text>
              <text class="nutri-label">热量</text>
            </view>

            <view class="nutrition-divider"></view>

            <view class="nutrition-tags">
              <text v-for="tag in primaryTags" :key="tag" class="tag-chip">{{ tag }}</text>
              <text v-if="primaryTags.length === 0" class="tag-chip muted">暂无标签</text>
            </view>
          </view>
        </view>

        <view v-if="imageAvailable && imageSrc" class="section-container">
          <view class="section-title">记录图片</view>
          <view class="image-frame" @click="previewImage">
            <image :src="imageSrc" mode="aspectFit" class="detail-image" lazy-load @error="handleImageError"></image>
          </view>
          <text class="image-caption">点击可放大查看当前保留的压缩图</text>
        </view>

        <view v-else class="section-container">
          <view class="text-only-card">
            <view class="text-only-header">
              <text class="text-only-badge">仅保留分析文本</text>
            </view>
            <text class="text-only-copy">
              原始缩略图已过期、被清理或无法加载，当前记录仅展示保存时的分析内容。
            </text>
          </view>
        </view>

        <view class="section-container" v-if="result.warning_message">
          <view class="warning-alert-card" :class="trafficLight">
            <text class="warning-icon-large">⚠️</text>
            <view class="warning-content">
              <view class="warning-title">健康预警</view>
              <text class="warning-text">{{ result.warning_message }}</text>
            </view>
          </view>
        </view>

        <view class="section-container">
          <view class="section-title">AI 分析</view>
          <view class="analysis-card">
            <view class="analysis-text summary">
              {{ result.total_analysis?.summary || '暂无分析摘要' }}
            </view>
            <view class="analysis-divider"></view>
            <view class="suggestion-row">
              <text class="suggestion-icon">💡</text>
              <text class="analysis-text suggestion">
                {{ result.total_analysis?.suggestion || '暂无建议' }}
              </text>
            </view>
          </view>
        </view>

        <view class="section-container" v-if="result.alternatives">
          <view class="section-title">AI 爆改建议</view>
          <view class="alternatives-card">
            <view class="alt-item">
              <view class="alt-header">
                <text class="alt-icon">🍽️</text>
                <text class="alt-label">点餐更优选</text>
              </view>
              <text class="alt-text">{{ result.alternatives.ordering_hint }}</text>
            </view>
            <view class="alt-divider"></view>
            <view class="alt-item">
              <view class="alt-header">
                <text class="alt-icon">👨‍🍳</text>
                <text class="alt-label">自制健康改</text>
              </view>
              <text class="alt-text">{{ result.alternatives.cooking_hint }}</text>
            </view>
          </view>
        </view>

        <view class="section-container" v-if="result.thought_process">
          <view class="thought-card">
            <view class="thought-toggle" @click="toggleThought">
              <view class="thought-toggle-copy">
                <view class="section-title small compact">识别逻辑</view>
                <text class="thought-toggle-hint">
                  {{ isThoughtExpanded ? '点击收起' : '点击展开' }}
                </text>
              </view>
              <text class="thought-toggle-icon" :class="{ expanded: isThoughtExpanded }">⌄</text>
            </view>
            <view v-if="isThoughtExpanded" class="thought-text">{{ result.thought_process }}</view>
          </view>
        </view>

        <view class="action-area">
          <button class="btn-close" @click="emit('close')">关闭</button>
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { computed, defineEmits, defineProps, ref, watch } from 'vue';

const props = defineProps({
  visible: Boolean,
  entry: {
    type: Object,
    default: null
  },
  imageSrc: {
    type: String,
    default: ''
  },
  imageAvailable: Boolean,
  scrollTop: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['close', 'image-error']);
const isThoughtExpanded = ref(false);
const innerScrollTop = ref(0);

const result = computed(() => props.entry?.result || {});
const primaryItem = computed(() => result.value.items?.[0] || {});
const displayName = computed(() => result.value.main_name || primaryItem.value.name || '未知菜品');
const totalCalories = computed(() => result.value.total_calories || primaryItem.value.calories || 0);
const primaryTags = computed(() => primaryItem.value.nutrition_tags || []);
const trafficLight = computed(() => {
  const color = (result.value.total_traffic_light || primaryItem.value.traffic_light || 'yellow').toLowerCase();
  return ['green', 'yellow', 'red'].includes(color) ? color : 'yellow';
});

const formatDetailDate = (isoString) => {
  const date = new Date(isoString);
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  const hours = `${date.getHours()}`.padStart(2, '0');
  const minutes = `${date.getMinutes()}`.padStart(2, '0');
  return `${year}/${month}/${day} ${hours}:${minutes}`;
};

const toggleThought = () => {
  isThoughtExpanded.value = !isThoughtExpanded.value;
};

const previewImage = () => {
  if (!props.imageAvailable || !props.imageSrc) {
    return;
  }

  uni.previewImage({
    current: props.imageSrc,
    urls: [props.imageSrc]
  });
};

const handleImageError = () => {
  emit('image-error');
};

const handleScroll = (event) => {
  innerScrollTop.value = event?.detail?.scrollTop || 0;
};

watch(
  () => [props.visible, props.entry?.id],
  () => {
    isThoughtExpanded.value = false;
  }
);

watch(
  () => props.scrollTop,
  (scrollTop) => {
    innerScrollTop.value = scrollTop;
  },
  { immediate: true }
);

const getTrafficLightLabel = (color) => {
  const map = {
    green: '推荐',
    yellow: '适量',
    red: '少吃'
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
  overscroll-behavior: contain;
}

.overlay-container.visible {
  pointer-events: auto;
  visibility: visible;
}

.backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
  opacity: 0;
  animation: fadeIn 0.3s forwards;
  will-change: opacity;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

.bottom-sheet {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff 0%, #f9fafc 100%);
  border-radius: 24px 24px 0 0;
  box-shadow: 0 -12px 40px rgba(15, 23, 42, 0.14);
  transform: translate3d(0, 100%, 0);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  padding-bottom: env(safe-area-inset-bottom);
  overflow: hidden;
  will-change: transform;
}

.bottom-sheet.slide-up {
  transform: translate3d(0, 0, 0);
}

.bottom-sheet.danger-border {
  border: 2px solid #ffb3ad;
  box-shadow: 0 -12px 40px rgba(255, 59, 48, 0.16);
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
  width: 40px;
  height: 5px;
  border-radius: 999px;
  background: #d6dae1;
}

.sheet-content {
  flex: 1;
  width: 100%;
  overflow-y: auto;
}

.detail-header {
  padding: 10px 24px 24px;
}

.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.meta-label {
  font-size: 13px;
  font-weight: 600;
  color: #7b8796;
  letter-spacing: 0.3px;
}

.record-time {
  font-size: 12px;
  color: #8e96a3;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.dish-name {
  flex: 1;
  font-size: 28px;
  line-height: 1.18;
  font-weight: 700;
  color: #172033;
}

.traffic-badge {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
}

.traffic-badge.green {
  background: #34c759;
}

.traffic-badge.yellow {
  background: #ff9500;
}

.traffic-badge.red {
  background: #ff3b30;
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
  font-size: 26px;
  font-weight: 700;
  color: #172033;
  margin-right: 4px;
}

.nutri-value.text-danger {
  color: #ff3b30;
}

.nutri-unit,
.nutri-label {
  font-size: 13px;
  color: #8e96a3;
}

.nutri-unit {
  margin-right: 6px;
}

.nutrition-divider {
  width: 1px;
  height: 22px;
  background: #e6e9ee;
  margin: 0 16px;
}

.nutrition-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: #eef2f7;
  color: #516076;
  font-size: 12px;
  font-weight: 500;
}

.tag-chip.muted {
  color: #8e96a3;
}

.section-container {
  padding: 0 24px 24px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #172033;
  margin-bottom: 12px;
}

.section-title.small {
  font-size: 13px;
  color: #7b8796;
}

.section-title.compact {
  margin-bottom: 0;
}

.image-frame {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  max-height: 280px;
  padding: 18px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.9), transparent 40%),
    linear-gradient(135deg, #eef4fb 0%, #f7f9fc 100%);
  border: 1px solid #e4ebf3;
  overflow: hidden;
}

.detail-image {
  width: 100%;
  height: 220px;
}

.image-caption {
  display: block;
  margin-top: 10px;
  font-size: 12px;
  color: #8e96a3;
}

.text-only-card {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff6ef 0%, #fffaf5 100%);
  border: 1px solid #f5d8bf;
}

.text-only-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.text-only-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 999px;
  background: #fff;
  color: #c46c2b;
  font-size: 12px;
  font-weight: 600;
}

.text-only-copy {
  font-size: 14px;
  line-height: 1.6;
  color: #83583a;
}

.warning-alert-card {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border-radius: 18px;
}

.warning-alert-card.red {
  background: #fff2f2;
  border: 1px solid #ff3b30;
}

.warning-alert-card.yellow {
  background: #fff8ef;
  border: 1px solid #ff9500;
}

.warning-alert-card.green {
  background: #effbf1;
  border: 1px solid #34c759;
}

.warning-alert-card.red .warning-icon-large,
.warning-alert-card.red .warning-title {
  color: #ff3b30;
}

.warning-alert-card.yellow .warning-icon-large,
.warning-alert-card.yellow .warning-title {
  color: #ff9500;
}

.warning-alert-card.green .warning-icon-large,
.warning-alert-card.green .warning-title {
  color: #34c759;
}

.warning-icon-large {
  margin-right: 12px;
  font-size: 24px;
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
  line-height: 1.5;
  color: #172033;
}

.analysis-card {
  padding: 16px;
  border-radius: 18px;
  background: #f4f7fb;
}

.analysis-text {
  font-size: 15px;
  line-height: 1.6;
  color: #172033;
}

.analysis-text.summary {
  font-weight: 500;
}

.analysis-text.suggestion {
  color: #445066;
}

.analysis-divider {
  height: 1px;
  background: #dde3eb;
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

.alternatives-card {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #eefbef 0%, #f7fff8 100%);
  border: 1px solid #c9e7cf;
}

.alt-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alt-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alt-icon {
  font-size: 16px;
}

.alt-label {
  font-size: 14px;
  font-weight: 700;
  color: #2e8b57;
}

.alt-text {
  font-size: 14px;
  line-height: 1.6;
  color: #172033;
}

.alt-divider {
  height: 1px;
  background: #c9e7cf;
  margin: 12px 0;
}

.thought-card {
  border-radius: 18px;
  background: #f9fafc;
  overflow: hidden;
  border: 1px solid #edf1f5;
}

.thought-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
}

.thought-toggle-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.thought-toggle-hint {
  font-size: 12px;
  color: #8e96a3;
}

.thought-toggle-icon {
  font-size: 16px;
  color: #7b8796;
  transform: rotate(0deg);
  transition: transform 0.2s ease;
}

.thought-toggle-icon.expanded {
  transform: rotate(180deg);
}

.thought-text {
  padding: 0 14px 14px;
  font-size: 13px;
  line-height: 1.6;
  color: #607086;
}

.action-area {
  padding: 0 24px 24px;
}

.btn-close {
  height: 50px;
  line-height: 50px;
  border: none;
  border-radius: 14px;
  background: #172033;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}
</style>
