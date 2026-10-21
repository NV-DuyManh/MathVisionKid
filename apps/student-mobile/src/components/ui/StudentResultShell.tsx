import React from 'react';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { AppHeader } from './AppHeader';
import { AppIllustration } from './AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';

/** Presentation only. Each result route keeps its own server checks and actions. */
export function StudentResultShell({ title, success = false, children }: { title: string; success?: boolean; children: React.ReactNode }) {
  const { width, height, fontScale } = useWindowDimensions();
  const wide = width >= 1000 && fontScale <= 1.3;
  return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <View style={styles.header}><AppHeader title={title} showBack /></View>
    <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={[styles.content, { minHeight: Math.max(0, height - 90) }, wide && styles.wide]}>
      <LinearGradient colors={success ? ['#F1EBFF', '#F8F2E7'] : ['#F0EAFC', '#F8F5FE']} style={[styles.hero, wide && styles.heroWide]}>
        <AppIllustration highResolution source={success ? require('../../../assets/illustrations/mathvision-star.png') : require('../../../assets/illustrations/approved/practice.webp')} style={[styles.art, wide && styles.artWide]} accessible={false} />
        <View style={styles.heroCopy}><Text style={styles.eyebrow}>CÙNG SAO NHỎ</Text><Text style={styles.title}>{success ? 'Thêm một bước tiến!' : 'Cùng nhìn lại nhé'}</Text><Text style={styles.copy}>{success ? 'Giữ lại cách em đã nghĩ và thử thêm một bài mới.' : 'Đọc từng ý, đối chiếu với bài rồi chọn điều em muốn làm tiếp.'}</Text></View>
      </LinearGradient>
      <View style={[styles.result, wide && styles.resultWide]}>{children}</View>
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background }, header: { width: '100%', maxWidth: 1120, alignSelf: 'center' },
  content: { flexGrow: 1, width: '100%', maxWidth: 1120, alignSelf: 'center', padding: 22, paddingBottom: 32, gap: 23, justifyContent: 'center' },
  wide: { flexDirection: 'row', alignItems: 'center', gap: 38, paddingVertical: 35 },
  hero: { borderRadius: 28, borderWidth: 1, borderColor: '#E9DFF8', padding: 22, flexDirection: 'row', alignItems: 'center', gap: 16 }, heroWide: { width: 340, minHeight: 500, flexDirection: 'column', justifyContent: 'center', padding: 32, gap: 30 },
  heroCopy: { flex: 1, minWidth: 0 }, art: { width: 94, height: 114 }, artWide: { width: 230, height: 225 },
  eyebrow: { fontFamily: FONTS.extraBold, fontSize: 10, letterSpacing: 1.2, color: '#8A70AB', marginBottom: 9 },
  title: { fontFamily: FONTS.extraBold, fontSize: 23, lineHeight: 30, color: COLORS.textPrimary, marginBottom: 9 }, copy: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: '#756487' },
  result: { padding: 21, backgroundColor: '#FFF', borderRadius: 27, borderWidth: 1, borderColor: '#EBE4F6', width: '100%', gap: 7 }, resultWide: { flex: 1, width: undefined, minWidth: 0, maxWidth: 660 },
});
