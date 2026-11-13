import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';
import type { StudentProfile } from './profileApi';
import { RankEmblem } from './RankEmblem';

export const avatars = [
  { id: 'star', icon: 'star', name: 'Sao nhỏ', color: '#7A4B00', background: '#FFF0BC' },
  { id: 'planet', icon: 'planet', name: 'Hành tinh', color: '#5630A1', background: '#EEE5FF' },
  { id: 'leaf', icon: 'leaf', name: 'Lá xanh', color: '#176A50', background: '#DDF6E9' },
  { id: 'rocket', icon: 'rocket', name: 'Tên lửa', color: '#9E3466', background: '#FFE5F0' },
  { id: 'moon', icon: 'moon', name: 'Mặt trăng', color: '#385C9E', background: '#E1EDFF' },
  { id: 'sun', icon: 'sunny', name: 'Mặt trời', color: '#9C461E', background: '#FFE8D8' },
] as const;

export function StudentAvatar({ id, size = 54, photo }: { id: string; size?: number; photo?: string | null }) {
  if (photo && /^data:image\/(?:jpeg|png);base64,/.test(photo)) return <Image source={{ uri: photo }} style={{ width: size, height: size, borderRadius: size / 2 }} accessible={false} />;
  const avatar = avatars.find(item => item.id === id) ?? avatars[0];
  return <View accessible={false} aria-hidden style={[styles.avatar, { width: size, height: size, backgroundColor: avatar.background }]}>
    <Ionicons name={avatar.icon} size={size * .53} color={avatar.color} />
  </View>;
}

export function ProfileRankCard({ profile }: { profile: StudentProfile }) {
  const { rank, stars, highestRank, position } = profile;
  const next = rank.goal > 0 ? rank.goal - rank.progress : 0;
  const title = profile.titles.find(t => t.id === profile.selectedTitle);
  return <View style={styles.rankCard}>
    <View style={styles.heroRow}>
      <RankEmblem name={rank.name} />
      <View style={styles.grow}>
        <Text style={styles.rankCaption}>HẠNG CỦA EM</Text>
        <Text accessibilityRole="header" style={styles.rank}>{rank.name}</Text>
        {title && <Text style={styles.light}>{title.name}</Text>}
        <Text style={styles.stars}>{stars} sao</Text>
      </View>
    </View>
    {rank.goal > 0 && <>
      <View accessibilityRole="progressbar" accessibilityLabel="Tiến độ lên hạng" accessibilityValue={{ min: 0, max: rank.goal, now: rank.progress }}
        aria-valuemin={0} aria-valuemax={rank.goal} aria-valuenow={rank.progress}
        style={styles.track}><View style={[styles.bar, { width: `${100 * rank.progress / rank.goal}%` }]} /></View>
      <Text style={styles.light}>Còn {next} sao để lên bậc tiếp theo</Text>
    </>}
    <Text style={styles.light}>Hạng cao nhất · {highestRank}</Text>
    {position !== null && <Text style={styles.light}>Vị trí toàn hệ thống · #{position}</Text>}
  </View>;
}

export function ProfileStats({ profile }: { profile: StudentProfile }) {
  const s = profile.stats;
  return <View style={styles.card}>
    <Text accessibilityRole="header" style={styles.heading}>Tiến độ của em</Text>
    <View style={styles.metrics}>{[
      [s.lessons, 'Bài đã hoàn thành'], [s.quizzes, 'Quiz giải đúng'], [s.games, 'Lượt chơi đạt yêu cầu'],
      [s.days, 'Ngày có hoạt động'], [s.week, 'Hoạt động trong 7 ngày'], [s.month, 'Hoạt động trong 30 ngày'],
    ].map(([value, label]) => <View key={label} style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.body}>{label}</Text></View>)}</View>
    <Text style={styles.body}>Học liên tiếp · {s.streak} ngày    Danh hiệu · {profile.titles.filter(t => t.unlocked).length}</Text>
  </View>;
}

export const profileStyles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { width: '100%', maxWidth: 960, alignSelf: 'center', padding: 20, paddingBottom: 112, gap: 16 },
  card: { padding: 18, gap: 12, borderRadius: 22, borderColor: '#E8E0F6', borderWidth: 1, backgroundColor: COLORS.surface },
  row: { flexDirection: 'row', gap: 12, alignItems: 'center', flexWrap: 'wrap' },
  heading: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 19 },
  body: { color: COLORS.textSecondary, fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21 },
  input: { minHeight: 48, padding: 12, color: COLORS.textPrimary, backgroundColor: COLORS.background, borderWidth: 1, borderColor: '#BBAED7', borderRadius: 12, fontFamily: FONTS.bold, fontSize: 16 },
  chip: { minHeight: 48, minWidth: 48, borderRadius: 14, padding: 10, justifyContent: 'center', backgroundColor: '#F2EAFB' },
  selected: { backgroundColor: '#E8D9FC', borderWidth: 2, borderColor: COLORS.primaryDark },
  error: { color: '#8C243D', fontFamily: FONTS.bold, fontSize: 14 },
  logoutButton: { backgroundColor: '#FFF5F5', borderColor: '#F3BDBD', borderWidth: 1 },
  logoutLabel: { color: COLORS.errorText, fontFamily: FONTS.extraBold },
  profileAction: { flexGrow: 1, flexBasis: 122, paddingHorizontal: 12 },
});

const styles = StyleSheet.create({
  ...profileStyles,
  avatar: { alignItems: 'center', justifyContent: 'center', borderRadius: 50 },
  rankCard: { gap: 10, borderRadius: 24, padding: 20, backgroundColor: '#412874' },
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 12, flexWrap: 'wrap' },
  grow: { flex: 1, minWidth: 135, gap: 2 },
  rankCaption: { color: '#E1D4FC', fontFamily: FONTS.extraBold, fontSize: 11, letterSpacing: 1 },
  rank: { color: '#FFF', fontFamily: FONTS.black, fontSize: 25, lineHeight: 33 },
  stars: { color: '#FFE39D', fontFamily: FONTS.black, fontSize: 21 },
  light: { color: '#F1E9FF', fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 20 },
  track: { height: 10, borderRadius: 8, backgroundColor: '#795CA9', overflow: 'hidden' },
  bar: { height: 10, borderRadius: 8, backgroundColor: '#FFD77B' },
  metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  metric: { flexBasis: 115, flexGrow: 1, backgroundColor: '#F5F0FC', borderRadius: 14, padding: 11 },
  metricValue: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold, fontSize: 22 },
});
