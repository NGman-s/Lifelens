<template>
  <view class="container">
    <view class="camera-view">
      <image v-if="capturedImage" :src="capturedImage" mode="aspectFill" class="bg-image"></image>
      <view v-if="!capturedImage" class="camera-placeholder" @click="handleCapture">
        <view class="placeholder-content">
          <text class="placeholder-icon">📷</text>
          <text class="placeholder-text">点击拍照识别食物</text>
        </view>
      </view>
    </view>

    <view class="shutter-area" v-if="!showOverlay">
      <view class="shutter-btn-outer" @click="handleCapture">
        <view class="shutter-btn-inner"></view>
      </view>
    </view>

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

    <BottomNav current="home" />
  </view>
</template>

<script setup>
import { onUnmounted, ref } from 'vue';
import { onHide, onUnload } from '@dcloudio/uni-app';
import { useUserStore } from '@/store/user';
import {
  chooseImage,
  compressImage,
  isCameraModuleUnavailableError,
  isChooseImageCanceledError
} from '@/utils/image';
import { checkCameraPermission, checkGalleryPermission } from '@/utils/permission';
import Api, { formatRequestError } from '@/utils/request';
import ResultOverlay from '@/components/ResultOverlay.vue';
import BottomNav from '@/components/BottomNav.vue';

const userStore = useUserStore();

const capturedImage = ref(null);
const showOverlay = ref(false);
const loading = ref(false);
const loadingAlternatives = ref(false);
const loadingStage = ref(0);
const analysisResult = ref(null);
let stageTimer = null;
let activeAnalysisRequestId = 0;
let activeAlternativesRequestId = 0;

const clearStageTimer = () => {
  if (stageTimer) {
    clearInterval(stageTimer);
    stageTimer = null;
  }
};

const invalidatePendingRequests = () => {
  activeAnalysisRequestId += 1;
  activeAlternativesRequestId += 1;
};

const resetOverlayState = () => {
  clearStageTimer();
  loading.value = false;
  loadingAlternatives.value = false;
  loadingStage.value = 0;
  uni.hideLoading();
};

const closeOverlay = () => {
  invalidatePendingRequests();
  resetOverlayState();
  showOverlay.value = false;
  analysisResult.value = null;
  capturedImage.value = null;
};

const showRequestError = (error, fallbackMessage) => {
  const message = formatRequestError(error, fallbackMessage);
  if (error?.traceId) {
    uni.showModal({
      title: '请求失败',
      content: message,
      showCancel: false
    });
    return;
  }
  uni.showToast({
    title: message,
    icon: 'none',
    duration: 3000
  });
};

const showMediaAccessError = (error, fallbackMessage) => {
  if (isChooseImageCanceledError(error)) {
    return;
  }

  showRequestError(error, fallbackMessage);
};

const startStageTimer = () => {
  clearStageTimer();
  stageTimer = setInterval(() => {
    if (loadingStage.value < 2) {
      loadingStage.value += 1;
    }
  }, 1500);
};

const ensureMediaPermission = async () => {
  const permissionState = {
    hasCameraPermission: false,
    hasGalleryPermission: false
  };

  try {
    await checkCameraPermission();
    permissionState.hasCameraPermission = true;
  } catch (error) {
    permissionState.hasCameraPermission = false;
  }

  try {
    await checkGalleryPermission();
    permissionState.hasGalleryPermission = true;
  } catch (error) {
    permissionState.hasGalleryPermission = false;
  }

  return permissionState;
};

const promptAlbumFallback = () => {
  return new Promise((resolve) => {
    uni.showModal({
      title: '相机暂不可用',
      content: '当前安装包未包含 Camera&Gallery 模块，本次将改为从相册选择图片。修复后请重新打包 APK。',
      confirmText: '打开相册',
      cancelText: '取消',
      success: (res) => {
        resolve(Boolean(res.confirm));
      },
      fail: () => resolve(false)
    });
  });
};

const handleAlbumFallback = async () => {
  const shouldOpenAlbum = await promptAlbumFallback();
  if (!shouldOpenAlbum) {
    return null;
  }

  return chooseImage(['album']);
};

