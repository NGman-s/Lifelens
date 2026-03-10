/**
 * Native Permission Handling Utility for Uni-app
 * Focuses on Camera and Gallery permissions for Android and iOS.
 */

const requestScopePermission = (scope, deniedMessage) => {
  return new Promise((resolve, reject) => {
    if (!uni.authorize) {
      reject(new Error(deniedMessage));
      return;
    }
    uni.authorize({
      scope,
      success: () => resolve(true),
      fail: () => reject(new Error(deniedMessage))
    });
  });
};

export const checkCameraPermission = () => {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    const platform = uni.getSystemInfoSync().platform;
    if (platform === 'ios') {
      try {
        const AVCaptureDevice = plus.ios.importClass('AVCaptureDevice');
        const authStatus = AVCaptureDevice.authorizationStatusForMediaType('video');
        if (authStatus === 3) {
          resolve(true);
          return;
        }
        if (authStatus === 0) {
          requestScopePermission('scope.camera', 'iOS相机权限被拒绝')
            .then(resolve)
            .catch(reject);
          return;
        }
        reject(new Error('iOS相机权限被拒绝'));
      } catch (error) {
        reject(error);
      }
      return;
    }

    plus.android.requestPermissions(['android.permission.CAMERA'], (event) => {
      if (event.granted.length > 0) {
        resolve(true);
        return;
      }
      reject(new Error('Android相机权限被拒绝'));
    }, (error) => {
      reject(error);
    });
    // #endif

    // #ifndef APP-PLUS
    resolve(true);
    // #endif
  });
};

export const checkGalleryPermission = () => {
  return new Promise((resolve, reject) => {
    // #ifdef APP-PLUS
    const platform = uni.getSystemInfoSync().platform;
    if (platform === 'ios') {
      try {
        const PHPhotoLibrary = plus.ios.importClass('PHPhotoLibrary');
        const authStatus = PHPhotoLibrary.authorizationStatus();
        if (authStatus === 3 || authStatus === 4 || authStatus === 0) {
          resolve(true);
          return;
        }
        reject(new Error('iOS相册权限被拒绝'));
      } catch (error) {
        reject(error);
      }
      return;
    }

    const permissions = [
      'android.permission.READ_EXTERNAL_STORAGE',
      'android.permission.READ_MEDIA_IMAGES'
    ];
    plus.android.requestPermissions(permissions, (event) => {
      if (event.granted.length > 0) {
        resolve(true);
        return;
      }
      reject(new Error('Android存储权限被拒绝'));
    }, (error) => {
      reject(error);
    });
    // #endif

    // #ifndef APP-PLUS
    resolve(true);
    // #endif
  });
};

export default {
  checkCameraPermission,
  checkGalleryPermission
};
