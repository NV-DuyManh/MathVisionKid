import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { COLORS, FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { PersonalLink, PersonalMetrics, PersonalPanel, personalWebStyles as web } from './PersonalWeb';
import type { StudentProfile } from './profileApi';

const vietnamDay = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit' });
const shortDay = new Intl.DateTimeFormat('vi-VN', { weekday: 'short', timeZone: 'UTC' });
const fullDay = new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: 'numeric', month: 'numeric', timeZone: 'UTC' });

function recentActivity(history: StudentProfile['history'], now: Date) {
  const date = new Date(vietnamDay.format(now) + 'T00:00:00Z');
  const events = new Map<string, number>();
  for (const row of history) {
    const completedAt = new Date(row.completedAt);
    if (Number.isFinite(completedAt.getTime()) && completedAt <= now) {
      const day = vietnamDay.format(completedAt);
      events.set(day, (events.get(day) ?? 0) + 1);
    }
  }
  return Array.from({ length: 7 }, (_, index) => {
    const day = new Date(date);
    day.setUTCDate(day.getUTCDate() - (6 - index));
    const key = day.toISOString().slice(0, 10);
    return { key, count: events.get(key) ?? 0, title: fullDay.format(day), label: index === 6 ? 'Nay' : shortDay.format(day) };
  });
}

function ActivityChart({ history }: { history: StudentProfile['history'] }) {
  const days = recentActivity(history, new Date());
  const maxCount = Math.max(1, ...days.map(day => day.count));
  return <PersonalPanel title="Hoạt động 7 ngày gần đây">
    <Text style={web.body}>Số lượt trong lịch sử nhận sao gần đây, theo giờ Việt Nam.</Text>
    {days.every(day => day.count === 0) ? <Text style={web.body}>Chưa có lượt nhận sao nào trong 7 ngày qua.</Text> :
      <View style={styles.chart} accessibilityLabel="Biểu đồ hoạt động">
        {days.map(day => <View key={day.key} accessible accessibilityLabel={day.title + ': ' + day.count + ' lượt nhận sao'} style={styles.day}>
          <Text aria-hidden style={styles.barCount}>{day.count}</Text>
          <View style={styles.barArea} aria-hidden>
            <View style={[styles.bar, { height: Math.round(98 * day.count / maxCount) + 3 }]} />
          </View>
          <Text aria-hidden style={styles.dayLabel}>{day.label}</Text>
        </View>)}
      </View>}
  </PersonalPanel>;
}

export function ProfileProgress({ value, failed, retry, wide, hideHeading = false }: {
  value?: StudentProfile; failed?: boolean; retry: () => void; wide: boolean; hideHeading?: boolean;
}) {
  const router = useRouter();
  const stats = value?.stats;
  return <View style={styles.section}>
    {!hideHeading && <Text accessibilityRole="header" aria-level={2} style={web.heading}>Tiến độ học tập</Text>}
    <PersonalMetrics metrics={[
      { label: 'Bài đã hoàn thành', amount: stats?.lessons, icon: 'book-outline', tone: 'purple' },
      { label: 'Quiz giải đúng', amount: stats?.quizzes, icon: 'checkmark-circle-outline', tone: 'green' },
      { label: 'Ngày học liên tiếp', amount: stats?.streak, icon: 'flame-outline', tone: 'yellow' },
      { label: 'Sao đã nhận', amount: value?.stars, icon: 'star-outline', tone: 'blue' },
    ]} />
    {value && stats ? <View style={[web.columns, wide && web.wide]}>
      <View style={[web.stack, wide && web.mainGrow]}>
        <ActivityChart history={value.history} />
        <PersonalPanel title="Kết quả theo hoạt động">
          <PersonalMetrics metrics={[
            { label: 'Lượt chơi đạt yêu cầu', amount: stats.games, icon: 'game-controller-outline', tone: 'purple' },
            { label: 'Ngày có hoạt động', amount: stats.days, icon: 'calendar-outline', tone: 'green' },
            { label: 'Hoạt động trong 30 ngày', amount: stats.month, icon: 'trending-up-outline', tone: 'blue' },
          ]} />
        </PersonalPanel>
      </View>
      <View style={[web.stack, wide && web.sideGrow]}>
        <PersonalPanel title={stats.today > 0 ? 'Tiếp tục học nhé!' : 'Bắt đầu một bài hôm nay'}>
          <PersonalLink label="Mở bài học" icon="book-outline" tone="purple" onPress={() => router.push('/(tabs)/lessons')} />
          <PersonalLink label="Luyện Quiz" icon="flash-outline" tone="yellow" onPress={() => router.push('/quiz')} />
        </PersonalPanel>
      </View>
    </View> : !failed && <ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang tải tiến độ" />}
    {failed && <RecoveryNotice dialog title="Chưa tải được tiến độ" message="Em kiểm tra kết nối rồi thử lại nhé."
      actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại tiến độ', icon: 'refresh-outline', onPress: retry }]} />}
  </View>;
}

const styles = StyleSheet.create({
  section: { gap: 14 },
  chart: { flexDirection: 'row', gap: 5, alignItems: 'flex-end', backgroundColor: STUDENT_WEB.background, borderRadius: 16, padding: 10 },
  day: { flex: 1, minWidth: 0, alignItems: 'center', gap: 6 },
  barCount: { color: STUDENT_WEB.primary, fontFamily: FONTS.extraBold, fontSize: 14 },
  barArea: { width: '100%', height: 101, justifyContent: 'flex-end', alignItems: 'center' },
  bar: { width: '74%', maxWidth: 36, borderRadius: 7, backgroundColor: '#7043DC' },
  dayLabel: { color: STUDENT_WEB.muted, fontFamily: FONTS.bold, fontSize: 12, textAlign: 'center' },
});