const handleCapture = async () => {
  const permissionState = await ensureMediaPermission();

  if (!permissionState.hasCameraPermission && !permissionState.hasGalleryPermission) {
    uni.showToast({
      title: '请先授予相机或相册权限',
      icon: 'none',
      duration: 3000
    });
    return;
  }

  try {
    const path = await chooseImage(['camera', 'album']);
    await processImage(path);
  } catch (error) {
    if (isChooseImageCanceledError(error)) {
      return;
    }

    if (isCameraModuleUnavailableError(error)) {
      if (!permissionState.hasGalleryPermission) {
        showMediaAccessError(error, '当前安装包未包含相机模块，且相册权限不可用');
        return;
      }

      try {
        const fallbackPath = await handleAlbumFallback();
        if (!fallbackPath) {
          return;
        }
        await processImage(fallbackPath);
      } catch (fallbackError) {
        if (isChooseImageCanceledError(fallbackError)) {
          return;
        }
        showMediaAccessError(fallbackError, '无法打开相册');
      }
      return;
    }

    showMediaAccessError(error, '无法打开相机或相册');
  }
};

const finishAnalysis = (result) => {
  clearStageTimer();
  analysisResult.value = result;
  loading.value = false;
};

const processImage = async (path) => {
  const requestId = ++activeAnalysisRequestId;

  capturedImage.value = path;
  showOverlay.value = true;
  loading.value = true;
  loadingAlternatives.value = false;
  analysisResult.value = null;
  loadingStage.value = 0;
  startStageTimer();

  try {
    const compressedPath = await compressImage(path);
    const res = await Api.uploadFile({
      url: '/api/v1/vision/analyze',
      filePath: compressedPath,
      timeout: 60000,
      formData: {
        user_context: JSON.stringify(userStore.profile)
      }
    });

    if (requestId !== activeAnalysisRequestId) {
      return;
    }

    if (res?.code === 200 && res.data) {
      finishAnalysis(res.data);
      return;
    }

    throw {
      message: res?.message || '识别失败，请重试',
      traceId: res?.trace_id || ''
    };
  } catch (error) {
    if (requestId !== activeAnalysisRequestId) {
      return;
    }
    showRequestError(error, '识别失败，请重试');
    closeOverlay();
  }
};

const handleGenerateAlternatives = async () => {
  if (!analysisResult.value) {
    uni.showToast({
      title: '未发现识别结果',
      icon: 'none'
    });
    return;
  }

  const requestId = ++activeAlternativesRequestId;
  loadingAlternatives.value = true;
  uni.showLoading({
    title: 'AI 正在爆改中...',
    mask: true
  });

  try {
    const res = await Api.request({
      url: '/api/v1/vision/generate-alternatives',
      method: 'POST',
      timeout: 60000,
      header: {
        'content-type': 'application/json'
      },
      data: {
        analysis_result: JSON.parse(JSON.stringify(analysisResult.value)),
        user_context: JSON.parse(JSON.stringify(userStore.profile))
      }
    });

    if (requestId !== activeAlternativesRequestId) {
      return;
    }

    if (res?.code === 200 && res.data) {
      analysisResult.value = {
        ...analysisResult.value,
        alternatives: res.data
      };
      return;
    }

    throw {
      message: res?.message || '方案生成失败，请重试',
      traceId: res?.trace_id || ''
    };
  } catch (error) {
    if (requestId !== activeAlternativesRequestId) {
      return;
    }
    showRequestError(error, '方案生成失败，请重试');
  } finally {
    uni.hideLoading();
    if (requestId === activeAlternativesRequestId) {
      loadingAlternatives.value = false;
    }
  }
};

const handleSave = async () => {
  if (!analysisResult.value) {
    return;
  }

  const savedResult = JSON.parse(JSON.stringify(analysisResult.value));
  const imagePath = savedResult.image_url || capturedImage.value;
  userStore.addHistoryEntry({
    image: imagePath,
    result: savedResult
  });
  closeOverlay();

  try {
    await userStore.syncDietRecord(savedResult);
  } catch (error) {
    console.warn('Failed to sync diet record', error);
    uni.showToast({
      title: '已保存到本地，本次未同步到好友动态',
      icon: 'none',
      duration: 3000
    });
  }
};

const handleDiscard = () => {
  closeOverlay();
};

const cleanupOnLeave = () => {
  if (showOverlay.value || loading.value || loadingAlternatives.value) {
    closeOverlay();
    return;
  }
  resetOverlayState();
};

onHide(cleanupOnLeave);
onUnload(cleanupOnLeave);
onUnmounted(() => {
  invalidatePendingRequests();
  resetOverlayState();
});
</script>

<style lang="scss" scoped>
.container {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: #000;
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

.shutter-area {
  position: absolute;
  bottom: calc(80px + env(safe-area-inset-bottom));
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  pointer-events: none;
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
</style>

