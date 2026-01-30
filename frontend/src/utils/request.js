// =============================================================================
// 环境配置 / Environment Configuration
// =============================================================================

// 1. 开发环境 (本地电脑浏览器调试用)
// 使用 localhost，避免因 IP 变动导致连接失败
const LOCAL_HOST = 'http://localhost:8000';

// 2. 生产环境 (上传服务器/打包APP时用)
// 使用相对路径，通过 Nginx 转发到后端 /api
const SERVER_HOST = '';

// 自动判断当前环境
// npm run dev -> 使用开发环境地址
// npm run build -> 使用生产环境地址
const BASE_URL = import.meta.env.MODE === 'development'
  ? LOCAL_HOST
  : SERVER_HOST;

const request = (options) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: options.header || {},
      timeout: options.timeout || 10000,
      success: (res) => {
        // Response Interceptor
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          uni.showToast({
            title: `错误: ${res.statusCode}`,
            icon: 'none'
          });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '网络错误',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};

const uploadFile = (options) => {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + options.url,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData || {},
      header: options.header || {},
      timeout: options.timeout || 30000,
      success: (res) => {
        // Response Interceptor
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const data = JSON.parse(res.data);
            resolve(data);
          } catch (e) {
            resolve(res.data);
          }
        } else {
          uni.showToast({
            title: `上传错误: ${res.statusCode}`,
            icon: 'none'
          });
          reject(res);
        }
      },
      fail: (err) => {
        uni.showToast({
          title: '上传失败',
          icon: 'none'
        });
        reject(err);
      }
    });
  });
};

export { BASE_URL };

export default {
  request,
  uploadFile
};
