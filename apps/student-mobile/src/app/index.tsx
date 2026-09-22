import React, { useEffect, useContext } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../constants/theme';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';

export default function SplashScreen() {
  const router = useRouter();
  const auth = useContext(AuthContext);

  useEffect(() => {
    // S00 - SPLASH logic
    const timer = setTimeout(() => {
      if (auth?.isAuthenticated) {
        router.replace('/(tabs)' as any);
      } else {
        router.replace('/login');
      }
    }, 1500);

    return () => clearTimeout(timer);
  }, [router, auth?.isAuthenticated]);

  return (
    <View style={styles.container}>
      <Ionicons name="scan-circle" size={80} color={COLORS.primary} style={styles.icon} />
      <Text style={styles.title}>MathVision Kids</Text>
      <Text style={styles.tagline}>Chụp bài • Hiểu lỗi • Tự sửa</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    marginBottom: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 8,
  },
  tagline: {
    fontSize: 16,
    color: COLORS.textSecondary,
    fontWeight: '500',
  }
});
