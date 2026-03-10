import assert from 'node:assert/strict';

import {
  buildServerUrlWithBaseUrl,
  createApiBaseUrlConfigError,
  resolveApiBaseUrl,
} from '../src/utils/request-config.mjs';

const expectThrowsWithMessage = (fn, expectedMessage) => {
  let actualError = null;
  try {
    fn();
  } catch (error) {
    actualError = error;
  }

  assert.ok(actualError, 'Expected function to throw');
  assert.equal(actualError.message, expectedMessage);
};

const missingBaseUrlMessage = createApiBaseUrlConfigError('').message;
const invalidBaseUrlMessage = createApiBaseUrlConfigError('/api').message;

assert.equal(
  resolveApiBaseUrl({
    envBaseUrl: 'https://example.com',
    requireAbsoluteBaseUrl: true,
  }),
  'https://example.com',
);

assert.equal(
  resolveApiBaseUrl({
    envBaseUrl: 'http://1.2.3.4:8080/',
    requireAbsoluteBaseUrl: true,
  }),
  'http://1.2.3.4:8080',
);

assert.equal(
  buildServerUrlWithBaseUrl('https://example.com', '/api/v1/vision/analyze'),
  'https://example.com/api/v1/vision/analyze',
);

expectThrowsWithMessage(
  () =>
    resolveApiBaseUrl({
      envBaseUrl: '',
      defaultBaseUrl: '',
      requireAbsoluteBaseUrl: true,
    }),
  missingBaseUrlMessage,
);

expectThrowsWithMessage(
  () =>
    resolveApiBaseUrl({
      envBaseUrl: '/api',
      requireAbsoluteBaseUrl: true,
    }),
  invalidBaseUrlMessage,
);

console.log('request-config checks passed');
