import React, { useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, IS_STUDENT_WEB } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import type { StudentProfile } from './profileApi';
import { RankEmblem } from './RankEmblem';
import { AppIllustration } from '../../components/ui/AppIllustration';

export const avatars = [
  { id: 'star', icon: 'star', name: 'Sao nhỏ', color: '#7A4B00', background: '#FFF0BC' },
  { id: 'planet', icon: 'planet', name: 'Hành tinh', color: '#5630A1', background: '#EEE5FF' },
  { id: 'leaf', icon: 'leaf', name: 'Lá xanh', color: '#176A50', background: '#DDF6E9' },
  { id: 'rocket', icon: 'rocket', name: 'Tên lửa', color: '#9E3466', background: '#FFE5F0' },
  { id: 'moon', icon: 'moon', name: 'Mặt trăng', color: '#385C9E', background: '#E1EDFF' },
  { id: 'sun', icon: 'sunny', name: 'Mặt trời', color: '#9C461E', background: '#FFE8D8' },
] as const;

export function StudentAvatar({ id, size = 54, photo }: { id: string; size?: number; photo?: string | null }) {
  const [failedPhoto, setFailedPhoto] = useState<string>();
  if (photo && photo !== failedPhoto && /^data:image\/(?:jpeg|png);base64,/.test(photo)) return <Image source={{ uri: photo }} style={{ width: size, height: size, borderRadius: size / 2 }}
    onError={() => setFailedPhoto(photo)} accessible={false} />;
  if (IS_STUDENT_WEB && photo && photo !== failedPhoto && /^https:\/\/[a-z0-9.-]+\.googleusercontent\.com\//.test(photo)) {
    return <img src={photo} alt="" referrerPolicy="no-referrer" onError={() => setFailedPhoto(photo)}
      style={{ width: size, height: size, borderRadius: size / 2, objectFit: 'cover' }} />;
  }
  const avatar = avatars.find(item => item.id === id) ?? avatars[0];
  return <View accessible={false} aria-hidden style={[styles.avatar, { width: size, height: size, backgroundColor: avatar.background }]}>
    <Ionicons name={avatar.icon} size={size * .53} color={avatar.color} />
  </View>;
}

