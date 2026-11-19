import React, { useContext, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { AppButton } from '../components/ui/AppButton';
import { RecoveryNotice } from '../components/ui/RecoveryNotice';
import { COLORS, FONTS } from '../constants/theme';
import { STUDENT_WEB } from '../constants/studentWebDesign';
import { PersonalLink, PersonalMetrics, PersonalPageHeader, PersonalPanel, personalWebStyles as web } from '../features/student-profile/PersonalWeb';
import { ProfileRankCard } from '../features/student-profile/ProfileCards';
import { useStudentProfile } from '../features/student-profile/useStudentProfile';
import type { StudentProfile } from '../features/student-profile/profileApi';

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

export default function ProgressPage() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  if (auth?.isLoading) return <ActivityIndicator accessibilityLabel="Đang mở tiến độ" />;
  if (!auth?.isAuthenticated || auth.user?.role !== 'STUDENT' || !owner) return <Redirect href="/login" />;
  return <ProgressContent key={owner} owner={owner} />;
}

function ProgressContent({ owner }: { owner: string }) {
  const router = useRouter();
  const profile = useStudentProfile(owner);
  const [width, setWidth] = useState(0);
  const wide = width >= 850;
  const stats = profile.value?.stats;
  const milestones = profile.value?.titles.filter(title => title.unlocked) ?? [];
  return <ScrollView style={styles.surface} contentContainerStyle={styles.page} onLayout={event => setWidth(event.nativeEvent.layout.width)}>
    <PersonalPageHeader title="Tiến độ học tập" onBack={() => router.replace('/(tabs)/achievements')} backLabel="Về thành tích" />
    <PersonalMetrics metrics={[
      { label: 'Bài đã hoàn thành', amount: stats?.lessons, icon: 'book-outline', tone: 'purple' },
      { label: 'Quiz giải đúng', amount: stats?.quizzes, icon: 'checkmark-circle-outline', tone: 'green' },
      { label: 'Ngày học liên tiếp', amount: stats?.streak, icon: 'flame-outline', tone: 'yellow' },
      { label: 'Sao đã nhận', amount: profile.value?.stars, icon: 'star-outline', tone: 'blue' },
    ]} />
    {profile.value && stats ? <View style={[web.columns, wide && web.wide]}>
      <View style={[web.stack, wide && web.mainGrow]}>
        <ActivityChart history={profile.value.history} />
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
        <PersonalPanel title="Các mốc em đã đạt">
          {milestones.length ? milestones.slice(0, 4).map(milestone => <View key={milestone.id} style={styles.milestone}>
            <Text style={styles.milestoneTitle}>{milestone.name}</Text>
            <Text style={web.body}>{milestone.description}</Text>
          </View>) : <Text style={web.body}>Danh hiệu sẽ xuất hiện khi em hoàn thành các mốc học tập.</Text>}
        </PersonalPanel>
        <ProfileRankCard profile={profile.value} />
        <AppButton title="Xem bảng xếp hạng" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
      </View>
    </View> : !profile.failed && <ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang tải tiến độ" />}
    {profile.failed && <RecoveryNotice title="Chưa tải được tiến độ" message="Em kiểm tra kết nối rồi thử lại nhé."
      actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại tiến độ', icon: 'refresh-outline', onPress: profile.retry }]} />}
  </ScrollView>;
}

const styles = StyleSheet.create({
  surface: { flex: 1, backgroundColor: STUDENT_WEB.background },
  page: { width: '100%', maxWidth: 1440, alignSelf: 'center', gap: 18, paddingHorizontal: 18, paddingTop: 16, paddingBottom: 38 },
  chart: { flexDirection: 'row', gap: 5, alignItems: 'flex-end', backgroundColor: STUDENT_WEB.background, borderRadius: 16, padding: 10 },
  day: { flex: 1, minWidth: 0, alignItems: 'center', gap: 6 },
  barCount: { color: STUDENT_WEB.primary, fontFamily: FONTS.extraBold, fontSize: 14 },
  barArea: { width: '100%', height: 101, justifyContent: 'flex-end', alignItems: 'center' },
  bar: { width: '74%', maxWidth: 36, borderRadius: 7, backgroundColor: '#7043DC' },
  milestone: { gap: 3, borderRadius: 12, padding: 10, backgroundColor: STUDENT_WEB.soft },
  milestoneTitle: { fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 20, color: STUDENT_WEB.ink },
  dayLabel: { color: STUDENT_WEB.muted, fontFamily: FONTS.bold, fontSize: 12, textAlign: 'center' },
});
