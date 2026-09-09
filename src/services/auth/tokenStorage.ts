import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const REFRESH_TOKEN_KEY = 'mathvision_refresh_token';
const ACCESS_TOKEN_KEY = 'mathvision_access_token';

export const tokenStorage = {
  async saveTokens(accessToken: string, refreshToken: string) {
    if (Platform.OS === 'web') {
      try {
        localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      } catch (e) {
        console.error('Error saving tokens on web', e);
      }
      return;
    }
    try {
      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
    } catch (e) {
      console.error('Error saving tokens', e);
    }
  },

  async clearTokens() {
    if (Platform.OS === 'web') {
      try {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      } catch (e) {
        console.error('Error clearing tokens on web', e);
      }
      return;
    }
    try {
      await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    } catch (e) {
      console.error('Error clearing tokens', e);
    }
  },

  async getAccessToken() {
    if (Platform.OS === 'web') {
      try {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
      } catch {
        return null;
      }
    }
    try {
      return await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
    } catch {
      return null;
    }
  },

  async getRefreshToken() {
    if (Platform.OS === 'web') {
      try {
        return localStorage.getItem(REFRESH_TOKEN_KEY);
      } catch {
        return null;
      }
    }
    try {
      return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
    } catch {
      return null;
    }
  }
};
