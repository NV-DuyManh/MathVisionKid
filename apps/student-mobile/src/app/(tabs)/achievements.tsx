import React, { useCallback, useContext, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { recognitionAnalyticsStore, type RecognitionSession } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildLearningActivity } from '../../features/home/learningActivity';
import { loadLessons, SavedLesson } from '../../features/tutoring/learningHistory';

export default function AchievementsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const auth = useContext(AuthContext);
  const userKey = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  const [sessions, setSessions] = useState<RecognitionSession[]>([]);
  const [unavailable, setUnavailable] = useState(false);
  const [lessons, setLessons] = useState<SavedLesson[]>([]);
  useFocusEffect(useCallback(() => {
    let active = true;
    setSessions([]); setLessons([]); setUnavailable(false);
    Promise.all([recognitionAnalyticsStore.init(), loadLessons(userKey)]).then(([, saved]) => {
      if (active) setLessons(saved);
      if (active) setSessions(recognitionAnalyticsStore.getSessions().filter(session => !session.isSampleData
        && !session.sessionId.startsWith('session_benchmark_') && Number.isFinite(session.timestamp) && session.timestamp <= Date.now()));
    }).catch(() => { if (active) setUnavailable(true); });
    return () => { active = false; };
  }, [userKey]));
  const activity = buildLearningActivity([...sessions, ...lessons.map(item => ({ sessionId: item.id, timestamp: item.timestamp }))]);
  const checked = sessions.reduce((sum, session) => sum + session.confirmedLines, 0) + lessons.reduce((sum, lesson) => sum + lesson.reviewedSteps, 0);
  return <ScrollView style={styles.screen} showsVerticalScrollIndicator={false}
    contentContainerStyle={[styles.content, { paddingTop: insets.top + 22 }]}>
    <Text style={styles.title} accessibilityRole="header">Thành tích của em</Text>
    <Text style={styles.subtitle}>Từng bước nhỏ, tiến bộ mỗi ngày.</Text>
    <LinearGradient colors={['#F1EAFF', '#F9F6FF']} style={styles.hero}>
      <View style={styles.heroCopy}><Text style={styles.heroTitle}>{activity.streak ? `${activity.streak} ngày liên tiếp!` : 'Cùng bắt đầu nhé!'}</Text>
        <Text style={styles.body}>{activity.streak ? 'Em đang giữ một thói quen thật tốt.' : 'Lưu bài đầu tiên để đánh dấu bước tiến của em.'}</Text></View>
      <Image source={require('../../../assets/illustrations/encouragement-crown.png')} style={styles.crown} resizeMode="contain" accessible={false} />
    </LinearGradient>
    <View style={styles.stats}>
      {[{ value: sessions.length + lessons.length, label: 'Bài đã lưu', color: '#FFF0EB', image: require('../../../assets/illustrations/saved-folder.png') },
        { value: checked, label: 'Bước đã xem', color: '#EAF6FF', image: require('../../../assets/illustrations/practice-notebook.png') }].map(stat =>
        <View key={stat.label} style={[styles.stat, { backgroundColor: stat.color }]}>
          <Image source={stat.image} style={styles.statArt} resizeMode="contain" accessible={false} />
          <Text style={styles.statValue}>{stat.value}</Text><Text style={styles.statLabel}>{stat.label}</Text>
        </View>)}
    </View>
    <View style={[styles.weekCard, SHADOWS.small]}>
      <Text style={styles.sectionTitle}>Tuần này của em</Text>
      <View style={styles.week}>{activity.days.map(day => <View key={day.label} style={styles.day} accessible
        accessibilityLabel={`${day.label}: ${day.completed ? 'đã lưu bài' : 'chưa lưu bài'}`}>
        <View style={[styles.circle, day.completed && styles.done]}>{day.completed
          ? <Image source={require('../../../assets/illustrations/reward-star.png')} style={styles.star} resizeMode="contain" accessible={false} />
          : <Ionicons name="star" size={22} color="#C7C4D4" accessible={false} />}</View>
        <Text style={styles.dayLabel}>{day.label}</Text>
      </View>)}</View>
      <Text style={styles.note}>Theo những bài em đã lưu trên thiết bị này.</Text>
    </View>
    <View style={styles.nextCard}>
      <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={styles.mascot} resizeMode="contain" accessible={false} />
      <Text style={styles.nextTitle}>{unavailable ? 'Chưa tải được lịch sử' : sessions.length ? 'Em đã làm rất tốt!' : 'Mỗi bài làm đều đáng tự hào'}</Text>
      <Text style={styles.body}>{unavailable ? 'Em vẫn có thể luyện tập hoặc xem bài đã lưu.' : 'Chọn bài học mới, thử sức và lưu lại hành trình của em nhé.'}</Text>
      <Pressable onPress={() => router.push('/(tabs)/lessons')} accessibilityRole="button" style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
        <Text style={styles.buttonText}>Cùng luyện tập</Text><Ionicons name="arrow-forward" size={18} color={COLORS.surface} accessible={false} />
      </Pressable>
      <Pressable onPress={() => router.push('/(tabs)/profile')} accessibilityRole="button" style={styles.historyButton}><Text style={styles.historyText}>Xem các bài đã lưu</Text></Pressable>
    </View>
  </ScrollView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingHorizontal: 20, paddingBottom: 116, width: '100%', maxWidth: 620, alignSelf: 'center' },
  title: { fontFamily: FONTS.black, fontSize: 29, color: COLORS.textPrimary },
  subtitle: { fontFamily: FONTS.regular, fontSize: 15, color: COLORS.textSecondary, marginTop: 5, marginBottom: 20 },
  hero: { borderRadius: 26, padding: 20, flexDirection: 'row', alignItems: 'center', marginBottom: 18 },
  heroCopy: { flex: 1 },
  heroTitle: { fontFamily: FONTS.extraBold, fontSize: 23, color: COLORS.primaryDark, marginBottom: 8 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 21, color: COLORS.textSecondary },
  crown: { width: '38%', height: 124 },
  stats: { flexDirection: 'row', gap: 12, marginBottom: 20 },
  stat: { flex: 1, alignItems: 'center', borderRadius: 23, paddingVertical: 16, paddingHorizontal: 8 },
  statArt: { width: 64, height: 60 },
  statValue: { fontFamily: FONTS.black, fontSize: 27, color: COLORS.textPrimary, marginTop: 7 },
  statLabel: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.textSecondary, textAlign: 'center' },
  weekCard: { backgroundColor: COLORS.surface, borderRadius: 24, padding: 20, marginBottom: 20 },
  sectionTitle: { fontFamily: FONTS.extraBold, fontSize: 20, color: COLORS.textPrimary },
  week: { flexDirection: 'row', justifyContent: 'space-between', gap: 3, marginTop: 20 },
  day: { flex: 1, alignItems: 'center', gap: 8 },
  circle: { width: 34, height: 34, borderRadius: 17, backgroundColor: '#F2F0F7', alignItems: 'center', justifyContent: 'center' },
  done: { backgroundColor: '#FFF2BF' },
  star: { width: 27, height: 27 },
  dayLabel: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textMuted },
  note: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: COLORS.textMuted, marginTop: 17 },
  nextCard: { alignItems: 'center', backgroundColor: '#EFEBFD', borderRadius: 26, padding: 22, gap: 10 },
  mascot: { width: 115, height: 115 },
  nextTitle: { fontFamily: FONTS.extraBold, fontSize: 21, color: COLORS.textPrimary, textAlign: 'center' },
  button: { flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'center', minHeight: 50, backgroundColor: COLORS.primary, borderRadius: 25, paddingHorizontal: 23, marginTop: 8 },
  buttonText: { fontFamily: FONTS.extraBold, fontSize: 15, color: COLORS.surface },
  historyButton: { minHeight: 48, justifyContent: 'center' },
  historyText: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  pressed: { opacity: 0.7 },
});
