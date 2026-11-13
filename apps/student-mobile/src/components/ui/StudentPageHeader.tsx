import React, { useContext } from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppIllustration } from './AppIllustration';
import { COLORS, FONTS, IS_STUDENT_WEB } from '../../constants/theme';
import { useRouter } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';
import { StudentAvatar } from '../../features/student-profile/ProfileCards';

export function StudentPageHeader({ title, subtitle, onHelp, onAvatar, compact = false, onBack, showAvatar = true, backLabel = 'Về trang chủ' }: {
  title?: string; subtitle?: string; onHelp?: () => void; onAvatar?: () => void; compact?: boolean; onBack?: () => void; showAvatar?: boolean; backLabel?: string;
}) {
  const { width } = useWindowDimensions();
  const router = useRouter();
  const openAvatar = onAvatar ?? (() => router.push('/account'));
  if (compact) return <View style={styles.compactHeader}>
    {onBack ? <Pressable accessibilityRole="button" accessibilityLabel={backLabel} onPress={onBack} style={styles.back}>
      <Ionicons name="chevron-back" size={23} color={COLORS.textPrimary} /></Pressable> : <View style={styles.back} />}
    <Text accessibilityRole="header" style={styles.compactTitle}>{title}</Text>
    {showAvatar ? <Pressable onPress={openAvatar} accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" style={styles.smallAvatar}>
      <HeaderAvatar size={42} />
    </Pressable> : <View style={styles.back} />}
  </View>;
  return <View style={styles.header}>
    {showAvatar && <Pressable onPress={openAvatar} accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" style={styles.avatar}>
      <HeaderAvatar size={44} />
    </Pressable>}
    <View style={styles.copy}>
      {title ? <Text accessibilityRole="header" style={styles.title}>{title}</Text>
        : <Text numberOfLines={1} style={[styles.brand, width < 360 && { fontSize: 21 }]}>MathVision<Text style={styles.accent}>Kid</Text>{width >= 360 ? <Text style={styles.spark}> ✦</Text> : null}</Text>}
      {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
    </View>
    {onHelp ? <Pressable accessibilityRole="button" accessibilityLabel="Mẹo chụp bài rõ nét" onPress={onHelp}
      style={({ pressed }) => [styles.help, pressed && { opacity: .7 }]}><Ionicons name="help-circle-outline" size={25} color={COLORS.primaryDark} /></Pressable> : null}
  </View>;
}
function HeaderAvatar({ size }: { size: number }) {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  const profile = useStudentProfile(owner);
  return profile.value ? <StudentAvatar id={profile.value.avatar} photo={profile.value.avatarPhoto} size={size} />
    : <AppIllustration source={IS_STUDENT_WEB ? require('../../../assets/illustrations/web/student-avatar.webp') : require('../../../assets/illustrations/student-avatar.png')} style={{ width: size, height: size }} accessible={false} />;
}
const styles = StyleSheet.create({
  compactHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 52, marginBottom: 16 },
  compactTitle: { flex: 1, textAlign: 'center', fontFamily: FONTS.extraBold, fontSize: 19, color: COLORS.textPrimary },
  back: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  smallAvatar: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0E9FF' },
  header: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 16, minHeight: 50 },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#EEE7FF', overflow: 'hidden', alignItems: 'center', justifyContent: 'center' },
  avatarArt: { width: 44, height: 44 }, copy: { flex: 1, minWidth: 0 },
  brand: { fontFamily: FONTS.black, fontSize: 23, letterSpacing: -.85, color: COLORS.textPrimary },
  accent: { color: '#7044F5' }, spark: { fontSize: 17, color: '#E8AF42' },
  title: { fontFamily: FONTS.extraBold, fontSize: 25, color: COLORS.textPrimary, letterSpacing: -.65 },
  subtitle: { fontFamily: FONTS.regular, fontSize: 11, color: '#6A6488', lineHeight: 16, marginTop: 2 },
  help: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#EDE7FA', alignItems: 'center', justifyContent: 'center' },
});
