import React, { useCallback, useContext, useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, Easing, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { StyleProp, ViewStyle } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, IS_STUDENT_WEB } from '../../constants/theme';
import { AppIllustration as Image } from '../ui/AppIllustration';
import { buildCompletedLearningActivity, WEEKLY_ACTIVITY_GOAL } from '../../features/home/learningActivity';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';
import { LearningJourney } from './LearningJourney';
import { ResumeLessonCard } from '../../features/tutoring/ResumeLessonCard';
import { AuthContext } from '../../context/AuthContext';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { RecoveryNotice } from '../ui/RecoveryNotice';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';
import { StudentAvatar } from '../../features/student-profile/ProfileCards';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { QuizShortcut } from '../../features/quiz/QuizShortcut';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { getLessonArtwork } from '../../features/lesson-artwork/lessonArtwork';
import { profileApi } from '../../features/student-profile/profileApi';
import type { Leaderboard } from '../../features/student-profile/profileApi';

const ART = {
  mascot: IS_STUDENT_WEB ? require('../../../assets/illustrations/web/robot-mascot.webp') : require('../../../assets/illustrations/robot-mascot.png'),
  saved: require('../../../assets/illustrations/approved/saved.webp'), practice: require('../../../assets/illustrations/approved/practice.webp'),
  progress: require('../../../assets/illustrations/approved/progress.webp'), calculator: require('../../../assets/illustrations/approved/calculator.webp'),
  crown: require('../../../assets/illustrations/encouragement-crown.png'), flame: require('../../../assets/illustrations/streak-flame.png'),
  rewardStar: require('../../../assets/illustrations/reward-star.png'),
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
    const movement = Animated.sequence([
      Animated.timing(offset, { toValue: -5, duration: 1450, easing: Easing.inOut(Easing.sin), useNativeDriver: Platform.OS !== 'web' }),
      Animated.timing(offset, { toValue: 0, duration: 1450, easing: Easing.inOut(Easing.sin), useNativeDriver: Platform.OS !== 'web' }),
    ]);
    const animation = IS_STUDENT_WEB ? movement : Animated.loop(movement);
    animation.start();
    return () => animation.stop();
  }, [offset, visible, focused, active, reducedMotion]);
  return <Animated.View pointerEvents="none" style={[style, { transform: [{ translateY: offset }] }]}>
    <Image highResolution source={ART.mascot} style={{ width: '100%', height: '100%' }} accessible={false} />
  </Animated.View>;
}

