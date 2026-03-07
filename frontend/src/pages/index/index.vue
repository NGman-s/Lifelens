<template>
  <view class="container">
    <!-- Camera View Finder / Background Image -->
    <view class="camera-view">
      <image v-if="capturedImage" :src="capturedImage" mode="aspectFill" class="bg-image"></image>
      <view v-if="!capturedImage" class="camera-placeholder" @click="handleCapture">
        <view class="placeholder-content">
          <text class="placeholder-icon">📷</text>
          <text class="placeholder-text">点击拍照识别食物</text>
        </view>
      </view>
    </view>

    <!-- Shutter Button Area -->
    <view class="shutter-area" v-if="!showOverlay">
      <view class="shutter-btn-outer" @click="handleCapture">
        <view class="shutter-btn-inner"></view>
      </view>
    </view>

    <!-- Result Overlay (Bottom Sheet) -->
    <ResultOverlay
      :visible="showOverlay"
      :loading="loading"
      :result="analysisResult"
      :stage="loadingStage"
      :healthConditions="userStore.profile.health_conditions"
      :loading-alternatives="loadingAlternatives"
      @close="handleDiscard"
      @save="handleSave"
      @discard="handleDiscard"
      @generate-alternatives="handleGenerateAlternatives"
    />

    <!-- Bottom Navigation -->
    <BottomNav current="home" />

    <!-- Mock Mode Indicator (Subtle) -->
    <view class="mock-indicator" v-if="mockMode" @click="handleLogoClick">M</view>

    <!-- Hidden Logo Trigger for Mock Mode -->
    <view class="logo-trigger" @click="handleLogoClick"></view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '@/store/user';
import { chooseImage, compressImage } from '@/utils/image';
import { checkCameraPermission, checkGalleryPermission } from '@/utils/permission';
import Api from '@/utils/request';
import ResultOverlay from '@/components/ResultOverlay.vue';
import BottomNav from '@/components/BottomNav.vue';

const userStore = useUserStore();

const capturedImage = ref(null);
const showOverlay = ref(false);
const loading = ref(false);
const loadingAlternatives = ref(false);
const loadingStage = ref(0);
const analysisResult = ref(null);
const mockMode = ref(false);
const clickCount = ref(0);

const ensureMediaPermission = async () => {
  let hasCameraPermission = false;
  let hasGalleryPermission = false;

  try {
    await checkCameraPermission();
    hasCameraPermission = true;
  } catch (e) {
    console.warn('Camera permission rejected', e);
  }

  try {
    await checkGalleryPermission();
    hasGalleryPermission = true;
  } catch (e) {
    console.warn('Gallery permission rejected', e);
  }

  return hasCameraPermission || hasGalleryPermission;
};

// Dynamic Mock Data for Demo
const getMockResult = (goal) => {
  const baseResult = {
    main_name: "烤鸡胸肉沙拉",
    total_calories: 350,
    total_traffic_light: "green",
    warning_message: "",
    thought_process: "识别出这是一份烤鸡胸肉沙拉，包含生菜、圣女果和玉米粒。",
    items: [
      {
        name: "烤鸡胸肉沙拉",
        calories: 350,
        unit: "kcal",
        nutrition_tags: ["高蛋白", "低脂"],
        traffic_light: "green"
      }
    ],
    total_analysis: {
      summary: "一份非常健康的减脂餐，蛋白质含量丰富。",
      suggestion: "建议搭配一份全麦面包增加优质碳水。",
      confidence: 0.99
    }
  };

  if (userStore.profile.health_conditions.includes('Hypertension')) {
    baseResult.main_name = "红烧牛肉面";
    baseResult.total_calories = 680;
    baseResult.total_traffic_light = "yellow";
    baseResult.warning_message = "这碗红烧牛肉面的钠含量较高，且属于高碳水食物。建议关注摄入量。";
    baseResult.total_analysis.summary = "高钠高热量的面食。";
    baseResult.total_analysis.suggestion = "建议避开此类重口味汤面，或减少喝汤。";

    // Add mock alternatives for Ramen
    baseResult.mock_alternatives = {
      ordering_hint: "如果您正在点餐，建议将‘日式拉面’换成‘荞麦凉面’（升糖指数更低，热量更少）。",
      cooking_hint: "如果您是自己做，建议将 50% 的面条替换为魔芋丝（大幅度降低碳水和热量）。"
    };
  } else if (goal === 'diabetes') {
    baseResult.total_analysis.suggestion = "蔬菜丰富，升糖指数低，适合您的饮食计划。";
  } else if (goal === 'weight_loss') {
    baseResult.total_analysis.suggestion = "热量控制得当，饱腹感强，非常适合减脂期食用。";
  }

  return baseResult;
};

const handleLogoClick = () => {
  clickCount.value++;
  if (clickCount.value >= 5) {
    mockMode.value = !mockMode.value;
    uni.showToast({
      title: mockMode.value ? '模拟模式开启' : '模拟模式关闭',
      icon: 'none'
    });
    clickCount.value = 0;
  }
};

const handleCapture = async () => {
  try {
    const hasPermission = await ensureMediaPermission();
    if (!hasPermission) {
      // Let chooseImage trigger native permission prompt on first use if supported.
      console.warn('No pre-authorized media permission, fallback to system prompt.');
    }
    // In H5 dev mode, chooseImage works for both camera and album usually
    const path = await chooseImage(['camera', 'album']);
    await processImage(path);
  } catch (e) {
    if (e?.errMsg && e.errMsg.includes('cancel')) {
      return;
    }
    console.error('Capture failed', e);
    uni.showToast({
      title: e?.message || '无法打开相机或相册',
      icon: 'none'
    });
  }
};

