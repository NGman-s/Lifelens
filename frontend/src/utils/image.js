/**
 * Camera and Image Processing Utilities
 */

const getErrorMessage = (error) => {
  if (!error) {
    return '';
  }

  return [
    error.errMsg,
    error.message,
    error.code,
    error.reason
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
};

const CAMERA_MODULE_ERROR_PATTERNS = [
  /未打包.*camera/,
  /camera.*未打包/,
  /camera.*模块/,
  /module.*camera/,
  /plus\.camera/,
  /getcamera/,
  /camera.*not.*(include|found|exist|packag|avail)/,
  /not.*(include|found|exist|packag|avail).*(camera|plus\.camera)/
];

const CHOOSE_IMAGE_CANCEL_PATTERNS = [
  /cancel$/,
  /cancelled/,
  /user cancelled/,
  /用户取消/,
  /resultcode is wrong/
];

/**
 * Capture an image from camera or choose from gallery
 * @param {string[]} sourceType
 * @returns {Promise<string>} - temp file path of the chosen image
 */
export const chooseImage = (sourceType = ['camera', 'album']) => {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: sourceType,
      success: (res) => {
        resolve(res.tempFilePaths[0]);
      },
      fail: (err) => {
        reject(err);
      }
    });
  });
};

/**
 * Detects whether the native camera module is missing from the packaged app.
 * @param {Error|Object} error
 * @returns {boolean}
 */
export const isCameraModuleUnavailableError = (error) => {
  const message = getErrorMessage(error);
  return CAMERA_MODULE_ERROR_PATTERNS.some((pattern) => pattern.test(message));
};

/**
 * Detects whether chooseImage failed because the user cancelled the picker/camera flow.
 * Covers App 端相机返回时的 "resultCode is wrong" 特殊情况。
 * @param {Error|Object|string} error
 * @returns {boolean}
 */
export const isChooseImageCanceledError = (error) => {
  if (typeof error === 'string') {
    return CHOOSE_IMAGE_CANCEL_PATTERNS.some((pattern) => pattern.test(error.toLowerCase()));
  }

  const message = getErrorMessage(error);
  return CHOOSE_IMAGE_CANCEL_PATTERNS.some((pattern) => pattern.test(message));
};

/**
 * Compress an image to reduce size while maintaining acceptable quality for AI analysis
 * @param {string} src - source image path
 * @param {number} quality - compression quality (0-100)
 * @returns {Promise<string>} - temp file path of the compressed image
 */
export const compressImage = (src, quality = 60) => {
  return new Promise((resolve, reject) => {
    // Check if uni.compressImage is supported (e.g., in H5 it might not be available)
    if (!uni.compressImage) {
      console.warn('uni.compressImage is not supported on this platform. Skipping compression.');
      resolve(src);
      return;
    }

    uni.compressImage({
      src: src,
      quality: quality,
      success: (res) => {
        resolve(res.tempFilePath);
      },
      fail: (err) => {
        // If compression fails, we might still want to proceed with the original image
        console.warn('Compression failed, using original image', err);
        resolve(src);
      }
    });
  });
};

export default {
  chooseImage,
  isCameraModuleUnavailableError,
  isChooseImageCanceledError,
  compressImage
};
