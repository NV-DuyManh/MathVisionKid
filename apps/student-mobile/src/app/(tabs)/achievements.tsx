import React, { useCallback, useContext, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { recognitionAnalyticsStore, type RecognitionSession } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildLearningActivity } from '../../features/home/learningActivity';
import { loadLessons, SavedLesson } from '../../features/tutoring/learningHistory';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';

export default function AchievementsScreen() {
  const insets = useSafeAreaInsets(), router = useRouter(), auth = useContext(AuthContext);
  const [pageWidth, setPageWidth] = useState(0);
  const userKey = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  const [sessions, setSessions] = useState<RecognitionSession[]>([]), [unavailable, setUnavailable] = useState(false);
  const [lessons, setLessons] = useState<SavedLesson[]>([]), [details, setDetails] = useState(false);
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
  const total = sessions.length + lessons.length;
  const checked = sessions.reduce((sum, session) => sum + session.confirmedLines, 0) + lessons.reduce((sum, lesson) => sum + lesson.reviewedSteps, 0);
  const wide = pageWidth >= 900;
  return <ScrollView style={styles.screen} onLayout={event => setPageWidth(event.nativeEvent.layout.width)} showsVerticalScrollIndicator={false}
    contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: pageWidth >= 768 ? 32 : 108 }]}>
    <StudentPageHeader compact title="Thành tích" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/(tabs)/profile')} />
    <View style={[styles.columns, wide && styles.columnsWide]}>
      <View style={[styles.celebration, wide && styles.celebrationWide]}>
        <LinearGradient colors={['#FCFAFF', '#F1E7FF', '#FAF7FF']} style={styles.trophyStage}>
          <Image source={require('../../../assets/illustrations/achievement-trophy.png')} style={styles.trophy} resizeMode="contain" accessible={false} />
        </LinearGradient>
        <Text style={styles.heroTitle}>{unavailable ? 'Mình cùng học tiếp nhé!' : total ? 'Tuyệt vời!' : 'Hành trình đang chờ em!'}</Text>
        <Text style={styles.heroCaption}>{total ? 'Em đã ghi lại ' + total + ' bài học.\nCố gắng của em thật đáng tự hào!' : 'Mỗi bài học là một bước tiến.\nCùng Sao Nhỏ bắt đầu nhé!'}</Text>
        <View style={styles.stats}>
          <View style={[styles.stat, styles.green]}><Text style={[styles.statValue, { color: '#24925C' }]}>{total}</Text><Text style={styles.statLabel}>Bài đã lưu</Text></View>
          <View style={[styles.stat, styles.peach]}><View style={styles.streak}><Ionicons name="flame" size={25} color="#EFAB32" /><Text style={[styles.statValue, { color: '#BC7726' }]}>{activity.streak}</Text></View><Text style={styles.statLabel}>Ngày liên tiếp</Text></View>
        </View>
        <View style={styles.journeyCard}><View style={styles.medal}><Ionicons name="ribbon" size={31} color="#B083FF" /></View>
          <View style={styles.copy}><Text style={styles.journeyTitle}>Từng bước em tiến bộ</Text><Text style={styles.small}>{checked} dòng và bước đã xem lại</Text></View></View>
        <Pressable accessibilityRole="button" accessibilityLabel={wide ? 'Xem các bài đã lưu' : details ? 'Thu gọn thành tích của em' : 'Xem thành tích của em'} accessibilityState={wide ? undefined : { expanded: details }}
          onPress={() => wide ? router.push('/(tabs)/profile') : setDetails(value => !value)} style={({ pressed }) => [pressed && styles.pressed]}>
          <LinearGradient colors={['#AD53FF', '#7750FF']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.button}>
            <Text style={styles.buttonText}>{wide ? 'Xem các bài đã lưu' : details ? 'Thu gọn thành tích' : 'Xem thành tích của em'}</Text><Ionicons name={!wide && details ? 'chevron-up' : 'arrow-forward'} size={18} color="#FFF" />
          </LinearGradient>
        </Pressable>
      </View>
      {(details || wide) ? <View style={[styles.detailColumn, wide && styles.detailColumnWide]}>
        <View style={styles.weekCard}><Text style={styles.sectionTitle}>Tuần này của em</Text><Text style={styles.body}>Mỗi ngôi sao là một ngày em lưu bài.</Text>
          <View style={styles.week}>{activity.days.map(day => <View key={day.label} style={styles.day} accessible
            accessibilityLabel={day.label + ': ' + (day.completed ? 'đã lưu bài' : 'chưa lưu bài')}>
            <View style={[styles.circle, day.completed && styles.done]}><Ionicons name="star" size={20} color={day.completed ? '#F6B72E' : '#D6CEEA'} accessible={false} /></View>
            <Text style={styles.dayLabel}>{day.label}</Text>
          </View>)}</View>
          <Text style={styles.small}>{unavailable ? 'Chưa tải đủ lịch sử. Em quay lại để thử nhé.' : 'Theo những bài em đã lưu trên thiết bị này.'}</Text>
        </View>
        <View style={styles.nextCard}><Text style={styles.sectionTitle}>Thêm một bước nhỏ hôm nay</Text><Text style={styles.body}>Chọn bài mới hoặc mở lại bài đã lưu để học tiếp.</Text>
          <Pressable onPress={() => router.push('/(tabs)/lessons')} accessibilityRole="button" style={styles.outlineButton}><Text style={styles.outlineText}>Cùng luyện tập</Text><Ionicons name="arrow-forward" size={19} color={COLORS.primaryDark} /></Pressable>
          <Pressable onPress={() => router.push('/(tabs)/profile')} accessibilityRole="button" style={styles.outlineButton}><Text style={styles.outlineText}>Xem các bài đã lưu</Text><Ionicons name="book-outline" size={19} color={COLORS.primaryDark} /></Pressable>
        </View>
      </View> : null}
    </View>
  </ScrollView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#FAF9FF' },
  content: { flexGrow: 1, paddingHorizontal: 20, width: '100%', maxWidth: 1100, alignSelf: 'center' },
  columns: { gap: 22 }, columnsWide: { flexDirection: 'row', alignItems: 'center', gap: 32 },
  celebration: { gap: 16, backgroundColor: '#FFF', borderRadius: 26, padding: 18, borderWidth: 1, borderColor: '#EFE7FB' }, celebrationWide: { flex: 1.1 },
  trophyStage: { height: 244, borderRadius: 22, marginBottom: -5 }, trophy: { width: '100%', height: '100%' },
  heroTitle: { fontFamily: FONTS.black, fontSize: 26, lineHeight: 34, textAlign: 'center', color: '#4B2C7B' },
  heroCaption: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 22, textAlign: 'center', color: '#89749D', marginTop: -9 },
  stats: { flexDirection: 'row', gap: 10 }, stat: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 14, borderRadius: 16, minHeight: 84 },
  green: { backgroundColor: '#EFF9EF' }, peach: { backgroundColor: '#FFF4E7' }, streak: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  statValue: { fontFamily: FONTS.black, fontSize: 25, lineHeight: 32 }, statLabel: { fontFamily: FONTS.bold, fontSize: 11, lineHeight: 18, color: '#8A7897' },
  journeyCard: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: '#F5EFFF', borderRadius: 16, padding: 13 },
  medal: { width: 44, height: 44, borderRadius: 15, backgroundColor: '#EBDEFF', alignItems: 'center', justifyContent: 'center' }, copy: { flex: 1 },
  journeyTitle: { fontFamily: FONTS.extraBold, fontSize: 15, color: '#6B409E', marginBottom: 2 }, small: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 19, color: '#8B789F' },
  button: { minHeight: 50, borderRadius: 17, paddingHorizontal: 15, flexDirection: 'row', gap: 10, alignItems: 'center', justifyContent: 'center' },
  buttonText: { fontFamily: FONTS.extraBold, fontSize: 14, color: '#FFF' },
  detailColumn: { gap: 18 }, detailColumnWide: { flex: 1, minWidth: 0 },
  weekCard: { backgroundColor: '#FFF', borderRadius: 23, padding: 20, borderWidth: 1, borderColor: '#EDE3F8', gap: 13 },
  sectionTitle: { fontFamily: FONTS.extraBold, fontSize: 19, color: COLORS.textPrimary }, body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: '#796B8F' },
  week: { flexDirection: 'row', justifyContent: 'space-between', gap: 3, marginVertical: 9 }, day: { flex: 1, alignItems: 'center', gap: 7 },
  circle: { width: 29, height: 29, borderRadius: 15, backgroundColor: '#F5F0FC', alignItems: 'center', justifyContent: 'center' }, done: { backgroundColor: '#FFF1C7' },
  dayLabel: { fontFamily: FONTS.bold, fontSize: 11, color: '#8E7AAB' },
  nextCard: { backgroundColor: '#F3EEFC', borderRadius: 23, padding: 20, gap: 16 },
  outlineButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, minHeight: 48, borderRadius: 14, padding: 12, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E2D7F6' },
  outlineText: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark }, pressed: { opacity: .7 },
});