const processImage = async (path) => {
  capturedImage.value = path;
  showOverlay.value = true;
  loading.value = true;
  loadingStage.value = 0;

  // Start stage animation
  const stageTimer = setInterval(() => {
    if (loadingStage.value < 2) {
      loadingStage.value++;
    }
  }, 1500);

  try {
    const compressedPath = await compressImage(path);

    if (mockMode.value) {
      setTimeout(() => {
        clearInterval(stageTimer);
        finishAnalysis(getMockResult(userStore.profile.goal));
      }, 3500); // Wait a bit longer to show off the HUD
      return;
    }

    const res = await Api.uploadFile({
      url: '/api/v1/vision/analyze',
      filePath: compressedPath,
      timeout: 60000,
      formData: {
        user_context: JSON.stringify(userStore.profile)
      }
    });

    clearInterval(stageTimer);
    if (res.code === 200) {
      finishAnalysis(res.data);
    } else {
      throw new Error(res.message || '分析失败');
    }
  } catch (e) {
    clearInterval(stageTimer);
    console.error('Analysis error', e);
    uni.showToast({
      title: '识别失败，请重试',
      icon: 'none'
    });
    closeOverlay();
  }
};

const finishAnalysis = (result) => {
  analysisResult.value = result;
  loading.value = false;
  // removed auto-save
};

const handleGenerateAlternatives = async () => {
  console.log('handleGenerateAlternatives: START', analysisResult.value);
  if (!analysisResult.value) {
    console.warn('handleGenerateAlternatives: No analysis result found');
    uni.showToast({
      title: '未发现识别结果',
      icon: 'none'
    });
    return;
  }

  loadingAlternatives.value = true;
  console.log('handleGenerateAlternatives: loadingAlternatives set to true');
  uni.showLoading({
    title: 'AI 正在爆改中...',
    mask: true
  });

  try {
    if (mockMode.value) {
      console.log('handleGenerateAlternatives: Running in mock mode');
      await new Promise(resolve => setTimeout(resolve, 1500));
      const mockAlts = analysisResult.value.mock_alternatives || {
           ordering_hint: "建议换成轻食沙拉",
           cooking_hint: "减少油盐投放"
      };

      analysisResult.value = {
        ...analysisResult.value,
        alternatives: mockAlts
      };
      console.log('handleGenerateAlternatives: Mock alternatives applied', analysisResult.value.alternatives);
    } else {
      console.log('handleGenerateAlternatives: Sending API request...');
      const reqData = {
        analysis_result: JSON.parse(JSON.stringify(analysisResult.value)),
        user_context: JSON.parse(JSON.stringify(userStore.profile))
      };
      console.log('handleGenerateAlternatives: Request data:', reqData);

      const res = await Api.request({
        url: '/api/v1/vision/generate-alternatives',
        method: 'POST',
        timeout: 60000,
        data: reqData
      });

      console.log('handleGenerateAlternatives: API Response received:', res);
      if (res && res.code === 200 && res.data) {
        const newResult = JSON.parse(JSON.stringify(analysisResult.value));
        newResult.alternatives = res.data;
        analysisResult.value = newResult;
        console.log('handleGenerateAlternatives: Success. analysisResult updated.');
      } else {
        const errorMsg = res?.message || '后端返回格式错误';
        console.error('handleGenerateAlternatives: API Error', res);
        throw new Error(errorMsg);
      }
    }
    uni.hideLoading();
  } catch (e) {
    uni.hideLoading();
    console.error('handleGenerateAlternatives: FAILED', e);
    const displayMsg = e.message || '网络连接超时';
    uni.showToast({
      title: '方案生成失败: ' + displayMsg,
      icon: 'none',
      duration: 3500
    });
  } finally {
    loadingAlternatives.value = false;
    console.log('handleGenerateAlternatives: loadingAlternatives set to false');
  }
};

const handleSave = () => {
  // Use server URL if available, otherwise fallback to local temp path
  const imagePath = analysisResult.value?.image_url || capturedImage.value;
  userStore.addHistoryEntry({
    image: imagePath,
    result: analysisResult.value
  });
  closeOverlay();
};

const handleDiscard = () => {
  closeOverlay();
};

const closeOverlay = () => {
  showOverlay.value = false;
  analysisResult.value = null;
  loading.value = false;
  capturedImage.value = null; // Reset camera view
};

onMounted(() => {
  console.log('LifeLens Camera Ready');
});
</script>

<style lang="scss" scoped>
.container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000; /* Camera bg is typically black */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.camera-view {
  flex: 1;
  width: 100%;
  position: relative;
  background-color: #000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.bg-image {
  width: 100%;
  height: 100%;
}

.camera-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #1c1c1e;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  opacity: 0.5;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: grayscale(1);
}

.placeholder-text {
  color: #fff;
  font-size: 14px;
  letter-spacing: 0.5px;
}

/* Shutter Button Area - positioned above bottom nav */
.shutter-area {
  position: absolute;
  bottom: calc(80px + env(safe-area-inset-bottom));
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  pointer-events: none; /* Allow clicks to pass through around the button */
}

.shutter-btn-outer {
  pointer-events: auto;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: transparent;
  transition: all 0.2s ease;

  &:active {
    transform: scale(0.95);
    background-color: rgba(255, 255, 255, 0.1);
  }
}

.shutter-btn-inner {
  width: 56px;
  height: 56px;
  background-color: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Hidden Logo Trigger */
.logo-trigger {
  position: absolute;
  top: 0;
  left: 0;
  width: 100px;
  height: 100px;
  z-index: 100;
}

.mock-indicator {
  position: absolute;
  top: calc(44px + env(safe-area-inset-top));
  right: 20px;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: bold;
  z-index: 20;
}
</style>
