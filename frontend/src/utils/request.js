const LOCAL_BACKEND_ORIGIN = 'http://localhost:8080';
const SERVER_PATH_PREFIXES = ['/api', '/uploads'];

const normalizeBaseUrl = (value = '') => value.trim().replace(/\/+$/, '');
const hasProtocol = (value = '') => /^[a-z][a-z0-9+.-]*:/i.test(value);
const ensureLeadingSlash = (value = '') => (value.startsWith('/') ? value : `/${value}`);

const envBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL || '');
let defaultBaseUrl = '';

// #ifndef H5
defaultBaseUrl = import.meta.env.DEV ? LOCAL_BACKEND_ORIGIN : '';
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

const buildServerUrl = (path) => {
  const normalizedPath = ensureLeadingSlash(path || '');
  return BASE_URL ? `${BASE_URL}${normalizedPath}` : normalizedPath;
};

const resolveImageUrl = (path) => {
  if (!path) return '';
  if (hasProtocol(path)) return path;
  if (SERVER_PATH_PREFIXES.some((prefix) => path.startsWith(prefix))) {
    return buildServerUrl(path);
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
        reject({
          statusCode: 0,
          code: 0,
          message: err.errMsg || '上传失败',
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