export function HomeDashboard({ userName, userKey, heroVisible = true, onAcquire, onPractice, onTips, onPrivacy }: Props) {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const { width, fontScale } = useWindowDimensions();
  const [availableWidth, setAvailableWidth] = useState(width);
  const wide = availableWidth >= 680;
  const desktop = IS_STUDENT_WEB && availableWidth >= 930;
  const PrimaryColumn = desktop ? View : React.Fragment;
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const profile = useStudentProfile(userKey);
  const activity = buildCompletedLearningActivity(profile.value?.history ?? []);
  const streak = profile.value?.stats.streak ?? 0;
  const profileName = profile.value?.displayName || userName;
  const displayName = profileName.includes('@') ? 'Bạn nhỏ' : profileName;
  const registeredGrade = Number(profile.value?.gradeLevel ?? auth?.user?.gradeLevel ?? auth?.user?.grade);
  const hasRegisteredGrade = Number.isInteger(registeredGrade) && registeredGrade >= 1 && registeredGrade <= 5;
  const gradeLessons = hasRegisteredGrade ? getProblemsByGrade(registeredGrade as 1 | 2 | 3 | 4 | 5) : [];
  const [ranking, setRanking] = useState<{ owner: string; grade: number; data: Leaderboard }>();
  useFocusEffect(useCallback(() => {
    if (!IS_STUDENT_WEB || !desktop || !userKey || !hasRegisteredGrade) return;
    const request = new AbortController();
    void profileApi.leaderboard(undefined, request.signal).then(data => {
      if (!request.signal.aborted && (!data.gradeLevel || data.gradeLevel === registeredGrade)) setRanking({ owner: userKey, grade: registeredGrade, data });
    }).catch(() => {});
    return () => request.abort();
  }, [desktop, hasRegisteredGrade, registeredGrade, userKey]));
  const leaders = ranking?.owner === userKey && ranking?.grade === registeredGrade
    ? ranking.data.entries.filter(entry => !entry.self || profile.value?.leaderboardVisible === true).slice(0, 3) : undefined;
  const weeklyProgress = Math.min(profile.value?.stats.week ?? 0, WEEKLY_ACTIVITY_GOAL);
  const titles = IS_STUDENT_WEB ? profile.value?.titles?.filter(item => item.unlocked).slice(0, 3) ?? [] : [];
  const quickActions = [
    { title: 'Bài đã lưu', label: 'Bài đã lưu. Xem lại bài làm của em', image: ART.saved, color: '#FDE7F2', action: () => router.push(IS_STUDENT_WEB ? '/saved' as never : '/(tabs)/profile') },
    { title: 'Luyện tập', label: 'Luyện tập. Làm bài theo chủ đề', image: ART.practice, color: '#E2F3FF', action: () => router.push('/(tabs)/lessons') },
    ...(IS_STUDENT_WEB ? [{ title: 'Chụp bài', label: 'Hỏi AI từ ảnh bài toán', image: ART.mascot, color: '#EFE6FC', action: onAcquire }] : []),
    { title: 'Tiến bộ', label: 'Tiến bộ. Xem hành trình học tập', image: ART.progress, color: '#DEF6EE', action: () => router.push(IS_STUDENT_WEB ? '/progress' as never : '/(tabs)/achievements') },
    IS_STUDENT_WEB
      ? { title: 'Thành tích', label: 'Thành tích. Xem danh hiệu của em', image: ART.crown, color: '#FFF2CC', action: () => router.push('/(tabs)/achievements') }
      : { title: 'Máy tính', label: 'Mở máy tính bỏ túi', image: ART.calculator, color: '#EFE6FC', action: () => setCalculatorOpen(true) },
  ];
  const accountAction = () => router.push('/account');
  return <View onLayout={event => setAvailableWidth(event.nativeEvent.layout.width)}>
    {!IS_STUDENT_WEB && <Text style={styles.pageTitle} accessibilityRole="header">Trang chủ</Text>}
    {!desktop && <View style={styles.header}>
      <Pressable accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" onPress={accountAction} style={styles.avatar}>
        <StudentAvatar id={profile.value?.avatar ?? 'rocket'} photo={profile.value?.avatarPhoto} size={44} />
      </Pressable>
      <View style={styles.headerCopy}>
        {IS_STUDENT_WEB ? <Text style={styles.webPageTitle} accessibilityRole="header">Hôm nay em học gì?</Text> : null}
        <Text style={styles.welcome}>{IS_STUDENT_WEB ? `Chào mừng trở lại, ${displayName}!` : 'Chào mừng trở lại,'}</Text>
        {!IS_STUDENT_WEB && <Text style={styles.name}>{`${displayName}!`}</Text>}
      </View>
      <Pressable accessibilityRole="button" accessibilityLabel="Thông báo học tập" onPress={() => setNotificationsOpen(true)} style={styles.iconButton}>
        <Ionicons name="notifications-outline" size={26} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>}
    <PrimaryColumn {...(desktop ? { style: styles.desktopGrid } : {})}>
    <PrimaryColumn {...(desktop ? { style: styles.desktopPrimary } : {})}>
    <LinearGradient colors={IS_STUDENT_WEB ? [STUDENT_WEB.indigo, '#6543DB', STUDENT_WEB.heroEnd] : ['#343DDC', '#5430CB', '#9848E6']}
      start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.hero, wide && styles.heroWide, desktop && styles.desktopHero]} testID="home-hero">
      <View pointerEvents="none" style={styles.orbit} />
      {IS_STUDENT_WEB && <View pointerEvents="none" style={styles.heroClouds}>
        <View style={styles.cloud} /><View style={[styles.cloud, styles.cloudLower]} /><View style={styles.cloud} />
      </View>}
      <View style={[styles.heroCopy, fontScale > 1.3 && { width: '100%' }]}>
        {desktop && <View style={styles.heroGreeting}>
          <Pressable accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" onPress={accountAction} style={styles.greetingPill}>
            <Text style={styles.greetingLabel} numberOfLines={1}>{`Chào mừng trở lại, ${displayName}!`}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Thông báo học tập" onPress={() => setNotificationsOpen(true)} style={styles.greetingBell}>
            <Ionicons name="notifications-outline" size={17} color="#FFF" accessible={false} />
          </Pressable>
        </View>}
        <Text style={[styles.heroTitle, wide && styles.heroTitleWide]} accessibilityRole="header">Cùng <Text style={styles.yellow}>MathVisionKid</Text>{'\n'}khám phá Toán học nhé!</Text>
        {IS_STUDENT_WEB && wide && <Text style={styles.heroSubtitle}>Hiểu đề, tự tìm cách giải và luyện tập theo lớp của em.</Text>}
        <View style={IS_STUDENT_WEB ? styles.heroActions : undefined}>
          {IS_STUDENT_WEB ? <Pressable accessibilityRole="button" onPress={() => onPractice()}
            style={({ pressed }) => [styles.capture, styles.heroButtonIcon, pressed && styles.pressed]}><Ionicons name="play" size={16} color="#20143F" accessible={false} /><Text style={styles.captureText}>Học ngay</Text></Pressable> : null}
          <Pressable accessibilityRole="button" accessibilityLabel="Chụp bài toán" accessibilityHint="Mở máy ảnh để chụp đề hoặc chọn ảnh bài toán" onPress={onAcquire}
            style={({ pressed }) => [styles.capture, IS_STUDENT_WEB && styles.webCapture, pressed && styles.pressed]}>{IS_STUDENT_WEB && <Ionicons name="camera-outline" size={19} color="#20143F" accessible={false} />}<Text style={styles.captureText}>{IS_STUDENT_WEB ? 'Chụp bài, hỏi AI' : 'Chụp bài toán'}</Text></Pressable>
        </View>
      </View>
      {desktop && fontScale <= 1.3 && <View pointerEvents="none" accessible={false} aria-hidden style={styles.mathCard}>
        <Text style={styles.mathLabel}>8 + 5 = 13</Text><Ionicons name="shapes-outline" size={34} color="#DBF5FF" />
      </View>}
      {fontScale <= 1.3 ? <HomeMascot visible={heroVisible} style={[styles.mascot, wide && styles.mascotWide]} /> : null}
    </LinearGradient>
    <View style={styles.headingRow}><Ionicons name="bulb-outline" size={24} color={COLORS.primaryDark} accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Tiện ích nhanh</Text>
      {IS_STUDENT_WEB && <Pressable accessibilityRole="button" accessibilityLabel="Mở máy tính bỏ túi" onPress={() => setCalculatorOpen(true)} style={styles.utility}>
        <Ionicons name="calculator-outline" size={19} color={COLORS.primaryDark} accessible={false} /><Text style={styles.link}>Máy tính</Text>
      </Pressable>}
    </View>
    <View style={[styles.quickGrid, desktop && styles.desktopQuickGrid]} testID="quick-actions-grid">
      {quickActions.map(item => <Pressable key={item.title} accessibilityRole="button" accessibilityLabel={item.label} onPress={item.action}
        style={({ pressed }) => [styles.quickCard, { backgroundColor: item.color }, wide && styles.quickCardWide, desktop && styles.desktopQuickCard, pressed && styles.pressed]}>
        <Image source={item.image} style={[styles.quickArt, wide && styles.quickArtWide, desktop && styles.desktopQuickArt]} accessible={false} />
        <Text style={[styles.quickTitle, wide && styles.quickTitleWide, desktop && styles.desktopQuickTitle]}>{item.title}</Text>
      </Pressable>)}
    </View>
    <LearningJourney desktop={wide} onPractice={() => onPractice()} onAcquire={onAcquire} onCheck={IS_STUDENT_WEB ? () => router.push('/quiz') : undefined} />
    <View style={styles.headingRow}><Ionicons name="star" size={22} color={IS_STUDENT_WEB ? '#A2650D' : '#F0BB42'} accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Bài học gợi ý cho em</Text>
      {IS_STUDENT_WEB && <Pressable accessibilityRole="button" accessibilityLabel="Xem tất cả bài học" onPress={() => onPractice()} style={styles.utility}><Text style={styles.link}>Xem tất cả</Text></Pressable>}
    </View>
    {auth?.user && !hasRegisteredGrade ? <RecoveryNotice title="Chưa tải được lớp của em" message="Em tải lại hồ sơ để xem đúng bài học nhé."
      actions={[{ label: 'Tải lại hồ sơ', onPress: () => { profile.retry(); void auth.refreshUser?.(); } }]} /> : <View style={[styles.recommendations, wide && styles.recommendationsWide]}>
      {(hasRegisteredGrade ? gradeLessons.slice(0, IS_STUDENT_WEB ? 3 : 1).map(problem => ({ title: problem.title, artwork: getLessonArtwork(problem.id), description: `Lớp ${registeredGrade} · ${problem.topic}`,
        label: `Học bài ${problem.title}`, action: () => router.push({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } }) })) : [
        { title: 'Phép cộng đến 100', artwork: getLessonArtwork('grade1_prob1'), description: 'Lớp 1 · Đọc đề và thử giải', label: 'Luyện phép cộng và trừ trong phạm vi 100, lớp 1', action: () => onPractice(1) },
      ]).map((item, index) => <Pressable key={item.title} accessibilityRole="button" accessibilityLabel={item.label} onPress={item.action} style={({ pressed }) => [styles.lesson, IS_STUDENT_WEB && { backgroundColor: ['#FCE9F3', '#E5F2FF', '#E3F6EE'][index] }, pressed && styles.pressed]}>
        <Image source={item.artwork.source} style={styles.lessonArt} accessible={false} /><View style={styles.headerCopy}><Text style={styles.lessonTitle}>{item.title}</Text><Text style={styles.lessonDescription}>{item.description}</Text></View>
        <Ionicons name="play-circle" size={28} color={IS_STUDENT_WEB ? COLORS.primaryDark : '#FFFFFF'} accessible={false} />
      </Pressable>)}
    </View>}
    </PrimaryColumn>
    <PrimaryColumn {...(desktop ? { style: styles.desktopAside } : {})}>
    {!IS_STUDENT_WEB && <ResumeLessonCard key={userKey} owner={userKey} />}
    <View style={[styles.streakCard, desktop && styles.desktopStreak]} testID="learning-streak">
      <Image source={ART.crown} style={styles.crown} accessible={false} />
      <View style={styles.headingRow}><Image source={ART.flame} style={styles.flame} accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Chuỗi học tập</Text></View>
      <Text style={styles.streak}>{!profile.value ? profile.failed ? 'Chưa tải được chuỗi học tập' : 'Đang tải chuỗi học tập…' : streak ? `Em đã học liên tiếp ${streak} ngày!` : 'Bắt đầu hôm nay!'}</Text>
      <Text style={styles.caption}>{profile.failed ? 'Em thử tải lại để xem hoạt động đã hoàn thành.' : profile.value?.stats.today ? 'Giỏi lắm! Hôm nay em đã hoàn thành hoạt động học.' : streak ? 'Hãy tiếp tục học hôm nay để duy trì chuỗi nhé!' : 'Hoàn thành một bài học để bắt đầu chuỗi học tập của em.'}</Text>
      <View style={styles.week}>{activity.days.map(day => <View key={day.label} style={styles.day} accessible accessibilityLabel={`${day.label}: ${day.completed ? 'đã học' : 'chưa có hoạt động hoàn thành'}${day.today ? ', hôm nay' : ''}`}>
        <View style={[styles.dayCircle, day.completed && styles.dayCompleted]}>
          {day.completed ? <>
            <Image source={ART.rewardStar} style={styles.dayRewardStar} accessible={false} />
            <Ionicons name="sparkles" size={13} color="#E6A418" style={styles.daySparkles} accessible={false} testID="completed-day-sparkles" />
          </> : <Ionicons name="star" size={18} color="#C9C1D7" accessible={false} />}
        </View>
        <Text style={[styles.dayLabel, day.today && styles.todayLabel]}>{day.label}</Text>
      </View>)}</View>
      <Text style={styles.historyNote}>Theo hoạt động đã hoàn thành · Giờ Việt Nam.</Text>
      {profile.failed ? <Pressable accessibilityRole="button" accessibilityLabel="Tải lại chuỗi học tập" onPress={profile.retry} style={styles.textButton}><Text style={styles.link}>Tải lại</Text></Pressable> : null}
    </View>
    {IS_STUDENT_WEB && profile.value ? <View style={styles.desktopProgress}>
      <View style={styles.panelTitleRow}><Ionicons name="locate" size={21} color={COLORS.primaryDark} accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Mục tiêu tuần</Text></View>
      <View style={styles.weeklySummary}>
        <Text style={styles.progressLabel}>Hoạt động trong 7 ngày qua</Text>
        <Text style={styles.link}>{weeklyProgress}/{WEEKLY_ACTIVITY_GOAL}</Text>
      </View>
      <View accessibilityRole="progressbar" accessibilityLabel="Mục tiêu hoạt động trong tuần"
        accessibilityValue={{ min: 0, now: weeklyProgress, max: WEEKLY_ACTIVITY_GOAL }} style={styles.weeklyTrack}>
        <View style={[styles.weeklyBar, { width: `${weeklyProgress * 100 / WEEKLY_ACTIVITY_GOAL}%` }]} />
      </View>
      <Pressable accessibilityRole="button" onPress={() => router.push('/progress' as never)} style={styles.textButton}>
        <Text style={styles.link}>Xem tiến bộ</Text>
      </Pressable>
    </View> : null}
    {IS_STUDENT_WEB && profile.value ? <View style={styles.desktopProgress}>
      <View style={styles.panelTitleRow}><Ionicons name="star" size={20} color="#A76405" accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Danh hiệu của em</Text></View>
      {titles.length ? <View style={styles.progressMetrics}>{titles.map(item => <View key={item.id} style={styles.titleTile}>
        <Ionicons name="ribbon" size={24} color={COLORS.primaryDark} accessible={false} /><Text style={styles.progressLabel}>{item.name}</Text>
      </View>)}</View> : <Text style={styles.caption}>Chưa có danh hiệu.</Text>}
      <Pressable accessibilityRole="button" onPress={() => router.push('/(tabs)/achievements')} style={styles.textButton}><Text style={styles.link}>Xem danh hiệu</Text></Pressable>
    </View> : null}
    {IS_STUDENT_WEB && hasRegisteredGrade ? <View style={[styles.desktopProgress, styles.leaderPanel]}>
      <LinearGradient colors={['#643BD3', '#814CEB']} start={{ x: 0, y: 0 }} end={{ x: 1, y: .5 }} style={styles.leaderHeading}>
        <Ionicons name="trophy-outline" size={21} color="#FFE888" accessible={false} />
        <Text accessibilityRole="header" style={styles.leaderTitle}>Bảng xếp hạng</Text><Text style={styles.leaderGrade}>Khối {registeredGrade}</Text>
      </LinearGradient>
      {leaders?.map((entry, index) => <View key={entry.position} style={[styles.leader, index === 0 && styles.leaderTop]}>
        <Text style={styles.link}>#{entry.position}</Text>
        <StudentAvatar id={entry.avatar} size={25} />
        <Text style={styles.leaderName}>{entry.self && profile.value?.leaderboardNameHidden ? profile.value.publicAlias : entry.alias}</Text>
        <Text style={styles.progressLabel}>{entry.stars} sao</Text>
      </View>)}
      <Pressable accessibilityRole="button" onPress={() => router.push('/(tabs)/achievements')} style={styles.textButton}><Text style={styles.link}>Xem bảng xếp hạng</Text></Pressable>
    </View> : null}
    {IS_STUDENT_WEB && <ResumeLessonCard key={userKey} owner={userKey} />}
    {IS_STUDENT_WEB ? <View style={styles.quizShortcut}><QuizShortcut /></View> : null}
    </PrimaryColumn>
    </PrimaryColumn>
    <View style={styles.footer}><Pressable accessibilityRole="button" accessibilityLabel="Mẹo chụp bài rõ nét" onPress={onTips} style={styles.textButton}><Text style={styles.link}>Mẹo chụp bài</Text></Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel="Bảo vệ thông tin riêng tư của em" onPress={onPrivacy} style={styles.textButton}><Text style={styles.link}>Bảo vệ thông tin riêng tư của em</Text></Pressable></View>
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
    {notificationsOpen ? <LessonSheet title="Thông báo học tập" compact onClose={() => setNotificationsOpen(false)}>
      <Text style={styles.caption}>Chưa có thông báo mới. Em có thể mở lại bài đang học hoặc chọn một bài trong chương trình của mình.</Text>
      {!IS_STUDENT_WEB && <Pressable accessibilityRole="button" accessibilityLabel="Mở lại giới thiệu MathVisionKid" onPress={() => { setNotificationsOpen(false); router.push('/onboarding'); }} style={styles.textButton}><Text style={styles.link}>Xem giới thiệu MathVisionKid</Text></Pressable>}
    </LessonSheet> : null}
  </View>;
}
const styles = StyleSheet.create({
  desktopGrid: { flexDirection: 'row', alignItems: 'flex-start', gap: 22 },
  desktopPrimary: { flex: 1, minWidth: 0 },
  desktopAside: { width: 340, flexShrink: 0 },
  desktopHero: { minHeight: 248, padding: 20, borderRadius: STUDENT_WEB.radius, marginBottom: 8 },
  desktopStreak: { marginTop: 0, borderColor: STUDENT_WEB.border, backgroundColor: STUDENT_WEB.surface },
  desktopQuickGrid: { marginBottom: 15, gap: 8 },
  desktopQuickCard: { minHeight: 59, flexDirection: 'row', gap: 6, paddingHorizontal: 6, borderRadius: 14 },
  desktopQuickArt: { width: 34, height: 34, marginBottom: 0 },
  desktopQuickTitle: { fontSize: 13, lineHeight: 17, flexShrink: 1 },
  desktopProgress: { marginTop: 14, paddingHorizontal: 18, paddingTop: 14, borderRadius: STUDENT_WEB.radius,
    borderWidth: 1, borderColor: STUDENT_WEB.border, backgroundColor: STUDENT_WEB.surface },
  progressMetrics: { flexDirection: 'row', gap: 8, marginTop: 12 },
  panelTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  weeklySummary: { paddingTop: 11, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 6 },
  weeklyTrack: { height: 8, marginTop: 8, borderRadius: 4, backgroundColor: STUDENT_WEB.soft, overflow: 'hidden' },
  weeklyBar: { height: '100%', borderRadius: 4, backgroundColor: STUDENT_WEB.brand },
  progressLabel: { color: STUDENT_WEB.muted, fontFamily: FONTS.semiBold, fontSize: 12 },
  titleTile: { flex: 1, alignItems: 'center', padding: 8, gap: 5, borderRadius: 12, backgroundColor: STUDENT_WEB.soft },
  leaderPanel: { paddingHorizontal: 0, paddingTop: 0, overflow: 'hidden' },
  leaderHeading: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12 },
  leaderTitle: { flex: 1, fontFamily: FONTS.extraBold, fontSize: 16, color: '#FFF' },
  leaderGrade: { color: '#FFF', backgroundColor: '#FFFFFF26', fontFamily: FONTS.bold, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, fontSize: 12 },
  leader: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 40, paddingHorizontal: 12, borderBottomWidth: 1, borderColor: STUDENT_WEB.border },
  leaderTop: { backgroundColor: '#FFF4D9' },
  leaderName: { flex: 1, color: STUDENT_WEB.ink, fontFamily: FONTS.bold, fontSize: 13 },
  quizShortcut: { marginTop: 16 },
  pageTitle: { fontFamily: FONTS.extraBold, fontSize: 25, color: COLORS.textPrimary, marginBottom: 16 },
  webPageTitle: { fontFamily: FONTS.black, fontSize: 28, lineHeight: 36, color: COLORS.textPrimary },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 }, avatar: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FDE7F1', overflow: 'hidden' },
  headerCopy: { flex: 1, minWidth: 0 }, welcome: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary }, name: { fontFamily: FONTS.extraBold, fontSize: 17, lineHeight: 24, color: COLORS.textPrimary },
  iconButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  hero: { borderRadius: 24, padding: 17, minHeight: 184, justifyContent: 'center', overflow: 'hidden', marginBottom: 18 }, heroWide: { minHeight: 228, padding: 28 }, heroCopy: { width: '68%', zIndex: 1, alignItems: 'flex-start', gap: 13 },
  heroTitle: { fontFamily: FONTS.black, fontSize: 19, lineHeight: 25, color: '#FFFFFF', letterSpacing: -.35 }, heroTitleWide: { fontSize: 29, lineHeight: 38 }, yellow: { color: '#FFDE54' },
  heroSubtitle: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: '#F7EEFF' },
  heroGreeting: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  greetingPill: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 13, borderRadius: 24, backgroundColor: '#FFFFFF22', flexShrink: 1 },
  greetingLabel: { color: '#FEF2FF', fontFamily: FONTS.bold, fontSize: 13 },
  greetingBell: { width: 44, minHeight: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  mathCard: { position: 'absolute', right: '28%', top: 60, width: 102, alignItems: 'center', gap: 5, padding: 7, borderWidth: 1, borderColor: '#8EE5FF99', borderRadius: 16, backgroundColor: '#3D65CD', transform: [{ rotate: '-9deg' }] },
  mathLabel: { color: '#EAFAFF', fontFamily: FONTS.extraBold, fontSize: 13 },
  heroClouds: { position: 'absolute', flexDirection: 'row', right: '-5%', bottom: -62, width: '38%', minWidth: 230, justifyContent: 'flex-end' },
  cloud: { width: 110, height: 110, borderRadius: 55, backgroundColor: '#C9ACFFF2', marginLeft: -25 },
  cloudLower: { marginTop: 24, backgroundColor: '#D4BEFFF2' },
  capture: { minHeight: 44, backgroundColor: '#FFDC50', borderRadius: 26, paddingHorizontal: 16, paddingVertical: 11, justifyContent: 'center' }, captureText: { fontFamily: FONTS.extraBold, fontSize: 13, lineHeight: 19, color: '#20143F' },
  heroButtonIcon: { flexDirection: 'row', gap: 7, alignItems: 'center' },
  webCapture: { backgroundColor: '#F5F2FF', flexDirection: 'row', gap: 8, alignItems: 'center' },
  heroActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  utility: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, paddingHorizontal: 10, minHeight: 44, borderRadius: 12, backgroundColor: STUDENT_WEB.soft },
  mascot: { position: 'absolute', right: 0, bottom: 9, width: '36%', height: 155 }, mascotWide: { right: 20, bottom: 4, height: 218, width: '34%' }, orbit: { position: 'absolute', width: '90%', height: 90, borderWidth: 2, borderColor: '#AD78EA', bottom: -60, right: -30, borderRadius: 80, transform: [{ rotate: '-15deg' }] },
  headingRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 13 }, heading: { flex: 1, fontFamily: FONTS.extraBold, fontSize: 20, lineHeight: 27, color: COLORS.textPrimary },
  quickGrid: { flexDirection: 'row', gap: 7, marginBottom: 24 }, quickCard: { flex: 1, minWidth: 0, borderRadius: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 3, paddingVertical: 12, minHeight: 90 }, quickCardWide: { minHeight: 138 },
  quickArt: { width: '90%', height: 40, marginBottom: 8 }, quickArtWide: { height: 70 }, quickTitle: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 15, textAlign: 'center', color: COLORS.textPrimary }, quickTitleWide: { fontSize: 15, lineHeight: 22 },
  recommendations: { gap: 10, marginBottom: 2 }, recommendationsWide: { flexDirection: 'row' }, lesson: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', padding: 14, gap: 10, backgroundColor: '#EFE5FC', borderRadius: 22, minHeight: 84 }, lessonArt: { width: 44, height: 50 }, lessonTitle: { fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 20, color: COLORS.textPrimary }, lessonDescription: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: COLORS.textSecondary, marginTop: 3 },
  streakCard: { marginTop: 24, borderRadius: 24, padding: 18, borderWidth: 1, borderColor: '#E8E0F8', backgroundColor: '#FFFFFF' }, crown: { position: 'absolute', right: 12, top: 10, width: 48, height: 44 }, flame: { width: 20, height: 24 }, streak: { fontFamily: FONTS.extraBold, fontSize: 20, lineHeight: 28, color: COLORS.primaryDark, paddingRight: 15 }, caption: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: COLORS.textSecondary, marginTop: 7 },
  week: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 14 }, day: { alignItems: 'center', gap: 6 }, dayCircle: { width: 30, height: 30, borderRadius: 16, backgroundColor: '#F1EDF7', alignItems: 'center', justifyContent: 'center' }, dayCompleted: { backgroundColor: '#FFF0BA' }, dayLabel: { fontFamily: FONTS.semiBold, fontSize: 11, color: COLORS.textSecondary }, todayLabel: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold }, historyNote: { fontFamily: FONTS.regular, fontSize: 10, lineHeight: 16, color: COLORS.textSecondary, marginTop: 10 },
  dayRewardStar: { width: 40, height: 40 },
  daySparkles: { position: 'absolute', right: -5, top: -5 },
  footer: { marginTop: 16, flexDirection: 'row', justifyContent: 'center', flexWrap: 'wrap', gap: 12 }, textButton: { minHeight: 44, justifyContent: 'center', alignItems: 'center' }, link: { fontFamily: FONTS.bold, fontSize: 12, color: COLORS.primaryDark }, pressed: { opacity: .75 },
});
