import React, { useCallback, useState } from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppIllustration as Image } from '../ui/AppIllustration';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { recognitionAnalyticsStore } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildLearningActivity } from '../../features/home/learningActivity';
import { loadLessons } from '../../features/tutoring/learningHistory';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';

const ART = {
  avatar: require('../../../assets/illustrations/student-avatar.png'),
  mascot: require('../../../assets/illustrations/mathvision-star.png'),
  saved: require('../../../assets/illustrations/approved/saved.webp'),
  practice: require('../../../assets/illustrations/approved/practice.webp'),
  progress: require('../../../assets/illustrations/approved/progress.webp'),
  calculator: require('../../../assets/illustrations/approved/calculator.webp'),
  crown: require('../../../assets/illustrations/encouragement-crown.png'),
  flame: require('../../../assets/illustrations/streak-flame.png'),
  star: require('../../../assets/illustrations/reward-star.png'),
};

type Props = {
  userName: string;
  userKey?: string;
  onAcquire: () => void;
  onArithmetic: () => void;
  onPractice: (grade?: 1 | 2 | 3 | 4 | 5) => void;
  onTips: () => void;
  onPrivacy: () => void;
};

export function HomeDashboard({ userName, userKey, onAcquire, onArithmetic, onPractice, onTips, onPrivacy }: Props) {
  const router = useRouter();
  const { width, fontScale } = useWindowDimensions();
  const [availableWidth, setAvailableWidth] = useState(width);
  const desktop = availableWidth >= 1000 && fontScale <= 1.3;
  const wide = availableWidth >= 540 && fontScale <= 1.3;
  const roomyText = availableWidth < 350 || fontScale > 1.3;
  const [activity, setActivity] = useState<ReturnType<typeof buildLearningActivity> | null>(null);
  const [historyUnavailable, setHistoryUnavailable] = useState(false);
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true;
    setActivity(null);
    setHistoryUnavailable(false);
    Promise.all([recognitionAnalyticsStore.init(), loadLessons(userKey)]).then(([, lessons]) => {
      if (active) {
        setActivity(buildLearningActivity([...recognitionAnalyticsStore.getSessions(), ...lessons.map(item => ({ sessionId: item.id, timestamp: item.timestamp }))]));
        setHistoryUnavailable(false);
      }
    }).catch(() => { if (active) setHistoryUnavailable(true); });
    return () => { active = false; };
  }, [userKey]));
  const quickActions = [
    { title: 'Bài đã lưu', description: 'Xem lại bài làm của em', image: ART.saved, background: '#F4EFFF', onPress: () => router.push('/(tabs)/profile') },
    { title: 'Luyện tập', description: 'Làm bài theo chủ đề', image: ART.practice, background: '#F9F4E9', onPress: () => router.push('/(tabs)/lessons' as any) },
    { title: 'Tiến bộ', description: 'Xem hành trình học tập', image: ART.progress, background: '#EFF5F0', onPress: () => router.push('/(tabs)/achievements' as any) },
    { title: 'Máy tính', description: 'Số thường, phân số, chia có dư', image: ART.calculator, background: '#F0EBFF', onPress: () => setCalculatorOpen(true) },
  ];

  const hero = <>
    <LinearGradient colors={['#F7F5FF', '#F0EBFF', '#EAE3FD']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.hero, roomyText && styles.heroRoomy, wide && styles.heroWide]}>
      <View style={styles.heroBubble} accessible={false} />
      <View style={styles.heroMintBubble} accessible={false} />
      <Text style={styles.mathPlus} accessible={false}>+</Text>
      <Text style={styles.mathDivision} accessible={false}>÷</Text>
      <Image source={ART.mascot} style={[styles.heroMascot, roomyText && styles.heroMascotRoomy, wide && styles.heroMascotWide]} resizeMode="contain" accessible={false} />
      {wide && <Text style={styles.eyebrow}>MỖI BÀI TOÁN, MỘT KHÁM PHÁ</Text>}
      <View style={styles.greetingRow}>
        <Text style={[styles.greeting, wide && styles.greetingWide]} accessibilityRole="header" accessibilityLabel={`Chào ${userName}!`}>Chào em!</Text>
        <View style={styles.greetingSparkle} accessible={false}>
          <View style={[styles.sparkleStroke, styles.greetingStrokeOne]} />
          <View style={[styles.sparkleStroke, styles.greetingStrokeTwo]} />
        </View>
      </View>
      <Text style={[styles.heroDescription, roomyText && styles.heroDescriptionRoomy, wide && styles.heroDescriptionWide]}>Cùng MathVisionKid khám phá Toán học theo cách thật thú vị nhé!</Text>
      <Pressable onPress={onAcquire} accessibilityRole="button" accessibilityLabel="Chụp bài toán" accessibilityHint="Mở máy ảnh ngay để chụp đề hoặc bài em đã làm" style={({ pressed }) => [styles.captureButton, roomyText && styles.captureButtonRoomy, wide && styles.captureButtonWide, pressed && styles.pressed]}>
        <LinearGradient colors={['#7D5AEC', '#6C4AF5', '#5F40ED']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} pointerEvents="none" />
        <Ionicons name="camera" size={21} color={COLORS.surface} accessible={false} />
        <Text style={[styles.captureLabel, wide && styles.captureLabelWide]}>Chụp bài toán</Text>
        <Ionicons name="chevron-forward" size={17} color={COLORS.surface} accessible={false} />
      </Pressable>
    </LinearGradient>

  </>;
  const utilities = <>
    <View style={styles.sectionHeading}>
      <Text style={styles.sectionTitle} accessibilityRole="header">Tiện ích nhanh</Text>
      <Pressable onPress={() => router.push('/(tabs)/lessons' as any)} accessibilityRole="button" accessibilityLabel="Xem tất cả bài luyện tập lớp 1 đến lớp 5" style={({ pressed }) => [styles.sectionLink, pressed && styles.pressed]}>
        <Text style={styles.sectionLinkText}>Xem tất cả</Text>
        <Ionicons name="chevron-forward" size={15} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    <View style={[styles.quickGrid, wide && styles.quickGridWide]}>
      {(wide ? quickActions : quickActions.slice(0, 3)).map(action => <Pressable key={action.title} onPress={action.onPress} accessibilityRole="button" accessibilityLabel={action.title === 'Máy tính' ? 'Mở máy tính bỏ túi' : `${action.title}. ${action.description}`} style={({ pressed }) => [styles.quickCard, { backgroundColor: action.background }, roomyText && styles.quickCardWide, wide && styles.quickCardTablet, desktop && styles.quickCardDesktop, pressed && styles.pressed]}>
        <Image source={action.image} style={[styles.quickArt, wide && styles.quickArtTablet, desktop && styles.quickArtDesktop]} resizeMode="contain" accessible={false} />
        <View style={wide && !desktop && styles.quickCopyTablet}><View style={styles.quickTitleRow}>
          <Text style={[styles.quickTitle, wide && styles.quickTitleWide]}>{action.title}</Text>
          <View style={styles.cardArrow}><Ionicons name="chevron-forward" size={13} color={COLORS.primaryDark} accessible={false} /></View>
        </View>
        <Text style={[styles.quickDescription, wide && styles.quickDescriptionWide]}>{action.description}</Text></View>
      </Pressable>)}
    </View>

    {!wide && <Pressable accessibilityRole="button" accessibilityLabel="Mở máy tính bỏ túi" onPress={() => setCalculatorOpen(true)}
      style={({ pressed }) => [styles.calculatorCard, pressed && styles.pressed]}>
      <Image source={ART.calculator} style={styles.calculatorArt} accessible={false} />
      <View style={styles.lessonCopy}><Text style={styles.calculatorTitle}>Máy tính bỏ túi</Text><Text style={styles.quickDescription}>Số thường · Phân số · Chia có dư</Text></View>
      <Ionicons name="chevron-forward" size={20} color={COLORS.primaryDark} accessible={false} />
    </Pressable>}


  </>;
  const learningActivity = <>
    <View style={[styles.activityCard, desktop && styles.activityDesktop, wide && styles.activityWide, SHADOWS.small]}>
      <View style={styles.activityCopy}>
        <View style={styles.activityTitleRow}>
          <Image source={ART.flame} style={styles.flame} resizeMode="contain" accessible={false} />
          <Text style={styles.sectionTitle} accessibilityRole="header">Chuỗi học tập</Text>
        </View>
        <View style={styles.streakTitleRow}>
          <Image source={ART.star} style={styles.streakStar} resizeMode="contain" accessible={false} />
          <Text style={styles.streakTitle}>{activity && activity.streak > 0 ? `${activity.streak} ngày liên tiếp!` : 'Bắt đầu hôm nay!'}</Text>
        </View>
      </View>
      <Image source={ART.crown} style={styles.crown} resizeMode="contain" accessible={false} />
      <Text style={styles.activityDescription}>
        {historyUnavailable ? 'Chưa tải được lịch sử. Em vẫn có thể bắt đầu bài mới.'
          : activity?.completedToday ? 'Siêu quá! Hãy giữ thói quen học Toán mỗi ngày nhé!'
          : activity?.streak ? 'Lưu thêm bài hôm nay để nối tiếp chuỗi của em nhé!'
          : 'Lưu bài đầu tiên, cùng bắt đầu hành trình nhé!'}
      </Text>
      {activity && <View style={styles.week}>
        <View style={styles.weekConnector} accessible={false} />
        {activity.days.map(day => <View key={day.label} style={styles.weekDay} accessibilityLabel={`${day.label}, ${day.date}: ${day.completed ? 'đã lưu bài' : 'chưa lưu bài'}`} accessible>
          <View style={[styles.dayCircle, day.completed && styles.dayCircleDone]}>
            {day.completed ? <Image source={ART.star} style={styles.rewardStar} resizeMode="contain" accessible={false} /> : <Ionicons name="star" size={19} color="#C2C4D5" accessible={false} />}
          </View>
          <Text style={styles.dayLabel}>{day.label}</Text>
        </View>)}
      </View>}
      <Text style={styles.historyNote}>Chuỗi tính theo bài đã lưu trên thiết bị này.</Text>
    </View>

  </>;
  const gradePicker = wide ? <View style={styles.gradePicker}>
    <Text style={styles.gradePrompt}>Luyện tập theo lớp</Text>
    <View style={styles.gradeChoices}>{([1, 2, 3, 4, 5] as const).map(grade =>
      <Pressable key={grade} accessibilityRole="button" accessibilityLabel={`Luyện tập lớp ${grade}`} onPress={() => onPractice(grade)}
        style={({ pressed }) => [styles.gradeChoice, pressed && styles.pressed]}><Text style={styles.gradeLabel}>Lớp {grade}</Text></Pressable>)}</View>
  </View> : null;
  const recommendations = <>
    <View style={styles.sectionHeading}>
      <Text style={styles.sectionTitle} accessibilityRole="header">Bài học gợi ý cho em</Text>
      <Pressable onPress={() => router.push('/(tabs)/lessons' as any)} accessibilityRole="button" style={({ pressed }) => [styles.sectionLink, pressed && styles.pressed]}>
        <Text style={styles.sectionLinkText}>Xem thêm</Text>
        <Ionicons name="chevron-forward" size={15} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    <View style={[styles.lessonGrid, wide && !desktop && styles.lessonGridTablet]}>
      <Pressable onPress={() => onPractice(1)} accessibilityRole="button" accessibilityLabel="Luyện phép cộng và trừ trong phạm vi 100, lớp 1" style={({ pressed }) => [styles.lessonCard, wide && styles.lessonCardWide, pressed && styles.pressed]}>
        <View style={styles.lessonSymbol}><Ionicons name="add" size={24} color={COLORS.surface} accessible={false} /></View>
        <View style={styles.lessonCopy}><Text style={[styles.lessonTitle, wide && styles.lessonTitleWide]}>Phép cộng đến 100</Text><Text style={styles.lessonDetail}>Lớp 1 · Có lời văn</Text>{wide && <Text style={styles.lessonDescription}>Đọc đề, xem gợi ý và thử viết lời giải.</Text>}</View>
      </Pressable>
      <Pressable onPress={onArithmetic} accessibilityRole="button" accessibilityLabel="Đọc phép tính. Kiểm tra phép cộng và trừ đặt dọc" style={({ pressed }) => [styles.lessonCard, styles.arithmeticCard, wide && styles.lessonCardWide, pressed && styles.pressed]}>
        <View style={[styles.lessonSymbol, styles.arithmeticSymbol]}><Ionicons name="calculator-outline" size={24} color={COLORS.surface} accessible={false} /></View>
        <View style={styles.lessonCopy}><Text style={[styles.lessonTitle, wide && styles.lessonTitleWide]}>Đọc phép tính</Text><Text style={styles.lessonDetail}>Cộng, trừ đặt dọc</Text>{wide && <Text style={styles.lessonDescription}>Chụp phép tính để cùng kiểm tra cách làm.</Text>}</View>
      </Pressable>
    </View>
  </>;
  return <View onLayout={event => setAvailableWidth(event.nativeEvent.layout.width)}>
    <View style={[styles.header, wide && styles.headerWide]}>
      <Pressable accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" onPress={() => router.push('/(tabs)/profile')} style={({ pressed }) => [styles.avatar, pressed && styles.pressed]}>
        <Image source={ART.avatar} style={styles.avatarArt} resizeMode="contain" accessible={false} />
      </Pressable>
      <View style={styles.brandCopy}>
        <View style={styles.brandLine}>
          <Text style={styles.brandName}>MathVision<Text style={styles.brandAccent}>Kid</Text></Text>
          <View style={styles.brandSparkle} accessible={false}>
            <View style={[styles.sparkleStroke, styles.sparkleBlue]} />
            <View style={[styles.sparkleStroke, styles.sparklePurple]} />
            <View style={[styles.sparkleStroke, styles.sparkleYellow]} />
          </View>
        </View>
        <Text style={styles.tagline}>Toán học thật dễ, thật vui!</Text>
      </View>
      <Pressable accessibilityRole="button" accessibilityLabel="Mẹo chụp bài rõ nét" onPress={onTips} style={({ pressed }) => [styles.helpButton, pressed && styles.pressed]}>
        <Ionicons name="notifications-outline" size={25} color={COLORS.textPrimary} accessible={false} />
      </Pressable>
    </View>

    {desktop ? <>
      <View style={styles.overview}><View style={styles.heroColumn}>{hero}</View><View style={styles.activityColumn}>{learningActivity}</View></View>
      {utilities}{recommendations}{gradePicker}
    </> : wide ? <>
      {hero}{utilities}
      <View style={[styles.tabletBottom, availableWidth < 640 && styles.tabletBottomNarrow]}>
        <View style={[styles.activityColumn, availableWidth < 640 && styles.stackedColumn]}>{learningActivity}{gradePicker}</View>
        <View style={[styles.recommendationColumn, availableWidth < 640 && styles.stackedColumn]}>{recommendations}</View>
      </View>
    </> : <>{hero}{utilities}{learningActivity}{recommendations}</>}
    <Pressable onPress={onPrivacy} accessibilityRole="button" style={({ pressed }) => [styles.privacyLink, pressed && styles.pressed]}>
      <Ionicons name="shield-checkmark-outline" size={17} color={COLORS.primaryDark} accessible={false} />
      <Text style={styles.privacyText}>Bảo vệ thông tin riêng tư của em</Text>
      <Ionicons name="chevron-forward" size={15} color={COLORS.primaryDark} accessible={false} />
    </Pressable>
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
  </View>;
}

