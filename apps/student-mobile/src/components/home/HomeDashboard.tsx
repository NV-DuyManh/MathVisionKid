import React, { useCallback, useContext, useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, Easing, Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { StyleProp, ViewStyle } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, IS_STUDENT_WEB } from '../../constants/theme';
import { AppIllustration as Image } from '../ui/AppIllustration';
import { buildCompletedLearningActivity } from '../../features/home/learningActivity';
import { PocketCalculator } from '../../features/calculator/PocketCalculator';
import { LearningJourney } from './LearningJourney';
import { ResumeLessonCard } from '../../features/tutoring/ResumeLessonCard';
import { AuthContext } from '../../context/AuthContext';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { RecoveryNotice } from '../ui/RecoveryNotice';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';
import { StudentAvatar } from '../../features/student-profile/ProfileCards';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { getLessonArtwork } from '../../features/lesson-artwork/lessonArtwork';

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
  const quickActions = [
    { title: 'Bài đã lưu', label: 'Bài đã lưu. Xem lại bài làm của em', image: ART.saved, color: '#FDE7F2', action: () => router.push('/(tabs)/profile') },
    { title: 'Luyện tập', label: 'Luyện tập. Làm bài theo chủ đề', image: ART.practice, color: '#E2F3FF', action: () => router.push('/(tabs)/lessons') },
    { title: 'Tiến bộ', label: 'Tiến bộ. Xem hành trình học tập', image: ART.progress, color: '#DEF6EE', action: () => router.push('/(tabs)/achievements') },
    { title: 'Máy tính', label: 'Mở máy tính bỏ túi', image: ART.calculator, color: '#EFE6FC', action: () => setCalculatorOpen(true) },
  ];
  return <View onLayout={event => setAvailableWidth(event.nativeEvent.layout.width)}>
    <Text style={styles.pageTitle} accessibilityRole="header">Trang chủ</Text>
    <View style={styles.header}>
      <Pressable accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" onPress={() => router.push('/account')} style={styles.avatar}>
        <StudentAvatar id={profile.value?.avatar ?? 'rocket'} photo={profile.value?.avatarPhoto} size={44} />
      </Pressable>
      <View style={styles.headerCopy}><Text style={styles.welcome}>Chào mừng trở lại,</Text><Text style={styles.name}>{`${displayName}!`}</Text></View>
      <Pressable accessibilityRole="button" accessibilityLabel="Thông báo học tập" onPress={() => setNotificationsOpen(true)} style={styles.iconButton}>
        <Ionicons name="notifications-outline" size={26} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    <LinearGradient colors={['#343DDC', '#5430CB', '#9848E6']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.hero, wide && styles.heroWide]} testID="home-hero">
      <View pointerEvents="none" style={styles.orbit} />
      <View style={[styles.heroCopy, fontScale > 1.3 && { width: '100%' }]}>
        <Text style={[styles.heroTitle, wide && styles.heroTitleWide]} accessibilityRole="header">Cùng <Text style={styles.yellow}>MathVisionKid</Text>{'\n'}khám phá Toán học nhé!</Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Chụp bài toán" accessibilityHint="Mở máy ảnh để chụp đề hoặc chọn ảnh bài toán" onPress={onAcquire}
          style={({ pressed }) => [styles.capture, pressed && styles.pressed]}><Text style={styles.captureText}>Chụp bài toán</Text></Pressable>
      </View>
      {fontScale <= 1.3 ? <HomeMascot visible={heroVisible} style={[styles.mascot, wide && styles.mascotWide]} /> : null}
    </LinearGradient>
    <View style={styles.headingRow}><Ionicons name="bulb-outline" size={24} color={COLORS.primaryDark} accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Tiện ích nhanh</Text></View>
    <View style={styles.quickGrid} testID="quick-actions-grid">
      {quickActions.map(item => <Pressable key={item.title} accessibilityRole="button" accessibilityLabel={item.label} onPress={item.action}
        style={({ pressed }) => [styles.quickCard, { backgroundColor: item.color }, wide && styles.quickCardWide, pressed && styles.pressed]}>
        <Image source={item.image} style={[styles.quickArt, wide && styles.quickArtWide]} accessible={false} />
        <Text style={[styles.quickTitle, wide && styles.quickTitleWide]}>{item.title}</Text>
      </Pressable>)}
    </View>
    <LearningJourney desktop={wide} onPractice={() => onPractice()} onAcquire={onAcquire} />
    <View style={styles.headingRow}><Ionicons name="star" size={22} color="#F0BB42" accessible={false} /><Text accessibilityRole="header" style={styles.heading}>Bài học gợi ý cho em</Text></View>
    {auth?.user && !hasRegisteredGrade ? <RecoveryNotice title="Chưa tải được lớp của em" message="Em tải lại hồ sơ để xem đúng bài học nhé."
      actions={[{ label: 'Tải lại hồ sơ', onPress: () => { profile.retry(); void auth.refreshUser?.(); } }]} /> : <View style={[styles.recommendations, wide && styles.recommendationsWide]}>
      {(hasRegisteredGrade ? gradeLessons.slice(0, 1).map(problem => ({ title: problem.title, artwork: getLessonArtwork(problem.id), description: `Lớp ${registeredGrade} · ${problem.topic}`,
        label: `Học bài ${problem.title}`, action: () => router.push({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } }) })) : [
        { title: 'Phép cộng đến 100', artwork: getLessonArtwork('grade1_prob1'), description: 'Lớp 1 · Đọc đề và thử giải', label: 'Luyện phép cộng và trừ trong phạm vi 100, lớp 1', action: () => onPractice(1) },
      ]).map(item => <Pressable key={item.title} accessibilityRole="button" accessibilityLabel={item.label} onPress={item.action} style={({ pressed }) => [styles.lesson, pressed && styles.pressed]}>
        <Image source={item.artwork.source} style={styles.lessonArt} accessible={false} /><View style={styles.headerCopy}><Text style={styles.lessonTitle}>{item.title}</Text><Text style={styles.lessonDescription}>{item.description}</Text></View>
        <Ionicons name="play-circle" size={28} color="#FFFFFF" accessible={false} />
      </Pressable>)}
    </View>}
    <ResumeLessonCard key={userKey} owner={userKey} />
    <View style={styles.streakCard} testID="learning-streak">
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
    <View style={styles.footer}><Pressable accessibilityRole="button" accessibilityLabel="Mẹo chụp bài rõ nét" onPress={onTips} style={styles.textButton}><Text style={styles.link}>Mẹo chụp bài</Text></Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel="Bảo vệ thông tin riêng tư của em" onPress={onPrivacy} style={styles.textButton}><Text style={styles.link}>Bảo vệ thông tin riêng tư của em</Text></Pressable></View>
    <PocketCalculator visible={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
    {notificationsOpen ? <LessonSheet title="Thông báo học tập" compact onClose={() => setNotificationsOpen(false)}>
      <Text style={styles.caption}>Chưa có thông báo mới. Em có thể mở lại bài đang học hoặc chọn một bài trong chương trình của mình.</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Mở lại giới thiệu MathVisionKid" onPress={() => { setNotificationsOpen(false); router.push('/onboarding'); }} style={styles.textButton}><Text style={styles.link}>Xem giới thiệu MathVisionKid</Text></Pressable>
    </LessonSheet> : null}
  </View>;
}
const styles = StyleSheet.create({
  pageTitle: { fontFamily: FONTS.extraBold, fontSize: 25, color: COLORS.textPrimary, marginBottom: 16 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 }, avatar: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FDE7F1', overflow: 'hidden' },
  headerCopy: { flex: 1, minWidth: 0 }, welcome: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary }, name: { fontFamily: FONTS.extraBold, fontSize: 17, lineHeight: 24, color: COLORS.textPrimary },
  iconButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  hero: { borderRadius: 24, padding: 17, minHeight: 184, justifyContent: 'center', overflow: 'hidden', marginBottom: 18 }, heroWide: { minHeight: 228, padding: 28 }, heroCopy: { width: '68%', zIndex: 1, alignItems: 'flex-start', gap: 13 },
  heroTitle: { fontFamily: FONTS.black, fontSize: 19, lineHeight: 25, color: '#FFFFFF', letterSpacing: -.35 }, heroTitleWide: { fontSize: 29, lineHeight: 38 }, yellow: { color: '#FFDE54' },
  capture: { minHeight: 44, backgroundColor: '#FFDC50', borderRadius: 26, paddingHorizontal: 16, paddingVertical: 11, justifyContent: 'center' }, captureText: { fontFamily: FONTS.extraBold, fontSize: 13, lineHeight: 19, color: '#20143F' },
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
