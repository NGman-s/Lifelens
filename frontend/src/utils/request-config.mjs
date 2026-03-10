const SERVER_PATH_PREFIXES = ['/api', '/uploads'];
const ABSOLUTE_HTTP_URL_PATTERN = /^https?:\/\/[^/\s?#]+/i;

const normalizeBaseUrl = (value = '') => value.trim().replace(/\/+$/, '');
const hasProtocol = (value = '') => /^[a-z][a-z0-9+.-]*:/i.test(value);
const ensureLeadingSlash = (value = '') => (value.startsWith('/') ? value : `/${value}`);
const isAbsoluteHttpUrl = (value = '') => ABSOLUTE_HTTP_URL_PATTERN.test(normalizeBaseUrl(value));

const createApiBaseUrlConfigError = (configuredBaseUrl = '') => {
  const normalizedBaseUrl = normalizeBaseUrl(configuredBaseUrl);
  const hasValue = Boolean(normalizedBaseUrl);
  const message = hasValue
    ? `APK 后端地址无效，请在打包前将 VITE_API_BASE_URL 设置为 http:// 或 https:// 开头的绝对地址。当前值：${normalizedBaseUrl}`
    : 'APK 未配置后端地址，请在打包前设置 VITE_API_BASE_URL，例如 https://example.com 或 http://1.2.3.4:8080';

  return {
    statusCode: 0,
    code: 0,
    message,
    traceId: '',
    payload: null,
  };
};

const resolveApiBaseUrl = ({
  envBaseUrl = '',
  defaultBaseUrl = '',
  requireAbsoluteBaseUrl = false,
} = {}) => {
  const resolvedBaseUrl = normalizeBaseUrl(envBaseUrl) || normalizeBaseUrl(defaultBaseUrl);

  if (!requireAbsoluteBaseUrl) {
    return resolvedBaseUrl;
  }

  if (!resolvedBaseUrl || !isAbsoluteHttpUrl(resolvedBaseUrl)) {
    throw createApiBaseUrlConfigError(resolvedBaseUrl);
  }

  return resolvedBaseUrl;
};

const buildServerUrlWithBaseUrl = (baseUrl = '', path = '') => {
  const normalizedPath = ensureLeadingSlash(path || '');
  return baseUrl ? `${normalizeBaseUrl(baseUrl)}${normalizedPath}` : normalizedPath;
};

export {
  SERVER_PATH_PREFIXES,
  buildServerUrlWithBaseUrl,
  createApiBaseUrlConfigError,
  ensureLeadingSlash,
  hasProtocol,
  isAbsoluteHttpUrl,
  normalizeBaseUrl,
  resolveApiBaseUrl,
};