const styles = StyleSheet.create({
  overview: { flexDirection: 'row', gap: 20, alignItems: 'stretch', marginBottom: 18 },
  heroColumn: { flex: 1.85, minWidth: 0 }, activityColumn: { flex: 1, minWidth: 0 }, recommendationColumn: { flex: 1, minWidth: 0 },
  tabletBottom: { flexDirection: 'row', alignItems: 'flex-start', gap: 18, marginTop: 4 },
  tabletBottomNarrow: { flexDirection: 'column' }, stackedColumn: { flex: 0, width: '100%' },
  headerWide: { marginBottom: 20 },
  eyebrow: { fontFamily: FONTS.extraBold, color: '#66508A', fontSize: 10, letterSpacing: 1.2, marginBottom: 12, zIndex: 1 },
  heroWide: { minHeight: 248, padding: 24, marginBottom: 18, borderRadius: 28 },
  heroMascotWide: { height: 212, width: 226, right: -6, bottom: -4 },
  greetingWide: { fontSize: 34, lineHeight: 44 },
  heroDescriptionWide: { fontSize: 15, lineHeight: 23, width: '59%', maxWidth: 380, marginBottom: 18 },
  captureButtonWide: { width: 230, minHeight: 50, alignSelf: 'flex-start' }, captureLabelWide: { fontSize: 15 },
  quickGridWide: { gap: 12, marginBottom: 20 },
  quickCardTablet: { flex: 0, flexBasis: '48%', flexGrow: 1, flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 110, padding: 14, borderWidth: 1, borderColor: '#E8E3F1' },
  quickCardDesktop: { flexBasis: '23%', flexDirection: 'column', alignItems: 'stretch', gap: 4, minHeight: 184, padding: 16 },
  quickArtTablet: { width: 76, height: 76, marginBottom: 0 }, quickArtDesktop: { width: '100%', height: 96, marginBottom: 4 },
  quickCopyTablet: { flex: 1, minWidth: 0 },
  quickTitleWide: { fontSize: 16 }, quickDescriptionWide: { fontSize: 13, lineHeight: 20 },
  activityDesktop: { flex: 1, marginBottom: 18 }, activityWide: { borderWidth: 1, borderColor: '#E8E3F1', padding: 18 },
  lessonGridTablet: { flexDirection: 'column' }, lessonCardWide: { minHeight: 112, padding: 18 },
  lessonTitleWide: { fontSize: 16 }, lessonDescription: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: COLORS.textSecondary, marginTop: 7 },
  gradePicker: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12, marginTop: 2, marginBottom: 8 },
  gradePrompt: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.textSecondary },
  gradeChoices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, maxWidth: '100%' },
  gradeChoice: { minWidth: 48, minHeight: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E5DFF1', paddingHorizontal: 12 },
  gradeLabel: { fontFamily: FONTS.extraBold, fontSize: 13, color: COLORS.primaryDark },
  calculatorArt: { width: 64, height: 68 },
  calculatorCard: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16, minHeight: 88, borderRadius: 24, backgroundColor: COLORS.primaryLight, marginBottom: 20 },
  calculatorTitle: { fontFamily: FONTS.extraBold, fontSize: 18, color: COLORS.textPrimary, marginBottom: 4 },
  pressed: { opacity: 0.75 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 14 },
  avatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  avatarArt: { width: 54, height: 54 },
  brandCopy: { flex: 1 },
  brandLine: { flexDirection: 'row', alignItems: 'center' },
  brandName: { color: COLORS.textPrimary, fontSize: 22, fontFamily: FONTS.black, letterSpacing: -0.8 },
  brandAccent: { color: COLORS.primary },
  brandSparkle: { width: 10, height: 24, alignSelf: 'flex-start' },
  sparkleStroke: { position: 'absolute', width: 3, height: 9, borderRadius: 2 },
  sparkleBlue: { left: 1, top: 0, backgroundColor: '#55B7DB', transform: [{ rotate: '18deg' }] },
  sparklePurple: { left: -4, top: 4, backgroundColor: '#C1B9F0', transform: [{ rotate: '-35deg' }] },
  sparkleYellow: { left: 5, top: 10, backgroundColor: '#F7D06C', transform: [{ rotate: '65deg' }] },
  tagline: { color: COLORS.textSecondary, fontSize: 11.5, fontFamily: FONTS.regular, marginTop: 1 },
  helpButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.surface, alignItems: 'center', justifyContent: 'center', ...SHADOWS.small },
  hero: { backgroundColor: '#F0EDFE', borderRadius: 26, padding: 18, overflow: 'hidden', marginBottom: 12, minHeight: 198 },
  heroRoomy: { minHeight: 280 },
  heroBubble: { position: 'absolute', width: 240, height: 260, borderRadius: 120, backgroundColor: '#E4DEFB', right: -62, top: 14, transform: [{ rotate: '24deg' }] },
  heroMintBubble: { position: 'absolute', width: 90, height: 46, borderRadius: 46, backgroundColor: '#BEE5CF', left: '49%', bottom: -27, transform: [{ rotate: '-23deg' }] },
  mathPlus: { position: 'absolute', right: '42%', top: 42, color: '#F49DA8', fontFamily: FONTS.black, fontSize: 32 },
  mathDivision: { position: 'absolute', right: 18, top: 3, color: '#B29AEB', fontFamily: FONTS.black, fontSize: 29, transform: [{ rotate: '15deg' }] },
  heroMascot: { position: 'absolute', width: '55%', height: 195, right: -7, bottom: -6 },
  heroMascotRoomy: { opacity: 0.23, width: '70%', right: -25 },
  greetingRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 5, zIndex: 1 },
  greeting: { color: COLORS.textPrimary, fontSize: 32, lineHeight: 39, fontFamily: FONTS.black, letterSpacing: -0.8 },
  greetingSparkle: { width: 22, height: 24, marginLeft: 4 },
  greetingStrokeOne: { width: 4, height: 10, left: 4, top: 1, backgroundColor: '#F8D56E', transform: [{ rotate: '30deg' }] },
  greetingStrokeTwo: { width: 4, height: 8, left: 12, top: 11, backgroundColor: '#F8D56E', transform: [{ rotate: '74deg' }] },
  heroDescription: { width: '52%', color: COLORS.textSecondary, fontSize: 13, lineHeight: 19, fontFamily: FONTS.regular, marginBottom: 14, zIndex: 1 },
  heroDescriptionRoomy: { width: '100%', fontSize: 15, lineHeight: 23 },
  captureButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 48, width: '64%', backgroundColor: '#6B4CF5', borderRadius: 26, overflow: 'hidden', paddingVertical: 11, paddingHorizontal: 10, zIndex: 2, shadowColor: '#6645EB', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 9, elevation: 3 },
  captureButtonRoomy: { width: '100%' },
  captureLabel: { color: COLORS.surface, fontSize: 14.5, fontFamily: FONTS.extraBold, flexShrink: 1 },
  sectionHeading: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 4, marginBottom: 6 },
  sectionTitle: { color: COLORS.textPrimary, fontSize: 17, fontFamily: FONTS.extraBold, flexShrink: 1 },
  sectionLink: { flexDirection: 'row', alignItems: 'center', gap: 3, minHeight: 42, paddingHorizontal: 2 },
  sectionLinkText: { color: COLORS.primaryDark, fontSize: 11.5, fontFamily: FONTS.semiBold },
  quickGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 16 },
  quickCard: { flex: 1, minWidth: 90, borderRadius: 20, paddingHorizontal: 9, paddingTop: 7, paddingBottom: 13, minHeight: 156 },
  quickCardWide: { flexBasis: '46%' },
  quickArt: { width: '100%', height: 80, marginBottom: 5 },
  quickTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 2, marginBottom: 4 },
  quickTitle: { color: COLORS.textPrimary, fontSize: 14, fontFamily: FONTS.extraBold, flexShrink: 1, flex: 1 },
  cardArrow: { width: 17, height: 17, backgroundColor: COLORS.surface, borderRadius: 9, alignItems: 'center', justifyContent: 'center' },
  quickDescription: { color: COLORS.textSecondary, fontSize: 12, fontFamily: FONTS.regular, lineHeight: 18 },
  activityCard: { backgroundColor: COLORS.surface, borderRadius: 22, padding: 16, marginBottom: 14 },
  activityCopy: { paddingRight: 48 },
  activityTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginBottom: 4 },
  flame: { width: 21, height: 26 },
  streakTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  streakStar: { width: 17, height: 17 },
  streakTitle: { color: COLORS.primaryDark, fontSize: 21, fontFamily: FONTS.extraBold, flexShrink: 1 },
  crown: { position: 'absolute', width: 64, height: 66, right: 10, top: 10 },
  activityDescription: { color: COLORS.textSecondary, fontSize: 14, fontFamily: FONTS.regular, lineHeight: 22, marginTop: 8 },
  week: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 13, gap: 4 },
  weekConnector: { position: 'absolute', height: 2, left: 16, right: 16, top: 14, backgroundColor: '#EFEDF5' },
  weekDay: { flex: 1, alignItems: 'center', gap: 5 },
  dayCircle: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#F4F3F8', justifyContent: 'center', alignItems: 'center' },
  dayCircleDone: { backgroundColor: '#FFF3C7' },
  rewardStar: { width: 23, height: 23 },
  dayLabel: { color: COLORS.textSecondary, fontSize: 10.5, fontFamily: FONTS.regular },
  historyNote: { color: COLORS.textSecondary, fontSize: 12, lineHeight: 18, fontFamily: FONTS.regular, marginTop: 8 },
  lessonGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 12 },
  lessonCard: { flex: 1, minWidth: 140, backgroundColor: COLORS.primaryLight, padding: 12, borderRadius: 20, gap: 8, flexDirection: 'row', alignItems: 'center', minHeight: 84 },
  arithmeticCard: { backgroundColor: '#E8F6E9' },
  lessonSymbol: { width: 34, height: 34, borderRadius: 17, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  arithmeticSymbol: { backgroundColor: '#258548' },
  lessonCopy: { flex: 1 },
  lessonTitle: { color: COLORS.textPrimary, fontSize: 13, fontFamily: FONTS.extraBold },
  lessonDetail: { color: COLORS.textSecondary, fontSize: 10.5, fontFamily: FONTS.regular, lineHeight: 15, marginTop: 3 },
  privacyLink: { flexDirection: 'row', alignItems: 'center', gap: 7, minHeight: 48, paddingHorizontal: 4 },
  privacyText: { color: COLORS.primaryDark, fontSize: 11, fontFamily: FONTS.semiBold, flex: 1 },
});
