import React, { useEffect } from 'react';
import { View } from 'react-native';
import { useRouter } from 'expo-router';

/**
 * TabCameraRoute — provides a valid child route for (tabs)/camera,
 * eliminating the Expo Router warning:
 * "[Layout children]: No route named 'camera' exists in nested children".
 *
 * When accessed directly, safely redirects to the root /camera modal
 * with the default HANDWRITING_TEXT flow domain.
 */
export default function TabCameraRoute() {
  const router = useRouter();

  useEffect(() => {
    router.replace({ pathname: '/camera' as any, params: { mode: 'HANDWRITING_TEXT' } });
  }, [router]);

  return <View style={{ flex: 1, backgroundColor: '#000000' }} />;
}
