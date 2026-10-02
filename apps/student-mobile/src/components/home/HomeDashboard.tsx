import React, { useCallback, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SHADOWS } from '../../constants/theme';
import { recognitionAnalyticsStore } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildLearningActivity } from '../../features/home/learningActivity';

const ART = {
  mascot: require('../../../assets/illustrations/mathvision-star.png'),
  saved: require('../../../assets/illustrations/saved-folder.png'),
  practice: require('../../../assets/illustrations/practice-notebook.png'),
  progress: require('../../../assets/illustrations/progress-bars.png'),
  crown: require('../../../assets/illustrations/encouragement-crown.png'),
  flame: require('../../../assets/illustrations/streak-flame.png'),
  star: require('../../../assets/illustrations/reward-star.png'),
};

type Props = {
  userName: string;
  userKey?: string;
  onCamera: () => void;
  onArithmetic: () => void;
  onGallery: () => Promise<void>;
  onPractice: (grade?: 1 | 2 | 3 | 4 | 5) => void;
  onTips: () => void;
  onPrivacy: () => void;
};

export function HomeDashboard({ userName, userKey, onCamera, onArithmetic, onGallery, onPractice, onTips, onPrivacy }: Props) {
  const router = useRouter();
  const { width, fontScale } = useWindowDimensions();
  const roomyText = width < 350 || fontScale > 1.3;
  const [activity, setActivity] = useState<ReturnType<typeof buildLearningActivity> | null>(null);
  const [historyUnavailable, setHistoryUnavailable] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true;
    setActivity(null);
    setHistoryUnavailable(false);
    recognitionAnalyticsStore.init().then(() => {
      if (active) {
        setActivity(buildLearningActivity(recognitionAnalyticsStore.getSessions()));
        setHistoryUnavailable(false);
      }
    }).catch(() => { if (active) setHistoryUnavailable(true); });
    return () => { active = false; };
  }, [userKey]));
  const quickActions = [
    { title: 'Bài đã lưu', description: 'Xem lại bài làm của em', image: ART.saved, background: '#FFF0EE', onPress: () => router.push('/recognition/analytics') },
    { title: 'Luyện tập', description: 'Làm bài theo chủ đề', image: ART.practice, background: '#EAF6FD', onPress: () => onPractice() },
    { title: 'Tiến bộ', description: 'Xem kết quả đã lưu', image: ART.progress, background: '#ECF8EC', onPress: () => router.push('/recognition/analytics') },
  ];

  return <View>
    <View style={styles.header}>
      <Pressable accessibilityRole="button" accessibilityLabel="Trang cá nhân của em" onPress={() => router.push('/(tabs)/profile')} style={({ pressed }) => [styles.avatar, pressed && styles.pressed]}>
        <Image source={ART.mascot} style={styles.avatarArt} resizeMode="contain" accessible={false} />
      </Pressable>
      <View style={styles.brandCopy}>
        <Text style={styles.brandName}>MathVision<Text style={styles.brandAccent}>Kid</Text></Text>
        <Text style={styles.tagline}>Toán học thật dễ, thật vui!</Text>
      </View>
      <Pressable accessibilityRole="button" accessibilityLabel="Mẹo chụp bài rõ nét" onPress={onTips} style={({ pressed }) => [styles.helpButton, pressed && styles.pressed]}>
        <Ionicons name="help-circle-outline" size={26} color={COLORS.textPrimary} accessible={false} />
      </Pressable>
    </View>

    <View style={[styles.hero, roomyText && styles.heroStack]}>
      <View style={styles.heroCopy}>
        <Text style={styles.greeting} accessibilityRole="header">Chào {userName === 'em' ? 'em' : userName}!</Text>
        <Text style={styles.heroDescription}>Cùng MathVisionKid khám phá Toán học theo cách thật thú vị nhé!</Text>
        <Pressable onPress={onCamera} accessibilityRole="button" accessibilityLabel="Chụp bài toán hoặc bài viết tay" style={({ pressed }) => [styles.captureButton, SHADOWS.small, pressed && styles.pressed]}>
          <Ionicons name="camera" size={22} color={COLORS.surface} accessible={false} />
          <Text style={styles.captureLabel}>Chụp bài toán</Text>
          <Ionicons name="chevron-forward" size={18} color={COLORS.surface} accessible={false} />
        </Pressable>
      </View>
      <Image source={ART.mascot} style={[styles.heroMascot, width < 400 && styles.heroMascotCompact, roomyText && styles.heroMascotStack]} resizeMode="contain" accessible={false} />
    </View>

    <View style={styles.captureOptions}>
      <Pressable onPress={onCamera} accessibilityRole="button" style={({ pressed }) => [styles.optionButton, pressed && styles.pressed]}>
        <Ionicons name="create-outline" size={18} color={COLORS.primaryDark} accessible={false} />
        <Text style={styles.optionLabel}>Đọc chữ viết tay</Text>
      </Pressable>
      <Pressable onPress={onGallery} accessibilityRole="button" accessibilityLabel="Chọn ảnh bài làm từ thư viện" style={({ pressed }) => [styles.optionButton, pressed && styles.pressed]}>
        <Ionicons name="images-outline" size={18} color={COLORS.primaryDark} accessible={false} />
        <Text style={styles.optionLabel}>Chọn ảnh có sẵn</Text>
      </Pressable>
    </View>

    <View style={styles.sectionHeading}>
      <Text style={styles.sectionTitle} accessibilityRole="header">Tiện ích nhanh</Text>
      <Pressable onPress={() => onPractice()} accessibilityRole="button" accessibilityLabel="Xem kho bài luyện tập lớp 1 đến lớp 5" style={({ pressed }) => [styles.sectionLink, pressed && styles.pressed]}>
        <Text style={styles.sectionLinkText}>Kho bài tập</Text>
        <Ionicons name="chevron-forward" size={16} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    <View style={styles.quickGrid}>
      {quickActions.map(action => <Pressable key={action.title} onPress={action.onPress} accessibilityRole="button" accessibilityLabel={`${action.title}. ${action.description}`} style={({ pressed }) => [styles.quickCard, { backgroundColor: action.background }, roomyText && styles.quickCardWide, pressed && styles.pressed]}>
        <Image source={action.image} style={styles.quickArt} resizeMode="contain" accessible={false} />
        <Text style={styles.quickTitle}>{action.title}</Text>
        <Text style={styles.quickDescription}>{action.description}</Text>
        <View style={styles.cardArrow}><Ionicons name="chevron-forward" size={14} color={COLORS.primaryDark} accessible={false} /></View>
      </Pressable>)}
    </View>

    <View style={[styles.activityCard, SHADOWS.small]}>
      <View style={styles.activityHeader}>
        <View style={styles.activityCopy}>
          <View style={styles.activityTitleRow}>
            <Image source={ART.flame} style={styles.flame} resizeMode="contain" accessible={false} />
            <Text style={styles.sectionTitle} accessibilityRole="header">Chuỗi học tập</Text>
          </View>
          <Text style={styles.streakTitle}>
            {activity && activity.streak > 0 ? `${activity.streak} ngày liên tiếp!` : 'Mỗi ngày một chút!' }
          </Text>
        </View>
        <Image source={ART.crown} style={styles.crown} resizeMode="contain" accessible={false} />
      </View>
      <Text style={styles.activityDescription}>
        {historyUnavailable ? 'Chưa tải được lịch sử học tập. Em vẫn có thể bắt đầu bài mới.'
          : activity?.completedToday ? 'Hôm nay em đã lưu bài rồi. Tiếp tục giữ thói quen này nhé!'
          : activity?.streak ? 'Hãy lưu thêm bài hôm nay để nối tiếp chuỗi của em nhé!'
          : 'Chụp bài làm, kiểm tra và lưu kết quả để bắt đầu hành trình nhé!'}
      </Text>
      {activity && <View style={styles.week}>
        {activity.days.map(day => <View key={day.label} style={styles.weekDay} accessibilityLabel={`${day.label}, ${day.date}: ${day.completed ? 'đã lưu bài' : 'chưa lưu bài'}`} accessible>
          <View style={[styles.dayCircle, day.completed && styles.dayCircleDone]}>
            {day.completed ? <Image source={ART.star} style={styles.rewardStar} resizeMode="contain" accessible={false} /> : <Ionicons name="star-outline" size={21} color="#727087" accessible={false} />}
          </View>
          <Text style={styles.dayLabel}>{day.label}</Text>
        </View>)}
      </View>}
      <Text style={styles.historyNote}>Theo các bài em đã xác nhận và lưu trên thiết bị này.</Text>
    </View>

    <View style={styles.sectionHeading}>
      <Text style={styles.sectionTitle} accessibilityRole="header">Bài học gợi ý cho em</Text>
      <Pressable onPress={() => onPractice()} accessibilityRole="button" style={({ pressed }) => [styles.sectionLink, pressed && styles.pressed]}>
        <Text style={styles.sectionLinkText}>Xem thêm</Text>
        <Ionicons name="chevron-forward" size={16} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    <View style={styles.lessonGrid}>
      <Pressable onPress={() => onPractice(1)} accessibilityRole="button" accessibilityLabel="Luyện phép cộng và trừ trong phạm vi 100, lớp 1" style={({ pressed }) => [styles.lessonCard, pressed && styles.pressed]}>
        <View style={styles.lessonSymbol}><Ionicons name="add" size={25} color={COLORS.surface} accessible={false} /></View>
        <Text style={styles.lessonTitle}>Cộng, trừ{ '\n' }đến 100</Text>
        <Text style={styles.lessonDetail}>Lớp 1 · Bài toán có lời văn</Text>
      </Pressable>
      <Pressable onPress={onArithmetic} accessibilityRole="button" accessibilityLabel="Đọc phép tính. Cộng, trừ, nhân, chia đặt tính rồi tính" style={({ pressed }) => [styles.lessonCard, styles.arithmeticCard, pressed && styles.pressed]}>
        <View style={[styles.lessonSymbol, styles.arithmeticSymbol]}><Ionicons name="calculator-outline" size={25} color={COLORS.surface} accessible={false} /></View>
        <Text style={styles.lessonTitle}>Đọc phép tính</Text>
        <Text style={styles.lessonDetail}>Cộng, trừ, nhân, chia đặt tính rồi tính</Text>
      </Pressable>
    </View>
    <Pressable onPress={onPrivacy} accessibilityRole="button" style={({ pressed }) => [styles.privacyLink, pressed && styles.pressed]}>
      <Ionicons name="shield-checkmark-outline" size={18} color={COLORS.primaryDark} accessible={false} />
      <Text style={styles.privacyText}>Bảo vệ thông tin riêng tư của em</Text>
      <Ionicons name="chevron-forward" size={16} color={COLORS.primaryDark} accessible={false} />
    </Pressable>
  </View>;
}

