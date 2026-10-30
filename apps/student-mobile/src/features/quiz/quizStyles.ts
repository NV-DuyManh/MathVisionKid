import { StyleSheet } from 'react-native';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';

export const quizStyles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background }, scroll: { flex: 1 },
  content: { width: '100%', maxWidth: 840, alignSelf: 'center', padding: 16, paddingBottom: 40, gap: 16 },
  card: { padding: 20, borderRadius: 24, borderWidth: 1, borderColor: '#E6DCF3', backgroundColor: '#FFF', gap: 14, ...SHADOWS.small },
  heading: { fontFamily: FONTS.extraBold, fontSize: 23, lineHeight: 32, color: COLORS.textPrimary },
  title: { fontFamily: FONTS.bold, fontSize: 18, lineHeight: 26, color: COLORS.textPrimary },
  body: { fontFamily: FONTS.regular, fontSize: 16, lineHeight: 26, color: COLORS.textSecondary },
  small: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: COLORS.textSecondary },
  topic: { fontFamily: FONTS.bold, fontSize: 14, lineHeight: 22, color: COLORS.primaryDark },
  error: { fontFamily: FONTS.semiBold, fontSize: 15, lineHeight: 24, color: '#913E27' },
  success: { fontFamily: FONTS.bold, fontSize: 18, lineHeight: 28, color: '#336148' },
  mascot: { width: 100, height: 108, alignSelf: 'center' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, flexWrap: 'wrap' },
  groups: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  group: { minHeight: 48, paddingVertical: 12, paddingHorizontal: 15, borderRadius: 16, backgroundColor: '#FFF', borderColor: '#DDD0F0', borderWidth: 1 },
  selected: { backgroundColor: '#E9DFFD', borderColor: COLORS.primaryDark },
  input: { minHeight: 58, borderWidth: 2, borderColor: '#A991C8', borderRadius: 16, padding: 14, fontFamily: FONTS.bold, fontSize: 23, color: COLORS.textPrimary, backgroundColor: '#FCFAFF' },
  question: { fontFamily: FONTS.semiBold, fontSize: 20, lineHeight: 33, color: COLORS.textPrimary },
  note: { backgroundColor: '#F4EEFD', borderRadius: 16, padding: 14, gap: 8 },
  stars: { flexDirection: 'row', justifyContent: 'center', gap: 10 },
});
