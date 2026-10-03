import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';

/** Shared identity for app-owned launch and sign-in surfaces. */
export function BrandLockup({ compact = false }: { compact?: boolean }) {
  return <View style={styles.container} accessibilityLabel="MathVisionKid — Toán học thật dễ, thật vui!">
    <View style={[styles.iconFrame, compact && styles.compactFrame]}>
      <Image source={require('../../../assets/images/mathvision-icon-v2.png')} style={styles.icon} resizeMode="cover" accessible={false} />
    </View>
    <View style={styles.wordmarkRow}>
      <Text style={[styles.wordmark, compact && styles.smallWordmark]}>MathVision<Text style={styles.accent}>Kid</Text></Text>
      <View style={styles.sparkle}><Text style={styles.sparkleText}>✦</Text></View>
    </View>
    <Text style={styles.tagline}>Toán học thật dễ, thật vui!</Text>
    {!compact ? <LinearGradient colors={['#ECE4FF', '#F5F1FF']} style={styles.promise}>
      <Text style={styles.promiseText}>Hiểu từng bước · Tự tin mỗi ngày</Text>
    </LinearGradient> : null}
  </View>;
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', gap: 12 },
  iconFrame: { width: 164, height: 164, borderRadius: 42, overflow: 'hidden', marginBottom: 12, ...SHADOWS.medium },
  compactFrame: { width: 112, height: 112, borderRadius: 29, marginBottom: 4 },
  icon: { width: '100%', height: '100%' },
  wordmarkRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  wordmark: { fontFamily: FONTS.extraBold, fontSize: 31, letterSpacing: -1, color: COLORS.textPrimary },
  smallWordmark: { fontSize: 29 }, accent: { color: COLORS.primary },
  sparkle: { alignSelf: 'flex-start', marginTop: -7 }, sparkleText: { color: '#EAAF27', fontSize: 21 },
  tagline: { fontFamily: FONTS.regular, fontSize: 15, color: COLORS.textSecondary },
  promise: { paddingHorizontal: 18, paddingVertical: 10, borderRadius: 20, marginTop: 18 },
  promiseText: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.primaryDark },
});
