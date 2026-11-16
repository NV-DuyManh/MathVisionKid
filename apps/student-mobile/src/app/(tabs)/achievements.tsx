import React, { useCallback, useContext, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { ProfileRankCard, ProfileStats, profileStyles as s, StudentAvatar } from '../../features/student-profile/ProfileCards';
import { profileApi, type Leaderboard } from '../../features/student-profile/profileApi';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';
import { RankEmblem } from '../../features/student-profile/RankEmblem';
import { RankGuide } from '../../features/student-profile/RankGuide';
import { COLORS, FONTS } from '../../constants/theme';

const LEADERBOARD_PAGE_SIZE = 10;

export default function AchievementsScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  return <Achievements key={owner ?? 'signed-out'} owner={owner} />;
}

function Achievements({ owner }: { owner?: string }) {
  const router = useRouter();
  const profile = useStudentProfile(owner);
  const [retry, setRetry] = useState(0);
  const [visibleEntries, setVisibleEntries] = useState(LEADERBOARD_PAGE_SIZE);
  const [guideOpen, setGuideOpen] = useState(false);
  const [board, setBoard] = useState<{ data?: Leaderboard; error?: boolean }>();
  useFocusEffect(useCallback(() => {
    if (!owner) return;
    const call = new AbortController();
    setBoard(undefined);
    void profileApi.leaderboard(undefined, call.signal).then(data => {
      if (!call.signal.aborted) setBoard({ data });
    }).catch(() => {
      if (!call.signal.aborted) setBoard({ error: true });
    });
    return () => call.abort();
    // The retry counter intentionally reloads the focused request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, profile.value?.publicAlias, profile.value?.gradeLevel, retry]));
  const current = board;
  const value = profile.value;
  const grade = current?.data?.gradeLevel ?? value?.gradeLevel;
  return <SafeAreaView style={s.screen} edges={['top']}>
    <ScrollView contentContainerStyle={s.content}>
      <StudentPageHeader compact title="Thành tích" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/account')} />
      {value && <ProfileRankCard profile={value} />}
      <View style={s.card}>
        <View style={styles.boardHeader}>
          <View style={styles.grow}><Text accessibilityRole="header" style={s.heading}>Bảng xếp hạng{grade ? ` khối ${grade}` : ''}</Text>
            <Text style={s.body}>Cùng các bạn chăm học mỗi ngày</Text></View>
          <Pressable accessibilityRole="button" accessibilityLabel="Xem các bậc xếp hạng" onPress={() => setGuideOpen(true)} style={styles.rankHelp}>
            <Ionicons name="help-circle-outline" size={25} color={COLORS.primaryDark} accessible={false} /></Pressable>
        </View>
        {current?.error ? <RecoveryNotice title="Chưa mở được bảng xếp hạng" message="Em kiểm tra kết nối rồi thử lại nhé."
          actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại bảng xếp hạng', icon: 'refresh-outline', onPress: () => setRetry(n => n + 1) }]} />
          : current?.data ? <>
            <View style={styles.ownPosition}><Ionicons name="podium-outline" size={19} color={COLORS.primaryDark} accessible={false} />
              <Text accessibilityLiveRegion="polite" style={styles.positionText}>{current.data.ownPosition
                ? `Vị trí của em · #${current.data.ownPosition}` : 'Hoàn thành hoạt động để nhận sao nhé'}</Text></View>
            {current.data.entries.length === 0 && <Text style={s.body}>{grade ? 'Chưa có bạn nào được xếp hạng trong khối này.' : 'Em cập nhật khối lớp trong hồ sơ để mở bảng xếp hạng nhé.'}</Text>}
            {current.data.entries.slice(0, visibleEntries).map(item => <View key={item.position} testID="leaderboard-entry" style={[styles.boardRow, item.self && styles.selfRow]}>
              <Text style={styles.position}>#{item.position}</Text><StudentAvatar id={item.avatar} size={40} />
              <View style={styles.grow}>
                <View style={styles.nameRow}><Text style={styles.alias}>{item.alias?.trim() || 'Bạn chăm học'}</Text>{item.self && <Text style={styles.selfBadge}>Em</Text>}</View>
                <View style={styles.rankRow}><RankEmblem name={item.rank.name} size={22} /><Text style={styles.rankName}>{item.rank.name}</Text></View>
              </View>
              <View style={styles.stars}><Ionicons name="star" size={14} color="#A56200" accessible={false} /><Text style={styles.starCount}>{item.stars}</Text></View>
            </View>)}
            {current.data.entries.length > visibleEntries && <AppButton title="Xem thêm xếp hạng" variant="secondary"
              onPress={() => setVisibleEntries(count => count + LEADERBOARD_PAGE_SIZE)} />}
            {visibleEntries > LEADERBOARD_PAGE_SIZE && <AppButton title="Thu gọn bảng xếp hạng" variant="ghost"
              onPress={() => setVisibleEntries(LEADERBOARD_PAGE_SIZE)} />}
          </> : <ActivityIndicator accessibilityLabel="Đang tải bảng xếp hạng" />}
      </View>
      {value ? <>
        <ProfileStats profile={value} />
        <View style={s.card}>
          <Text accessibilityRole="header" style={s.heading}>Nhiệm vụ của em</Text>
          <Text style={s.body}>Hôm nay · {Math.min(1, value.stats.today)}/1 hoạt động</Text>
          <Text style={s.body}>7 ngày qua · {Math.min(5, value.stats.week)}/5 hoạt động</Text>
          <View style={s.row}>
            <AppButton title="Học một bài" onPress={() => router.push('/(tabs)/lessons')} />
            <AppButton title="Mở Quiz" variant="secondary" onPress={() => router.push('/quiz')} />
            <AppButton title="Chơi luyện toán" variant="secondary" onPress={() => router.push('/games/arithmetic-quest')} />
          </View>
        </View>
        <View style={s.card}>
          <Text accessibilityRole="header" style={s.heading}>Bộ sưu tập danh hiệu</Text>
          {value.titles.map(title => <View key={title.id} style={[s.row, s.chip]}>
            <Ionicons name={title.unlocked ? 'ribbon' : 'lock-closed-outline'} size={25} color="#5B339D" accessible={false} aria-hidden />
            <View style={{ flex: 1, minWidth: 150 }}>
              <Text style={s.heading}>{title.name}</Text>
              <Text style={s.body}>{title.rarity} · {title.unlocked ? 'Đã mở khóa' : `${title.progress}/${title.goal}`}</Text>
              <Text style={s.body}>{title.description}</Text>
            </View>
          </View>)}
          <AppButton title="Chọn danh hiệu trên hồ sơ" variant="secondary" onPress={() => router.push('/account')} />
        </View>
        <View style={s.card}>
          <Text accessibilityRole="header" style={s.heading}>Những lần em nhận sao</Text>
          {value.history.length === 0 && <Text style={s.body}>Sao sẽ xuất hiện khi em hoàn thành hoạt động đủ điều kiện.</Text>}
          {value.history.map((item, index) => <Text key={item.completedAt + item.source + index} style={s.body}>
            +{item.stars} sao · {{ LESSON: 'Hoàn thành bài học', QUIZ: 'Giải đúng Quiz', GAME: 'Thắng lượt chơi' }[item.source]} · {new Date(item.completedAt).toLocaleDateString('vi-VN')}
          </Text>)}
        </View>
      </> : !profile.failed && <ActivityIndicator accessibilityLabel="Đang tải thành tích" />}
      {profile.failed && <RecoveryNotice title={value ? 'Chưa cập nhật được thành tích' : 'Chưa tải được thành tích'}
        message={value ? 'Em đang xem thành tích đã tải trước đó.' : 'Em kiểm tra kết nối rồi thử lại nhé.'}
        actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại thành tích', icon: 'refresh-outline', onPress: profile.retry }]} />}
    </ScrollView>
    {guideOpen && <RankGuide onClose={() => setGuideOpen(false)} />}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  boardHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 }, grow: { flex: 1, minWidth: 0, gap: 4 },
  rankHelp: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surfaceSubdued },
  ownPosition: { minHeight: 48, borderRadius: 14, padding: 12, backgroundColor: COLORS.primaryLight, flexDirection: 'row', alignItems: 'center', gap: 8 },
  positionText: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  boardRow: { minHeight: 84, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 16, backgroundColor: COLORS.background, borderWidth: 1, borderColor: 'transparent' },
  selfRow: { borderColor: '#BCA8F6', backgroundColor: '#F2ECFF' }, position: { minWidth: 28, fontFamily: FONTS.extraBold, fontSize: 16, color: COLORS.primaryDark },
  nameRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6 }, alias: { flexShrink: 1, fontFamily: FONTS.bold, fontSize: 15, lineHeight: 22, color: COLORS.textPrimary },
  selfBadge: { fontFamily: FONTS.bold, fontSize: 11, color: COLORS.primaryDark, backgroundColor: '#E2D6FF', paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8 },
  rankRow: { flexDirection: 'row', alignItems: 'center', gap: 5 }, rankName: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary },
  stars: { flexDirection: 'row', alignItems: 'center', gap: 4 }, starCount: { fontFamily: FONTS.extraBold, fontSize: 15, color: '#8C5400' },
});
