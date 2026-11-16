import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, Easing, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { ScrollViewInstance, StyleProp, ViewStyle } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, IS_STUDENT_WEB, WEB_DESIGN } from '../../constants/theme';
import { AppButton } from '../ui/AppButton';
import { AppIllustration as Image } from '../ui/AppIllustration';
import { StudentPageHeader } from '../ui/StudentPageHeader';
import { recognitionAnalyticsStore } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildLearningActivity } from '../../features/home/learningActivity';
import { loadLessons } from '../../features/tutoring/learningHistory';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';
import { LearningJourney } from './LearningJourney';
import { ResumeLessonCard } from '../../features/tutoring/ResumeLessonCard';
import { AuthContext } from '../../context/AuthContext';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { RecoveryNotice } from '../ui/RecoveryNotice';

const ART = {
  mascot: IS_STUDENT_WEB ? require('../../../assets/illustrations/web/robot-mascot.webp') : require('../../../assets/illustrations/robot-mascot.png'), saved: require('../../../assets/illustrations/approved/saved.webp'),
  practice: require('../../../assets/illustrations/approved/practice.webp'), progress: require('../../../assets/illustrations/approved/progress.webp'),
  bars: IS_STUDENT_WEB ? require('../../../assets/illustrations/web/progress-bars.webp') : require('../../../assets/illustrations/progress-bars.png'), calculator: require('../../../assets/illustrations/approved/calculator.webp'),
  crown: IS_STUDENT_WEB ? require('../../../assets/illustrations/web/encouragement-crown.webp') : require('../../../assets/illustrations/encouragement-crown.png'), flame: IS_STUDENT_WEB ? require('../../../assets/illustrations/web/streak-flame.webp') : require('../../../assets/illustrations/streak-flame.png'), star: require('../../../assets/illustrations/reward-star.png'),
};
type Props = { userName: string; userKey?: string; heroVisible?: boolean; onAcquire: () => void; onArithmetic: () => void; onPractice: (grade?: 1 | 2 | 3 | 4 | 5) => void; onTips: () => void; onPrivacy: () => void };

function HomeMascot({ style, visible }: { style: StyleProp<ViewStyle>; visible: boolean }) {
  const [offset] = useState(() => new Animated.Value(0));
  const [reducedMotion, setReducedMotion] = useState(true);
  const [focused, setFocused] = useState(false);
  const [active, setActive] = useState(AppState.currentState !== 'background');
  useFocusEffect(useCallback(() => { setFocused(true); return () => setFocused(false); }, []));
  useEffect(() => {
    let mounted = true;
    void AccessibilityInfo.isReduceMotionEnabled().then(value => { if (mounted) setReducedMotion(value); });
    const preference = AccessibilityInfo.addEventListener('reduceMotionChanged', setReducedMotion);
    const app = AppState.addEventListener('change', value => setActive(value === 'active'));
    return () => { mounted = false; preference.remove(); app.remove(); };
  }, []);
  useEffect(() => {
    if (!visible || !focused || !active || reducedMotion) { offset.setValue(0); return; }
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(offset, { toValue: -5, duration: 1450, easing: Easing.inOut(Easing.sin), useNativeDriver: Platform.OS !== 'web' }),
      Animated.timing(offset, { toValue: 0, duration: 1450, easing: Easing.inOut(Easing.sin), useNativeDriver: Platform.OS !== 'web' }),
    ]));
    animation.start();
    return () => animation.stop();
  }, [offset, visible, focused, active, reducedMotion]);
  return <Animated.View pointerEvents="none" style={[style, { transform: [{ translateY: offset }] }]}>
    <Image highResolution source={ART.mascot} style={{ width: '100%', height: '100%' }} accessible={false} />
  </Animated.View>;
}

