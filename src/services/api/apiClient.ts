import axios from 'axios';
import { ENV } from '../../config/env';
import { tokenStorage } from '../auth/tokenStorage';


// eslint-disable-next-line import/no-named-as-default-member
const apiClient = axios.create({
  baseURL: ENV.API_BASE_URL,
  timeout: 4000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.request.use(
  async (config) => {
    const token = await tokenStorage.getAccessToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    // For FormData requests (e.g. image upload), delete default Content-Type header
    // so React Native / OkHttp automatically generates multipart/form-data with boundary!
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers['Authorization'] = 'Bearer ' + token;
            return axios(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = await tokenStorage.getRefreshToken();
      if (!refreshToken) {
        isRefreshing = false;
        // Optionally redirect to login or clear auth context here
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${ENV.API_BASE_URL}/auth/refresh`, { refreshToken });
        const data = response.data;
        await tokenStorage.saveTokens(data.accessToken, data.refreshToken);
        
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${data.accessToken}`;
        originalRequest.headers['Authorization'] = `Bearer ${data.accessToken}`;
        
        processQueue(null, data.accessToken);
        isRefreshing = false;
        
        return axios(originalRequest); // Retry original request once
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        await tokenStorage.clearTokens();
        // Redirect to login handled by AuthContext
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
