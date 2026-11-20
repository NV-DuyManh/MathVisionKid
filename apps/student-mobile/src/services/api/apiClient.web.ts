import type { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { studentSession } from '../auth/tokenStorage.web';
import { sessionEvents } from '../auth/sessionEvents';

const { apiClient } = studentSession;
studentSession.onExpired(() => sessionEvents.expired('expired'));
apiClient.interceptors.request.use(config => {
  if (config.url?.startsWith('/student/quizzes')) config.headers.set('X-MathVision-Client', 'confirmed-quiz-v3:web');
  if (config.data instanceof FormData) config.headers.delete('Content-Type');
  if (!config.headers.has('X-Request-ID')) {
    config.headers.set('X-Request-ID', 'req_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now().toString(36));
  }
  return config;
}, error => { throw error; }, { synchronous: true });
apiClient.interceptors.response.use(response => {
  const requestId = response.headers['x-request-id'];
  if (requestId && response.data && typeof response.data === 'object' && !response.data.requestId) response.data.requestId = requestId;
  return response;
}, async (error: AxiosError) => {
  const request = error.config as (InternalAxiosRequestConfig & { _identity?: string }) | undefined;
  const id = request?._identity;
  if (error.response?.status === 403 && id && id === studentSession.getSessionId()
      && !request?.signal?.aborted && request?.url !== '/me' && !request?.url?.startsWith('/auth/')) {
    let isStudent = false;
    try {
      const { data } = await apiClient.get('/me', { timeout: 10000 });
      isStudent = data.role === 'STUDENT' && data.active === true;
    } catch { /* Require a verified profile after a forbidden response. */ }
    if (!isStudent && id === studentSession.getSessionId()) {
      studentSession.clearSession();
      sessionEvents.expired('forbidden');
    }
  }
  throw error;
});
export default apiClient;