export function ProfileRankCard({ profile, compactWeb = false }: { profile: StudentProfile; compactWeb?: boolean }) {
  const { stars, position, rank, highestRank } = profile;
  const topName = rank.scheme === 2 ? "Huyền Thoại" : "Thách Đấu";
  const next = rank.goal > 0 ? rank.goal - rank.progress : 0;
  const progressStars = rank.progress;
  const goalStars = rank.goal;
  const student = IS_STUDENT_WEB && <View style={styles.rankStudent} testID="achievement-rank-student">
    <StudentAvatar id={profile.avatar} photo={profile.avatarPhoto} size={36} />
    <Text style={styles.rankStudentName} numberOfLines={1}>{profile.displayName}</Text>
  </View>;
  const identity = <View style={styles.heroRow}>
    <RankEmblem name={rank.name} size={IS_STUDENT_WEB && !compactWeb ? 94 : undefined} />
    <View style={styles.grow}>
      <Text style={styles.rankCaption}>HẠNG THEO SAO</Text>
      <Text accessibilityRole="header" style={styles.rank}>{rank.name}</Text>
      <Text style={styles.stars}>{stars} sao</Text>
    </View>
  </View>;
  const progress = <>
    {rank.goal > 0 ? <>
      <View accessibilityRole="progressbar" accessibilityLabel="Tiến độ lên hạng" accessibilityValue={{ min: 0, max: goalStars, now: progressStars }}
        aria-valuemin={0} aria-valuemax={goalStars} aria-valuenow={progressStars}
        style={styles.track}><View style={[styles.bar, { width: (100 * progressStars / goalStars) + '%' }]} /></View>
      <Text style={styles.light}><Text style={styles.webRankProgressCount}>{progressStars}/{goalStars} sao trong bậc · </Text>Còn {next} sao để lên bậc tiếp theo</Text>
    </> : <Text style={styles.light}>{rank.name === topName
      ? 'Em đang ở bậc ' + topName + '.'
      : rank.scheme === 2 || rank.scheme === 1 || rank.scheme === undefined
        ? 'Đạt Top 200 toàn hệ thống để lên ' + topName + '.' : 'Xem lộ trình xếp hạng để biết điều kiện tiếp theo.'}</Text>}
    <Text style={styles.light}>Hạng cao nhất · {highestRank}</Text>
    {!IS_STUDENT_WEB && position !== null && <Text style={styles.light}>Vị trí khối {profile.gradeLevel} · #{position}</Text>}
  </>;
  return IS_STUDENT_WEB && !compactWeb ? <LinearGradient colors={['#4A2DAD', '#6944DD', '#8A4FE9']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
    style={[styles.rankCard, styles.webRankCard]}>
    <View style={styles.webRankIdentity}>{student}{identity}</View>
    <View style={styles.webRankProgress}>{progress}</View>
    <AppIllustration source={require('../../../assets/illustrations/web/robot-mascot.webp')} style={styles.webRankMascot} accessible={false} />
  </LinearGradient> : <View style={styles.rankCard}>{student}{identity}{progress}</View>;
}

export function ProfileStats({ profile }: { profile: StudentProfile }) {
  const s = profile.stats;
  return <View style={[styles.card, IS_STUDENT_WEB && styles.webStatsCard]}>
    <Text accessibilityRole="header" style={styles.heading}>Tiến độ của em</Text>
    <View style={styles.metrics}>{[
      [s.lessons, 'Bài đã hoàn thành'], [s.quizzes, 'Quiz giải đúng'], [s.games, 'Lượt chơi đạt yêu cầu'],
      [s.days, 'Ngày có hoạt động'], [s.week, 'Hoạt động trong 7 ngày'], [s.month, 'Hoạt động trong 30 ngày'],
    ].map(([value, label]) => <View key={label} style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.body}>{label}</Text></View>)}</View>
    <Text style={styles.body}>Học liên tiếp · {s.streak} ngày</Text>
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
  chip: { minHeight: 48, minWidth: 48, maxWidth: '100%', borderWidth: 2, borderColor: 'transparent',
    borderRadius: 14, padding: 10, justifyContent: 'center', backgroundColor: '#F2EAFB' },
  selected: { backgroundColor: '#E8D9FC', borderColor: COLORS.primaryDark },
  error: { color: '#8C243D', fontFamily: FONTS.bold, fontSize: 14 },
  logoutButton: { backgroundColor: '#FFF5F5', borderColor: '#F3BDBD', borderWidth: 1 },
  logoutLabel: { color: COLORS.errorText, fontFamily: FONTS.extraBold },
  profileAction: { flexGrow: 1, flexBasis: 122, paddingHorizontal: 12 },
});

const styles = StyleSheet.create({
  ...profileStyles,
  avatar: { alignItems: 'center', justifyContent: 'center', borderRadius: 50 },
  webRankCard: { padding: 20, gap: 11, minHeight: 192, overflow: 'hidden' },
  rankStudent: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 6 },
  rankStudentName: { flex: 1, color: '#FFF', fontFamily: FONTS.extraBold, fontSize: 15 },
  webRankIdentity: { width: '76%', minWidth: 0, zIndex: 1 },
  webRankProgress: { width: '76%', minWidth: 0, gap: 6, zIndex: 1 },
  webRankProgressCount: { fontFamily: FONTS.extraBold, color: STUDENT_WEB.gold },
  webRankMascot: { position: 'absolute', right: 9, top: 11, bottom: 10, width: '28%', opacity: .95 },
  webStatsCard: { borderRadius: STUDENT_WEB.radius, borderColor: STUDENT_WEB.border, padding: 20 },
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