export function HomeDashboard({ userName, userKey, heroVisible = true, onAcquire, onArithmetic, onPractice, onTips, onPrivacy }: Props) {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const { width, height, fontScale } = useWindowDimensions();
  const [availableWidth, setAvailableWidth] = useState(width);
  const desktop = availableWidth >= 900 && fontScale <= 1.3;
  const wide = availableWidth >= 580 && fontScale <= 1.3;
  const roomy = availableWidth < 350 || fontScale > 1.3;
  const largeText = fontScale > 1.3;
  const [activity, setActivity] = useState<ReturnType<typeof buildLearningActivity> | null>(null);
  const [historyUnavailable, setHistoryUnavailable] = useState(false);
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const quickActionsScroll = useRef<ScrollViewInstance>(null);
  const [quickPage, setQuickPage] = useState(0);
  const quickCardWidth = Math.max(228, Math.min(272, availableWidth * .78));
  const quickCardStride = quickCardWidth + 12;
  const registeredGrade = Number(auth?.user?.gradeLevel ?? auth?.user?.grade);
  const hasRegisteredGrade = Number.isInteger(registeredGrade) && registeredGrade >= 1 && registeredGrade <= 5;
  const suggestedLessons = hasRegisteredGrade ? getProblemsByGrade(registeredGrade as 1 | 2 | 3 | 4 | 5).slice(0, 2) : [];
  useFocusEffect(useCallback(() => {
    let active = true;
    setActivity(null); setHistoryUnavailable(false);
    Promise.all([recognitionAnalyticsStore.init(), loadLessons(userKey)]).then(([, lessons]) => {
      if (active) setActivity(buildLearningActivity([...recognitionAnalyticsStore.getSessions(), ...lessons.map(item => ({ sessionId: item.id, timestamp: item.timestamp }))]));
    }).catch(() => { if (active) setHistoryUnavailable(true); });
    return () => { active = false; };
  }, [userKey]));
  const quickActions = [
    { title: 'Bài đã lưu', description: 'Xem lại bài làm của em', short:'Xem bài cũ',image: ART.saved, background: '#FFF0F1', onPress: () => router.push('/(tabs)/profile') },
    { title: 'Luyện tập', description: 'Làm bài theo chủ đề',short:'Theo chủ đề', image: ART.practice, background: '#EAF6FF', onPress: () => router.push('/(tabs)/lessons') },
    { title: 'Tiến bộ', description: 'Xem hành trình học tập',short:'Hành trình học', image: wide ? ART.bars : ART.progress, background: '#ECF8EE', onPress: () => router.push('/(tabs)/achievements') },
    { title: 'Máy tính', description: 'Số thường, phân số, chia có dư',short:'Cùng tính nhé', image: ART.calculator, background: '#F0EBFD', onPress: () => setCalculatorOpen(true) },
  ];
  const streak = <View style={[styles.activity, desktop && styles.activityDesktop, IS_STUDENT_WEB && styles.paperPanel]}>
    <Image source={ART.crown} style={styles.crown} accessible={false} />
    <View style={styles.row}><Image source={ART.flame} style={styles.flame} accessible={false} /><Text style={styles.activityHeading}>Chuỗi học tập</Text></View>
    <View style={styles.streakRow}><Ionicons name="star" size={16} color="#F2BE46" accessible={false} /><Text style={[styles.streak, IS_STUDENT_WEB && styles.webStreak]}>{activity?.streak ? `${activity.streak} ngày liên tiếp!` : 'Bắt đầu hôm nay!'}</Text></View>
    <Text style={styles.activityCaption}>{historyUnavailable ? 'Chưa tải được lịch sử. Em vẫn có thể bắt đầu bài mới.' : activity?.completedToday ? 'Giỏi lắm! Mỗi ngày mình cùng học một chút nhé.' : 'Lưu một bài hôm nay để bắt đầu chuỗi học tập nhé.'}</Text>
    <View style={styles.week}>{(activity?.days || ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'].map(label => ({ label, completed: false, date: '' }))).map(day =>
      <View key={day.label} style={styles.day} accessible accessibilityLabel={`${day.label}: ${day.completed ? 'đã lưu bài' : 'chưa lưu bài'}`}>
        <View style={[styles.dayCircle, day.completed && styles.dayDone]}><Ionicons name="star" size={18} color={day.completed ? '#EDB044' : '#C7C1D7'} accessible={false} /></View>
        <Text style={styles.dayLabel}>{day.label}</Text>
      </View>)}</View>
    <Text style={styles.historyNote}>Theo bài đã lưu trên thiết bị này.</Text>
  </View>;
  return <View onLayout={event => setAvailableWidth(event.nativeEvent.layout.width)} style={{ minHeight: Math.max(0, height - (wide ? 48 : 110)) }}>
    <StudentPageHeader title={IS_STUDENT_WEB ? 'Trang học của em' : undefined} subtitle={IS_STUDENT_WEB ? undefined : 'Toán học thật dễ, thật vui!'} onHelp={onTips} onAvatar={() => router.push('/account')} />
    <View style={[styles.overview, desktop && styles.overviewDesktop]}>
      {IS_STUDENT_WEB ? <View style={[styles.webHero, desktop && styles.heroDesktop, wide && styles.webHeroWide]} {...{ dataSet: { studentPaper: 'true' } }}>
        <View style={[styles.webHeroCopy, wide && styles.webHeroCopyWide]}>
          <Text style={[styles.webGreeting, wide && styles.webGreetingWide]} accessibilityRole="header">Cùng học toán nhé!</Text>
          <Text style={styles.webDescription}>Chụp một bài toán để xem lại bài làm hoặc cùng tìm cách giải.</Text>
          <View style={styles.webHeroActions}>
            <AppButton title="Chụp bài toán" onPress={onAcquire} icon={<Ionicons name="camera-outline" size={22} color="#FFF" accessible={false} />} />
            <AppButton title="Mở câu đố" variant="secondary" onPress={() => router.push('/quiz')}
              icon={<Ionicons name="extension-puzzle-outline" size={20} color={COLORS.primary} accessible={false} />} />
          </View>
        </View>
        {!largeText ? <HomeMascot visible={heroVisible} style={[styles.webMascot, wide && styles.webMascotWide, roomy && styles.webMascotRoomy]} /> : null}
      </View> : <LinearGradient colors={['#F7F2FF', '#ECE5FD']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.hero, wide && styles.heroWide, desktop && styles.heroDesktop, roomy && styles.heroRoomy]}>
        <View style={styles.orbit} accessible={false} /><View style={styles.mint} accessible={false} />{wide ? <View style={styles.peach} accessible={false} /> : null}
        <Text style={styles.plus} accessible={false}>+</Text><Text style={styles.division} accessible={false}>÷</Text>
        {!largeText ? <HomeMascot visible={heroVisible} style={[styles.mascot, wide && styles.mascotWide, desktop && styles.mascotDesktop, roomy && styles.mascotRoomy]} /> : null}
        <View style={styles.heroCopy}>
          <Text style={[styles.greeting, wide && styles.greetingWide]} accessibilityRole="header" accessibilityLabel={`Chào ${userName}!`}>Chào em!<Text style={styles.spark}> ✦</Text></Text>
          <Text style={[styles.description, wide && styles.descriptionWide, largeText && { width: '100%', maxWidth: '100%' }]}>Cùng MathVisionKid khám phá Toán học nhé!</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Chụp bài toán" accessibilityHint="Mở máy ảnh để chụp đề hoặc bài em đã làm" onPress={onAcquire}
            style={({ pressed }) => [styles.capture, wide && styles.captureWide, pressed && styles.pressed]}>
            <LinearGradient colors={['#8C5BFF', '#6534F4']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={StyleSheet.absoluteFill} pointerEvents="none" />
            <Ionicons name="camera" size={22} color="#FFF" accessible={false} /><Text style={[styles.captureLabel, wide && { fontSize: 18 }]}>Chụp bài toán</Text><Ionicons name="chevron-forward" size={18} color="#FFF" accessible={false} />
          </Pressable>
        </View>
      </LinearGradient>}
      {desktop ? streak : null}
    </View>
    <ResumeLessonCard key={userKey} owner={userKey}/>
    {desktop ? <LearningJourney desktop onPractice={() => onPractice()} onAcquire={onAcquire} /> : null}
    <View style={styles.sectionHeading}><Text style={styles.sectionTitle} accessibilityRole="header">Tiện ích nhanh</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Xem tất cả bài luyện tập lớp 1 đến lớp 5" onPress={() => router.push('/(tabs)/lessons')} style={styles.sectionLink}><Text style={styles.link}>Xem tất cả</Text><Ionicons name="chevron-forward" size={14} color={COLORS.primaryDark} /></Pressable>
    </View>
    {wide || IS_STUDENT_WEB ? <View style={[styles.quickGrid, wide && styles.quickGridWide, IS_STUDENT_WEB && styles.webQuickGrid]}>
      {quickActions.map(action => <Pressable key={action.title} onPress={action.onPress} accessibilityRole="button"
        accessibilityLabel={action.title === 'Máy tính' ? 'Mở máy tính bỏ túi' : `${action.title}. ${action.description}`}
        style={state => [styles.quickCard, { backgroundColor: action.background }, wide && styles.quickCardWide,
          IS_STUDENT_WEB && styles.webQuickCard, IS_STUDENT_WEB && wide && styles.webQuickCardWide, IS_STUDENT_WEB && 'hovered' in state && state.hovered === true && styles.webQuickHovered, state.pressed && styles.pressed]}>
        <Image source={action.image} style={[styles.quickArt, wide && styles.quickArtWide, IS_STUDENT_WEB && styles.webQuickArt]} accessible={false} />
        <View style={(largeText || IS_STUDENT_WEB) && styles.flex}><View style={styles.quickHeading}><Text style={[styles.quickTitle, wide && styles.quickTitleWide, IS_STUDENT_WEB && styles.webQuickTitle]}>{action.title}</Text>{!roomy ? <View style={styles.quickArrow}><Ionicons name="chevron-forward" size={13} color={COLORS.primaryDark} accessible={false} /></View> : null}</View><Text style={[styles.quickDescription, wide && styles.quickDescriptionWide, IS_STUDENT_WEB && styles.webQuickDescription]}>{action.description}</Text></View>
      </Pressable>)}
    </View> : <View style={styles.quickCarousel}>
      <ScrollView
        ref={quickActionsScroll}
        horizontal
        showsHorizontalScrollIndicator={false}
        snapToInterval={quickCardStride}
        decelerationRate="fast"
        contentContainerStyle={[styles.quickCarouselContent, { paddingRight: Math.max(0, availableWidth - quickCardWidth) }]}
        onMomentumScrollEnd={event => {
          setQuickPage(Math.round(event.nativeEvent.contentOffset.x / quickCardStride));
        }}
        accessibilityLabel={`Tiện ích nhanh, trang ${quickPage + 1} trên ${quickActions.length}`}>
        {quickActions.map(action => <Pressable key={action.title} onPress={action.onPress} accessibilityRole="button"
          accessibilityLabel={action.title === 'Máy tính' ? 'Mở máy tính bỏ túi' : `${action.title}. ${action.description}`}
          style={({ pressed }) => [styles.quickCard, styles.quickCarouselCard, { backgroundColor: action.background, width: quickCardWidth }, pressed && styles.pressed]}>
          <Image source={action.image} style={styles.quickCarouselArt} accessible={false} />
          <View style={styles.flex}><View style={styles.quickHeading}><Text style={styles.quickTitle}>{action.title}</Text><View style={styles.quickArrow}><Ionicons name="chevron-forward" size={13} color={COLORS.primaryDark} accessible={false} /></View></View><Text style={styles.quickDescription}>{action.short}</Text></View>
        </Pressable>)}
      </ScrollView>
      <View style={styles.quickCarouselControls}>
        <Pressable accessibilityRole="button" accessibilityLabel="Tiện ích trước" disabled={quickPage === 0} onPress={() => {
          const nextPage = Math.max(0, quickPage - 1); setQuickPage(nextPage);
          quickActionsScroll.current?.scrollTo({ x: nextPage * quickCardStride, animated: true });
        }} style={({ pressed }) => [styles.carouselButton, quickPage === 0 && styles.carouselButtonDisabled, pressed && styles.pressed]}>
          <Ionicons name="chevron-back" size={18} color={quickPage === 0 ? '#B7ADCE' : COLORS.primaryDark} accessible={false} />
        </Pressable>
        <Text accessibilityLiveRegion="polite" style={styles.carouselPage}>{quickPage + 1} / {quickActions.length}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Tiện ích tiếp theo" disabled={quickPage === quickActions.length - 1} onPress={() => {
          const nextPage = Math.min(quickActions.length - 1, quickPage + 1); setQuickPage(nextPage);
          quickActionsScroll.current?.scrollTo({ x: nextPage * quickCardStride, animated: true });
        }} style={({ pressed }) => [styles.carouselButton, quickPage === quickActions.length - 1 && styles.carouselButtonDisabled, pressed && styles.pressed]}>
          <Ionicons name="chevron-forward" size={18} color={quickPage === quickActions.length - 1 ? '#B7ADCE' : COLORS.primaryDark} accessible={false} />
        </Pressable>
      </View>
    </View>}
    {!desktop ? <View style={styles.streakBelow}>{streak}</View> : null}
    {!desktop ? <LearningJourney desktop={false} onPractice={() => onPractice()} onAcquire={onAcquire} /> : null}
    <View style={[styles.lower, desktop && styles.lowerDesktop]}>
      <View style={styles.flex}>
        <View style={styles.sectionHeading}><Text style={styles.sectionTitle} accessibilityRole="header">Bài học gợi ý cho em</Text><Pressable accessibilityRole="button" accessibilityLabel="Xem thêm bài học gợi ý" onPress={() => onPractice()} style={styles.sectionLink}><Text style={styles.link}>Xem thêm</Text><Ionicons name="chevron-forward" size={14} color={COLORS.primaryDark} /></Pressable></View>
        {auth?.user && !hasRegisteredGrade ? <RecoveryNotice title="Chưa tải được lớp của em" message="Em tải lại hồ sơ để xem đúng bài học nhé."
          actions={[{ label: 'Tải lại hồ sơ', onPress: () => { void auth.refreshUser?.(); } }]} /> : <View style={[styles.recommendations, !roomy && styles.recommendationsDesktop]}>
          {(hasRegisteredGrade ? suggestedLessons.map(problem => ({
            title: problem.title, description: problem.topic, icon: 'book-outline' as const,
            label: `Học bài ${problem.title}`, onPress: () => router.push({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } }),
          })) : [
            { title: 'Phép cộng đến 100', description: 'Lớp 1 · Đọc đề và thử giải', icon: 'star-outline' as const, label: 'Luyện phép cộng và trừ trong phạm vi 100, lớp 1', onPress: () => onPractice(1) },
            { title: 'Đọc phép tính', description: 'Cộng, trừ đặt dọc', icon: 'calculator-outline' as const, label: 'Đọc phép tính. Kiểm tra phép cộng và trừ đặt dọc', onPress: onArithmetic },
          ]).map((item, index) => <Pressable key={item.title} onPress={item.onPress} accessibilityRole="button" accessibilityLabel={item.label}
            style={({ pressed }) => [styles.lesson, index === 1 && { backgroundColor: '#EDF7EE' }, !roomy && styles.lessonDesktop, pressed && styles.pressed]}>
            <View style={styles.lessonHeading}><Text style={styles.lessonTitle}>{item.title}</Text>
              <View style={[styles.lessonIcon, index === 1 && { backgroundColor: '#6B9FE2' }]}><Ionicons name={item.icon} size={15} color="#FFF" accessible={false} /></View></View>
            <Text style={styles.lessonDetail}>{item.description}</Text>
          </Pressable>)}
        </View>}
      </View>
      {wide && !hasRegisteredGrade && !auth?.user ? <View style={[styles.gradePicker, desktop && styles.gradeDesktop]}><Text style={styles.gradeTitle}>Luyện tập theo lớp</Text><View style={styles.gradeChoices}>
        {([1, 2, 3, 4, 5] as const).map(grade => <Pressable key={grade} accessibilityRole="button" accessibilityLabel={`Luyện tập lớp ${grade}`} onPress={() => onPractice(grade)} style={({ pressed }) => [styles.gradeChoice, pressed && styles.pressed]}><Text style={styles.gradeLabel}>Lớp {grade}</Text></Pressable>)}
      </View></View> : null}
    </View>
    <Pressable onPress={onPrivacy} accessibilityRole="button" accessibilityLabel="Bảo vệ thông tin riêng tư của em" style={styles.privacy}><Ionicons name="shield-checkmark-outline" size={17} color={COLORS.primaryDark} accessible={false} /><Text style={styles.privacyText}>Bảo vệ thông tin riêng tư của em</Text><Ionicons name="chevron-forward" size={15} color={COLORS.primaryDark} accessible={false} /></Pressable>
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
  </View>;
}
const styles = StyleSheet.create({
  webHero: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', minWidth: 0, gap: 8, padding: 20,
    borderWidth: 1, borderColor: WEB_DESIGN.components.notebook.borderColor, borderRadius: WEB_DESIGN.components.notebook.radius,
    backgroundColor: '#FFF3CB' },
  webHeroWide: { gap: 16, padding: 28, minHeight: 248 },
  webHeroCopy: { flex: 1, minWidth: 176, gap: 12, zIndex: 1 },
  webHeroCopyWide: { gap: 14 },
  webGreeting: { fontFamily: FONTS.black, fontSize: 28, lineHeight: 34, letterSpacing: -.5, color: WEB_DESIGN.colors.ink },
  webGreetingWide: { fontSize: WEB_DESIGN.typography.sizes.display, lineHeight: 46 },
  webDescription: { maxWidth: 340, fontFamily: FONTS.regular, fontSize: WEB_DESIGN.typography.sizes.body, lineHeight: 24, color: WEB_DESIGN.colors.ink },
  webHeroActions: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10 },
  webMascot: { width: 100, height: 108, alignSelf: 'flex-end', marginLeft: 'auto' },
  webMascotWide: { width: '32%', maxWidth: 220, height: 200, alignSelf: 'center' },
  webMascotRoomy: { width: 56, height: 66 },
  paperPanel: { borderColor: WEB_DESIGN.colors.paperLine, borderRadius: WEB_DESIGN.components.notebook.radius, shadowOpacity: 0, elevation: 0 },
  webStreak: { color: WEB_DESIGN.colors.blue },
  webQuickGrid: { flexWrap: 'wrap', marginBottom: 24, gap: 10 },
  webQuickCard: { flex: 1, flexBasis: '100%', flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 74,
    paddingHorizontal: 12, paddingVertical: 10, borderWidth: 1, borderColor: 'transparent', borderRadius: WEB_DESIGN.components.action.radius },
  webQuickCardWide: { flexBasis: '47%' },
  webQuickHovered: { borderColor: WEB_DESIGN.focus.color },
  webQuickArt: { width: 52, height: 52, marginBottom: 0 },
  webQuickTitle: { fontSize: WEB_DESIGN.typography.sizes.body, lineHeight: 22 },
  webQuickDescription: { fontSize: WEB_DESIGN.typography.sizes.caption, lineHeight: 20, color: WEB_DESIGN.colors.mutedInk },
  flex: { flex: 1, minWidth: 0 }, row: { flexDirection: 'row', alignItems: 'center', gap: 6 }, overview: { marginBottom: 17, gap: 18 }, overviewDesktop: { flexDirection: 'row', alignItems: 'stretch' },
  hero: { minHeight: 196, padding: 18, borderRadius: 25, position: 'relative', overflow: 'hidden' }, heroWide: { minHeight: 232, padding: 25 }, heroDesktop: { flex: 1.85, minHeight: 256 }, heroRoomy: { minHeight: 210, paddingHorizontal: 16 },
  heroCopy: { zIndex: 2, alignItems: 'flex-start' }, greeting: { fontFamily: FONTS.black, fontSize: 31, lineHeight: 39, color: '#171345', letterSpacing: -.9, marginBottom: 6 }, greetingWide: { fontSize: 38, lineHeight: 48 },
  spark: { color: '#F1B744', fontSize: 21 }, description: { fontFamily: FONTS.regular, color: '#63577E', fontSize: 13, lineHeight: 19, width: '54%', maxWidth: 225, marginBottom: 13 }, descriptionWide: { fontSize: 16, lineHeight: 24, maxWidth: 320, width: '63%', marginBottom: 19 },
  orbit: { position: 'absolute', right: -90, top: 16, width: 270, height: 230, borderRadius: 160, backgroundColor: '#DACCF85C' }, mint: { position: 'absolute', right: 100, bottom: -32, width: 130, height: 70, borderRadius: 70, backgroundColor: '#B7DBC7AA', transform: [{ rotate: '-15deg' }] }, peach: { position: 'absolute', right: -25, bottom: -20, width: 100, height: 70, borderRadius: 60, backgroundColor: '#F9D6A3AA' },
  plus: { position: 'absolute', right: 117, top: 55, color: '#EAA0B8', fontSize: 25 }, division: { position: 'absolute', right: 24, top: 12, color: '#B9A1EF', fontSize: 19 },
  mascot: { position: 'absolute', width: '47%' as const, height: 178, right: 9, bottom: 8 }, mascotWide: { width: '43%' as const, height: 234, right: 12, bottom: 0 }, mascotDesktop: { width: '44%' as const, height: 248 }, mascotRoomy: { width: '43%' as const, height: 164 },
  quickCarousel: { marginBottom: 16 }, quickCarouselContent: { gap: 12, paddingBottom: 4 }, quickCarouselCard: { flex: 0, flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 108, padding: 14 }, quickCarouselArt: { width: 68, height: 72 },
  quickCarouselControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, paddingTop: 4 }, carouselButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#EEE7FF', alignItems: 'center', justifyContent: 'center' }, carouselButtonDisabled: { backgroundColor: '#F2EEF8' }, carouselPage: { fontFamily: FONTS.bold, fontSize: 12, color: '#75698A', minWidth: 36, textAlign: 'center' },
  capture: { borderRadius: 28, overflow: 'hidden', flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 48, paddingVertical: 10, paddingHorizontal: 16, borderWidth: 1, borderColor: '#AE8FFF', shadowColor: '#7F53E4', shadowOpacity: .15, shadowRadius: 7, shadowOffset: { width: 0, height: 3 }, elevation: 3 }, captureWide: { minHeight: 52, paddingHorizontal: 22 }, captureLabel: { fontFamily: FONTS.extraBold, color: '#FFF', fontSize: 15 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 10 }, sectionTitle: { flex: 1, fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 19, lineHeight: 26, letterSpacing: -.3 }, sectionLink: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 4 }, link: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 12 },
  quickGrid: { flexDirection: 'row', gap: 8, marginBottom: 16 }, quickGridWide: { gap: 12, marginBottom: 22 }, quickCard: { flex: 1, minWidth: 0, minHeight: 148, borderRadius: 20, paddingHorizontal: 10, paddingTop: 12, paddingBottom: 12 }, quickCardWide: { minHeight: 178, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 16, borderRadius: 22 }, quickCardRoomy: { paddingHorizontal: 8 },
  quickArt: { width: '100%', height: 60, marginBottom: 8 }, quickArtWide: { height: 80, marginBottom: 10 }, quickHeading: { flexDirection: 'row', alignItems: 'center', gap: 3, marginBottom: 5 }, quickArrow: { width: 17, height: 17, borderRadius: 9, backgroundColor: '#FFFFFFD9', alignItems: 'center', justifyContent: 'center' }, quickTitle: { flex: 1, fontFamily: FONTS.extraBold, fontSize: 13, lineHeight: 18, color: COLORS.textPrimary }, quickTitleWide: { fontSize: 16, lineHeight: 22 }, quickDescription: { fontFamily: FONTS.regular, color: '#6F6588', fontSize: 11, lineHeight: 16 }, quickDescriptionWide: { fontSize: 12, lineHeight: 18 },
  activity: { position: 'relative', borderRadius: 24, padding: 18, borderWidth: 1, borderColor: '#E8E0F8', backgroundColor: '#FFF', minWidth: 0, shadowColor: '#49386E', shadowOffset: { width: 0, height: 3 }, shadowOpacity: .07, shadowRadius: 9, elevation: 2 }, activityDesktop: { flex: 1 }, activityHeading: { fontFamily: FONTS.extraBold, fontSize: 17, lineHeight: 23, color: COLORS.textPrimary }, flame: { width: 20, height: 22 }, crown: { position: 'absolute', right: 10, top: 12, width: 57, height: 55 }, streakRow: { flexDirection: 'row', alignItems: 'center', gap: 7, marginTop: 5, paddingRight: 22 }, streak: { flex: 1, fontFamily: FONTS.extraBold, color: '#6C3FE4', fontSize: 20, lineHeight: 27 }, week: { flexDirection: 'row', gap: 3, justifyContent: 'space-between', marginTop: 12 }, day: { alignItems: 'center', gap: 5, flex: 1 }, dayCircle: { width: 29, height: 29, borderRadius: 15, backgroundColor: '#F1EDF7', alignItems: 'center', justifyContent: 'center' }, dayDone: { backgroundColor: '#FFF0BA' }, dayLabel: { fontFamily: FONTS.semiBold, fontSize: 11, lineHeight: 15, color: '#78678C' }, activityCaption: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: '#746A8B', marginTop: 7 }, historyNote: { fontFamily: FONTS.regular, fontSize: 10, lineHeight: 15, color: '#7B6E8A', marginTop: 8 }, streakBelow: { marginBottom: 20 },
  lower: { gap: 18 }, lowerDesktop: { flexDirection: 'row', alignItems: 'stretch', gap: 20 }, recommendations: { gap: 10 }, recommendationsDesktop: { flexDirection: 'row' },
  lesson: { justifyContent: 'center', gap: 5, padding: 10, borderRadius: 15, backgroundColor: '#EEE7FF', minHeight: 76 }, lessonDesktop: { flex: 1, minWidth: 0 },
  lessonHeading: { flexDirection: 'row', alignItems: 'center', gap: 6 }, lessonIcon: { width: 22, height: 22, borderRadius: 8, backgroundColor: '#9B72ED', alignItems: 'center', justifyContent: 'center' },
  lessonTitle: { flex: 1, minWidth: 0, fontFamily: FONTS.extraBold, fontSize: 13, lineHeight: 18, color: COLORS.textPrimary },
  lessonDetail: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 11, lineHeight: 16 },
  gradePicker: { padding: 20, borderRadius: 23, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#ECE5F8', gap: 15 }, gradeDesktop: { width: 260 }, gradeTitle: { fontFamily: FONTS.extraBold, fontSize: 17, color: COLORS.textPrimary }, gradeChoices: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, gradeChoice: { minHeight: 44, minWidth: 54, paddingHorizontal: 10, justifyContent: 'center', alignItems: 'center', borderRadius: 12, backgroundColor: '#F3EEFF' }, gradeLabel: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark },
  privacy: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, marginTop: 22 }, privacyText: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#74658F' }, pressed: { opacity: .73 },
});
