// =============================================================================
// 后端服务器地址配置 / Backend Configuration
// =============================================================================
// TODO: 请将下面的地址修改为你的云服务器公网 IP 或域名
// 格式示例: 'http://123.45.67.89:8000' 或 'https://api.yourdomain.com'
const SERVER_HOST = 'http://106.55.168.47:8080';

// 统一的基础路径配置
// 既支持 H5 (跨域访问云端)，也支持 App (直接访问云端)
const BASE_URL = SERVER_HOST;

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
