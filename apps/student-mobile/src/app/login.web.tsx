import { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { workspaceOrigin } from '../config/workspaceOrigin.web';

export default function LoginScreen() {
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    const sharedPortal = /^\/(?:study|learn)(?:\/|$)/.test(window.location.pathname);
    void Promise.resolve().then(() => {
      window.location.replace(sharedPortal ? '/login' : `${workspaceOrigin('PORTAL')}/login`);
    }).catch(() => setUnavailable(true));
  }, []);

  return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, padding: 24 }}>
    {!unavailable && <ActivityIndicator />}
    <Text accessibilityRole={unavailable ? 'alert' : undefined} accessibilityLiveRegion="polite">
      {unavailable ? 'Chưa mở được trang đăng nhập. Vui lòng thử lại sau.' : 'Đang mở trang đăng nhập…'}
    </Text>
  </View>;
}
