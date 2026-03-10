import {
  SERVER_PATH_PREFIXES,
  buildServerUrlWithBaseUrl,
  hasProtocol,
  normalizeBaseUrl,
  resolveApiBaseUrl,
} from './request-config.mjs';

const LOCAL_BACKEND_ORIGIN = 'http://localhost:8080';

const envBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || '');
let defaultBaseUrl = '';
let requireAbsoluteBaseUrl = false;

// #ifndef H5
defaultBaseUrl = import.meta.env.DEV ? LOCAL_BACKEND_ORIGIN : '';
// #endif

// #ifdef APP-PLUS
requireAbsoluteBaseUrl = !import.meta.env.DEV;
// #endif

const BASE_URL = envBaseUrl || defaultBaseUrl;

const parsePayload = (raw) => {
  if (typeof raw !== 'string') {
    return raw;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    return null;
  }
};

const resolveRuntimeBaseUrl = () =>
  resolveApiBaseUrl({
    envBaseUrl,
    defaultBaseUrl,
    requireAbsoluteBaseUrl
  });

const buildServerUrl = (path) => buildServerUrlWithBaseUrl(resolveRuntimeBaseUrl(), path);

const resolveImageUrl = (path) => {
  if (!path) return '';
  if (hasProtocol(path)) return path;
  if (SERVER_PATH_PREFIXES.some((prefix) => path.startsWith(prefix))) {
    try {
      return buildServerUrl(path);
    } catch (error) {
      return path;
    }
  }
  return path;
};

const createRequestError = ({ statusCode = 0, payload = null, fallbackMessage = '请求失败，请稍后重试' }) => {
  const parsedPayload = payload && typeof payload === 'object' ? payload : parsePayload(payload);
  return {
    statusCode,
    code: parsedPayload?.code || statusCode,
    message: parsedPayload?.message || fallbackMessage,
    traceId: parsedPayload?.trace_id || parsedPayload?.traceId || '',
    payload: parsedPayload
  };
};

const formatRequestError = (error, fallbackMessage = '请求失败，请稍后重试') => {
  const message = error?.message || fallbackMessage;
  return error?.traceId ? `${message} (trace_id: ${error.traceId})` : message;
};

const request = (options) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: buildServerUrl(options.url),
      method: options.method || 'GET',
      data: options.data || {},
      header: options.header || {},
      timeout: options.timeout || 10000,
      success: (res) => {
        const payload = parsePayload(res.data) ?? res.data;
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(payload);
          return;
        }
        reject(createRequestError({
          statusCode: res.statusCode,
          payload,
          fallbackMessage: `请求失败 (${res.statusCode})`
        }));
      },
      fail: (err) => {
        let message = '网络连接超时';
        if (err.errMsg && err.errMsg.includes('abort')) message = '请求已取消';
        if (err.errMsg && err.errMsg.includes('timeout')) message = '连接服务器超时';
        if (err.errMsg && err.errMsg.includes('statusCode: null')) message = '网络连接失败，请检查后端地址、服务器状态或 Android 网络权限';
        reject({
          statusCode: 0,
          code: 0,
          message,
          traceId: '',
          payload: null,
          originalError: err
        });
      }
    });
  });
};

const uploadFile = (options) => {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: buildServerUrl(options.url),
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData || {},
      header: options.header || {},
      timeout: options.timeout || 30000,
      success: (res) => {
        const payload = parsePayload(res.data) ?? res.data;
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(payload);
          return;
        }
        reject(createRequestError({
          statusCode: res.statusCode,
          payload,
          fallbackMessage: `上传失败 (${res.statusCode})`
        }));
      },
      fail: (err) => {
        let message = err.errMsg || '上传失败';
        if (err.errMsg && err.errMsg.includes('timeout')) message = '连接服务器超时';
        if (err.errMsg && err.errMsg.includes('statusCode: null')) message = '上传失败，请检查后端地址、服务器状态或 Android 网络权限';
        reject({
          statusCode: 0,
          code: 0,
          message,
          traceId: '',
          payload: null,
          originalError: err
        });
      }
    });
  });
};

export { BASE_URL, buildServerUrl, formatRequestError, resolveImageUrl };

export default {
  request,
  uploadFile
};
