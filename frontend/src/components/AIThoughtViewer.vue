<template>
  <view class="thought-viewer" :class="{ 'is-embedded': isEmbedded }" v-if="visible">
    <!-- Final background dimming -->
    <view class="overlay-dim" v-if="!isEmbedded"></view>

    <!-- Progress Text -->
    <view class="status-panel" :class="{ 'embedded-panel': isEmbedded }">
      <view class="status-header">正在分析 - 请稍候</view>
      <view class="status-text" :class="{ 'glitch-text': stageChanged }">
        {{ stageText }}
      </view>
      <view class="progress-bar-bg">
        <view class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  visible: Boolean,
  isEmbedded: {
    type: Boolean,
    default: false
  },
  stage: {
    type: Number,
    default: 0
  },
  healthConditions: {
    type: Array,
    default: () => []
  }
});

const HEALTH_MAP = {
  'Hypertension': '高血压',
  'Diabetes': '糖尿病',
  'Hyperlipidemia': '高血脂',
  'WeightLoss': '减脂',
  'High Cholesterol': '高胆固醇',
  'Gluten Free': '无麸质',
  'Nut Allergy': '坚果过敏',
  'Lactose Intolerant': '乳糖不耐受'
};

const stageChanged = ref(false);

const progressPercent = computed(() => {
  return Math.min((props.stage + 1) * 33, 100);
});

const stageText = computed(() => {
  const translatedConditions = props.healthConditions
    .map(c => HEALTH_MAP[c] || c);

  const conditions = translatedConditions.length > 0
    ? translatedConditions.join('/')
    : '常规档案';

  switch(props.stage) {
    case 0: return '正在识别物体核心特征';
    case 1: return '分析营养成分与热量';
    case 2: return `对比健康档案: ${conditions}`;
    default: return '处理中...';
  }
});

watch(() => props.stage, () => {
  stageChanged.value = true;
  setTimeout(() => stageChanged.value = false, 500);
});
</script>

<style lang="scss" scoped>
.thought-viewer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 5;
  pointer-events: none;
  overflow: hidden;

  &.is-embedded {
    position: relative;
    height: auto;
    z-index: 1;
  }
}

.overlay-dim {
  position: absolute;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.2);
}

.status-panel {
  position: absolute;
  bottom: 15vh;
  left: 40rpx;
  right: 40rpx;
  background: rgba(255, 255, 255, 0.9);
  padding: 30rpx;
  border-radius: 20rpx;
  box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.2);

  &.embedded-panel {
    position: relative;
    bottom: 0;
    left: 0;
    right: 0;
    background: transparent;
    padding: 20rpx 0;
    box-shadow: none;
    border-radius: 0;
    text-align: center;
  }
}

.status-header {
  color: #86868b;
  font-size: 24rpx;
  margin-bottom: 12rpx;
}

.status-text {
  color: #1d1d1f;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 20rpx;
}

.progress-bar-bg {
  width: 100%;
  height: 8rpx;
  background: #f2f2f7;
  border-radius: 4rpx;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: #007aff;
  transition: width 0.5s ease;
}

.glitch-text {
  /* removed glitch effect as well since user wants to remove effects */
}
</style>
