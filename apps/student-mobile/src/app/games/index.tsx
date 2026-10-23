import React, { useContext } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { COLORS, FONTS, SIZES } from '../../constants/theme';

export default function GamesScreen() {
  const auth = useContext(AuthContext);
  const router = useRouter();

  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;

  return <SafeAreaView style={styles.screen} edges={['top', 'left', 'right', 'bottom']}>
    <View style={styles.header}>
      <Pressable accessibilityRole="button" accessibilityLabel="Quay lại tab Của em"
        onPress={() => router.dismissTo('/(tabs)/profile')}
        style={({ pressed }) => [styles.back, pressed && styles.pressed]}>
        <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} accessible={false} />
      </Pressable>
      <Text accessibilityRole="header" style={styles.title}>Trò chơi rèn luyện cho em</Text>
      <View style={styles.placeholder} />
    </View>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  header: {
    minHeight: 64, flexDirection: 'row', alignItems: 'center', paddingHorizontal: SIZES.medium,
    paddingVertical: SIZES.base, width: '100%', maxWidth: 620, alignSelf: 'center',
  },
  back: {
    width: SIZES.minTouchTarget, height: SIZES.minTouchTarget, borderRadius: SIZES.minTouchTarget / 2,
    justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.primaryLight,
  },
  title: {
    flex: 1, minWidth: 0, paddingHorizontal: SIZES.small, fontFamily: FONTS.extraBold,
    fontSize: 20, lineHeight: 28, textAlign: 'center', color: COLORS.textPrimary,
  },
  placeholder: { width: SIZES.minTouchTarget },
  pressed: { opacity: .7 },
});