const styles = StyleSheet.create({
  pressed: { opacity: 0.72 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 22 },
  avatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center' },
  avatarArt: { width: 44, height: 44 },
  brandCopy: { flex: 1 },
  brandName: { color: COLORS.textPrimary, fontSize: 23, fontWeight: '900', letterSpacing: -0.7 },
  brandAccent: { color: COLORS.primary },
  tagline: { color: COLORS.textSecondary, fontSize: 12, marginTop: 3 },
  helpButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: COLORS.surface, alignItems: 'center', justifyContent: 'center', ...SHADOWS.small },
  hero: { backgroundColor: COLORS.primaryLight, borderRadius: 28, padding: 20, flexDirection: 'row', alignItems: 'center', overflow: 'hidden', minHeight: 232 },
  heroStack: { flexDirection: 'column-reverse', alignItems: 'stretch' },
  heroCopy: { flex: 1.15, zIndex: 1 },
  greeting: { color: COLORS.textPrimary, fontSize: 32, fontWeight: '900', letterSpacing: -0.8, marginBottom: 10 },
  heroDescription: { color: COLORS.textSecondary, fontSize: 14, lineHeight: 21, marginBottom: 18 },
  heroMascot: { width: '46%', height: 200, marginRight: -14, marginLeft: -4 },
  heroMascotCompact: { width: '40%' },
  heroMascotStack: { width: '100%', height: 146, marginRight: 0, marginLeft: 0, marginBottom: 12 },
  captureButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 52, backgroundColor: COLORS.primary, borderRadius: 28, paddingVertical: 12, paddingHorizontal: 12, alignSelf: 'flex-start' },
  captureLabel: { color: COLORS.surface, fontSize: 15, fontWeight: '800', flexShrink: 1 },
  captureOptions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8, marginBottom: 12 },
  optionButton: { flexGrow: 1, flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: 6, minHeight: 48, paddingHorizontal: 8, paddingVertical: 8 },
  optionLabel: { color: COLORS.primaryDark, fontSize: 13, fontWeight: '700' },
  sectionHeading: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 4, marginBottom: 12 },
  sectionTitle: { color: COLORS.textPrimary, fontSize: 18, fontWeight: '800', flexShrink: 1 },
  sectionLink: { flexDirection: 'row', alignItems: 'center', gap: 3, minHeight: 48, paddingHorizontal: 4 },
  sectionLinkText: { color: COLORS.primaryDark, fontSize: 12, fontWeight: '600' },
  quickGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 22 },
  quickCard: { flex: 1, minWidth: 92, borderRadius: 22, paddingHorizontal: 12, paddingTop: 10, paddingBottom: 42 },
  quickCardWide: { flexBasis: '46%' },
  quickArt: { width: '100%', height: 88, marginBottom: 8 },
  quickTitle: { color: COLORS.textPrimary, fontSize: 14, fontWeight: '800', marginBottom: 5 },
  cardArrow: { position: 'absolute', right: 12, bottom: 12, width: 20, height: 20, backgroundColor: COLORS.surface, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  quickDescription: { color: COLORS.textSecondary, fontSize: 12, lineHeight: 17 },
  activityCard: { backgroundColor: COLORS.surface, borderRadius: 24, padding: 18, marginBottom: 20 },
  activityHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  activityCopy: { flex: 1 },
  activityTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 },
  flame: { width: 25, height: 30 },
  streakTitle: { color: COLORS.primaryDark, fontSize: 23, fontWeight: '800' },
  crown: { width: 74, height: 86 },
  activityDescription: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 20, marginTop: 8 },
  week: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 18, gap: 4 },
  weekDay: { flex: 1, alignItems: 'center', gap: 8 },
  dayCircle: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#F0EFF5', justifyContent: 'center', alignItems: 'center' },
  dayCircleDone: { backgroundColor: '#FFF4CA' },
  rewardStar: { width: 25, height: 25 },
  dayLabel: { color: COLORS.textSecondary, fontSize: 11 },
  historyNote: { color: COLORS.textSecondary, fontSize: 11, lineHeight: 16, marginTop: 16 },
  lessonGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 14 },
  lessonCard: { flex: 1, minWidth: 140, backgroundColor: COLORS.primaryLight, padding: 16, borderRadius: 22, gap: 10 },
  arithmeticCard: { backgroundColor: '#E8F6E9' },
  lessonSymbol: { width: 42, height: 42, borderRadius: 21, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' },
  arithmeticSymbol: { backgroundColor: '#258548' },
  lessonTitle: { color: COLORS.textPrimary, fontSize: 16, fontWeight: '800' },
  lessonDetail: { color: COLORS.textSecondary, fontSize: 12, lineHeight: 18 },
  privacyLink: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8, minHeight: 48, paddingHorizontal: 6, paddingVertical: 10 },
  privacyText: { color: COLORS.primaryDark, fontSize: 12, fontWeight: '600', flex: 1 },
});
