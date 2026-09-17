import { Platform } from 'react-native';
import Constants from 'expo-constants';

export function resolveApiBaseUrl(): string {
  const isWeb = Platform.OS === 'web';
  const isAndroid = Platform.OS === 'android';
  
  // Determine if it's a physical device. Expo Constants.isDevice is true for physical devices.
  const isPhysicalDevice = Constants.isDevice;

  // 1. Production
  if (!__DEV__) {
    const prodUrl = process.env.EXPO_PUBLIC_API_BASE_URL || 'https://api.mathvisionkids.com/api/v1';
    let url = prodUrl;
    if (url.endsWith('/')) url = url.slice(0, -1);
    return url;
  }

  // 2. DEV Mode Override
  // Use EXPO_PUBLIC_DEV_API_BASE_URL if set, else fall back to EXPO_PUBLIC_API_BASE_URL
  const overrideUrl = process.env.EXPO_PUBLIC_DEV_API_BASE_URL || process.env.EXPO_PUBLIC_API_BASE_URL;
  let resolvedUrl = '';
  let selectedSource = 'UNKNOWN';

  const isLoopback = (url: string) => {
    return url.includes('localhost') || url.includes('127.0.0.1') || url.includes('::1') || url.includes('10.0.2.2');
  };

  if (overrideUrl) {
    if (isPhysicalDevice && isLoopback(overrideUrl)) {
      // Reject loopback on physical device
    } else {
      resolvedUrl = overrideUrl;
      selectedSource = 'ENV_OVERRIDE';
    }
  }

  // 3. Dynamic Metro Host (if not resolved by valid override)
  let metroHostUri = '';
  if (!resolvedUrl && !isWeb) {
    // Try multiple sources robustly
    metroHostUri = Constants.expoConfig?.hostUri || Constants.manifest?.hostUri || Constants.manifest2?.extra?.expoGo?.debuggerHost || '';
    if (metroHostUri) {
      // Extract hostname robustly from values like 172.16.3.96:8081, exp://..., http://...
      const match = metroHostUri.match(/^(?:https?:\/\/|exp:\/\/)?([^\/:]+)/i);
      const host = match ? match[1] : metroHostUri.split(':')[0];
      
      if (host) {
        resolvedUrl = `http://${host}:8080/api/v1`;
        selectedSource = 'METRO_DYNAMIC';
      }
    }
  }

  // 4. Fallbacks for Web / Emulator if still no valid resolvedUrl
  if (!resolvedUrl) {
    if (isWeb) {
      resolvedUrl = 'http://127.0.0.1:8080/api/v1';
      selectedSource = 'WEB';
    } else if (!isPhysicalDevice) {
      resolvedUrl = isAndroid ? 'http://10.0.2.2:8080/api/v1' : 'http://127.0.0.1:8080/api/v1';
      selectedSource = 'EMULATOR';
    } else {
      // PHYSICAL_INVALID: Missing Metro host and no valid override on physical device
      selectedSource = 'ERROR';
      console.error('DEV_BACKEND_HOST_UNRESOLVED: Không xác định được địa chỉ máy tính chạy backend. Hãy kiểm tra Expo LAN hoặc cấu hình DEV API URL.');
      throw new Error('DEV_BACKEND_HOST_UNRESOLVED');
    }
  }

  if (resolvedUrl.endsWith('/')) {
    resolvedUrl = resolvedUrl.slice(0, -1);
  }

  console.log('[API_RESOLVER]', {
    platform: Platform.OS,
    physicalDevice: isPhysicalDevice,
    dev: __DEV__,
    override: overrideUrl ? 'redacted-host-only' : 'NOT_SET',
    metroHost: metroHostUri,
    selectedSource,
    resolvedBaseURL: resolvedUrl
  });

  return resolvedUrl;
}
