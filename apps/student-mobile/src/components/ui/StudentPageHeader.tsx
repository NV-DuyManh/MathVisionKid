import React from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppIllustration } from './AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';

export function StudentPageHeader({ title, subtitle, onHelp, onAvatar, compact = false, onBack }: {
  title?: string; subtitle?: string; onHelp?: () => void; onAvatar?: () => void; compact?: boolean; onBack?: () => void;
}) {
  const { width } = useWindowDimensions();
  if (compact) return <View style={styles.compactHeader}>
    {onBack ? <Pressable accessibilityRole="button" accessibilityLabel="Về trang chủ" onPress={onBack} style={styles.back}>
      <Ionicons name="chevron-back" size={23} color={COLORS.textPrimary} /></Pressable> : <View style={styles.back} />}
    <Text accessibilityRole="header" style={styles.compactTitle}>{title}</Text>
    <Pressable onPress={onAvatar} disabled={!onAvatar} accessibilityRole={onAvatar ? 'button' : undefined}
      accessibilityLabel={onAvatar ? 'Trang cá nhân của em' : undefined} style={styles.smallAvatar}>
      <AppIllustration source={require('../../../assets/illustrations/student-avatar.png')} style={styles.smallAvatar} accessible={false} />
    </Pressable>
  </View>;
  return <View style={styles.header}>
    <Pressable onPress={onAvatar} disabled={!onAvatar} accessibilityRole={onAvatar ? 'button' : undefined}
      accessibilityLabel={onAvatar ? 'Trang cá nhân của em' : undefined} style={styles.avatar}>
      <AppIllustration source={require('../../../assets/illustrations/student-avatar.png')} style={styles.avatarArt} accessible={false} />
    </Pressable>
    <View style={styles.copy}>
      {title ? <Text accessibilityRole="header" style={styles.title}>{title}</Text>
        : <Text numberOfLines={1} style={[styles.brand, width < 360 && { fontSize: 21 }]}>MathVision<Text style={styles.accent}>Kid</Text>{width >= 360 ? <Text style={styles.spark}> ✦</Text> : null}</Text>}
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
    {onHelp ? <Pressable accessibilityRole="button" accessibilityLabel="Mẹo chụp bài rõ nét" onPress={onHelp}
      style={({ pressed }) => [styles.help, pressed && { opacity: .7 }]}><Ionicons name="help-circle-outline" size={25} color={COLORS.primaryDark} /></Pressable> : null}
  </View>;
}
const styles = StyleSheet.create({
  compactHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 52, marginBottom: 16 },
  compactTitle: { flex: 1, textAlign: 'center', fontFamily: FONTS.extraBold, fontSize: 19, color: COLORS.textPrimary },
  back: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  smallAvatar: { width: 42, height: 42, borderRadius: 21, backgroundColor: '#F0E9FF' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 16, minHeight: 50 },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#EEE7FF', overflow: 'hidden', alignItems: 'center', justifyContent: 'center' },
  avatarArt: { width: 44, height: 44 }, copy: { flex: 1, minWidth: 0 },
  brand: { fontFamily: FONTS.black, fontSize: 23, letterSpacing: -.85, color: COLORS.textPrimary },
  accent: { color: '#7044F5' }, spark: { fontSize: 17, color: '#E8AF42' },
  title: { fontFamily: FONTS.extraBold, fontSize: 25, color: COLORS.textPrimary, letterSpacing: -.65 },
  subtitle: { fontFamily: FONTS.regular, fontSize: 11, color: '#6A6488', lineHeight: 16, marginTop: 2 },
  help: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#EDE7FA', alignItems: 'center', justifyContent: 'center' },
});
