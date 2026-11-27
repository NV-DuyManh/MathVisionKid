import React, { useCallback, useContext, useState } from 'react';
import { useIsCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
import { ActivityIndicator, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
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
import { StarHistory } from '../../features/student-profile/StarHistory';
import { RankGuide } from '../../features/student-profile/RankGuide';
import { COLORS, FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { PersonalMetrics, PersonalPageHeader } from '../../features/student-profile/PersonalWeb';
import { WEEKLY_ACTIVITY_GOAL } from '../../features/home/learningActivity';

const LEADERBOARD_PAGE_SIZE = 10;
const placeColors = ['#8B4E06', '#465779', '#91451E'];
export default function AchievementsScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  return <Achievements key={owner ?? 'signed-out'} owner={owner} />;
}

function Achievements({ owner }: { owner?: string }) {
  const router = useRouter();
  const [width, setWidth] = useState(0);
  const web = Platform.OS === 'web';
  const compactWeb = useIsCompactStudentWeb();
  const desktopWeb = web && !compactWeb;
  const wide = desktopWeb && width >= 720;
  const profile = useStudentProfile(owner);
  const [retry, setRetry] = useState(0);
  const [visibleEntries, setVisibleEntries] = useState(LEADERBOARD_PAGE_SIZE);
  const [guideOpen, setGuideOpen] = useState(false);
  const [board, setBoard] = useState<{ data?: Leaderboard; error?: boolean }>();
  useFocusEffect(useCallback(() => {
    if (!owner) return;
    const call = new AbortController();
    if (web) setVisibleEntries(LEADERBOARD_PAGE_SIZE);
    setBoard(undefined);
    const loadBoard = web ? profileApi.leaderboard(undefined, call.signal, true) : profileApi.leaderboard(undefined, call.signal);
    void loadBoard.then(data => {
      if (!call.signal.aborted) setBoard({ data });
    }).catch(() => {
      if (!call.signal.aborted) setBoard({ error: true });
    });
    return () => call.abort();
    // The retry counter intentionally reloads the focused request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, web, profile.value?.publicAlias, profile.value?.gradeLevel, profile.value?.leaderboardVisible, profile.value?.leaderboardNameHidden, retry]));
  const current = board;
  const value = profile.value;
  const grade = current?.data?.gradeLevel ?? value?.gradeLevel;
  const rankingPrivate = web && value?.leaderboardVisible === false;
  const listedEntries = current?.data?.entries.filter(item => !rankingPrivate || !item.self) ?? [];
  const avatarSize = web && compactWeb ? 34 : 40;
  const ownEntryIndex = listedEntries.findIndex(item => item.self);
  const leaderboard = <View style={[s.card, web && styles.webPanel]}>
        <View style={styles.boardHeader}>
          {web && <View style={styles.boardIcon}><Ionicons name="trophy-outline" size={23} color="#895500" accessible={false} /></View>}
          <View style={styles.grow}><Text accessibilityRole="header" style={s.heading}>Bảng xếp hạng{!web && grade ? ` khối ${grade}` : ''}</Text>
            <Text style={web ? styles.boardScope : s.body}>{web ? 'Tất cả khối · Theo tổng số sao' : 'Cùng các bạn chăm học mỗi ngày'}</Text></View>
          <Pressable accessibilityRole="button" accessibilityLabel="Xem các bậc xếp hạng" onPress={() => setGuideOpen(true)} style={styles.rankHelp}>
            <Ionicons name="help-circle-outline" size={25} color={COLORS.primaryDark} accessible={false} /></Pressable>
        </View>
        {current?.error || (web && current?.data?.gradeLevel != null) ? <RecoveryNotice title="Chưa mở được bảng xếp hạng" message="Em thử tải lại bảng xếp hạng nhé."
          actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại bảng xếp hạng', icon: 'refresh-outline', onPress: () => setRetry(n => n + 1) }]} />
          : current?.data ? <>
            <View style={[styles.ownPosition, web && styles.webOwnPosition]}><Ionicons name="podium-outline" size={19} color={COLORS.primaryDark} accessible={false} />
              <Text accessibilityLiveRegion="polite" style={styles.positionText}>{!rankingPrivate && current.data.ownPosition
                ? `Vị trí của em · #${current.data.ownPosition}` : rankingPrivate
                  ? 'Em chưa tham gia bảng xếp hạng' : 'Hoàn thành hoạt động để nhận sao nhé'}</Text></View>
            {listedEntries.length === 0 && <Text style={s.body}>{web ? 'Chưa có bạn nào được xếp hạng.' : grade ? 'Chưa có bạn nào được xếp hạng trong khối này.' : 'Em cập nhật khối lớp trong hồ sơ để mở bảng xếp hạng nhé.'}</Text>}
            {web && ownEntryIndex >= visibleEntries && <AppButton title="Xem vị trí của em" variant="secondary"
              onPress={() => setVisibleEntries(Math.ceil((ownEntryIndex + 1) / LEADERBOARD_PAGE_SIZE) * LEADERBOARD_PAGE_SIZE)} />}
            {listedEntries.slice(0, visibleEntries).map(item => <View key={item.position} testID="leaderboard-entry" style={[styles.boardRow, web && styles.webBoardRow, item.self && styles.selfRow]}>
              <View accessible={web} accessibilityLabel={`Vị trí ${item.position}`} style={[styles.positionBadge, web && styles.webPosition, web && placeStyles[item.position - 1]]}>
                <Text style={[styles.position, web && styles.webPositionText, web && { color: placeColors[item.position - 1] ?? COLORS.primaryDark }]}>{`#${item.position}`}</Text>
              </View>
              {web && item.self && !value && !profile.failed
                ? <View style={{ width: avatarSize, height: avatarSize }} />
                : <StudentAvatar id={web && item.self ? value?.avatar ?? item.avatar : item.avatar}
                    photo={web && item.self ? value?.avatarPhoto : undefined} size={avatarSize} />}
              <View style={styles.grow}>
                <View style={styles.nameRow}><Text style={styles.alias}>{web && item.self
                  ? value?.leaderboardNameHidden === false ? value.displayName : value?.publicAlias?.trim() || 'Bạn chăm học'
                  : item.alias?.trim() || 'Bạn chăm học'}</Text>{item.self && <Text style={styles.selfBadge}>Em</Text>}</View>
                <View style={styles.rankRow}><RankEmblem name={item.rank.name} size={22} /><Text style={styles.rankName}>{item.rank.name}</Text></View>
              </View>
              <View accessible={web} accessibilityLabel={`${item.stars} sao`} style={[styles.stars, web && styles.webStars]}><Ionicons name="star" size={14} color="#A56200" accessible={false} /><Text style={styles.starCount}>{web ? item.stars.toLocaleString('vi-VN') : item.stars}</Text></View>
            </View>)}
            {listedEntries.length > visibleEntries && <AppButton title="Xem thêm xếp hạng" variant="secondary"
              onPress={() => setVisibleEntries(count => count + LEADERBOARD_PAGE_SIZE)} />}
            {visibleEntries > LEADERBOARD_PAGE_SIZE && <AppButton title="Thu gọn bảng xếp hạng" variant="ghost"
              onPress={() => setVisibleEntries(LEADERBOARD_PAGE_SIZE)} />}
          </> : <ActivityIndicator accessibilityLabel="Đang tải bảng xếp hạng" />}
      </View>;
  const tasks = value && <View style={[s.card, desktopWeb && styles.webPanel]}>
          <Text accessibilityRole="header" style={s.heading}>Nhiệm vụ của em</Text>
          <Text style={s.body}>Hôm nay · {Math.min(1, value.stats.today)}/1 hoạt động</Text>
          <Text style={s.body}>7 ngày qua · {Math.min(WEEKLY_ACTIVITY_GOAL, value.stats.week)}/{WEEKLY_ACTIVITY_GOAL} hoạt động</Text>
          <View style={s.row}>
            <AppButton title="Học một bài" onPress={() => router.push('/(tabs)/lessons')} />
            <AppButton title="Mở Quiz" variant="secondary" onPress={() => router.push('/quiz')} />
            <AppButton title="Chơi luyện toán" variant="secondary" onPress={() => router.push('/games/arithmetic-quest')} />
          </View>
        </View>;
  const history = value && <StarHistory recent={value.history} style={web ? styles.webPanel : undefined} />;
  const rank = value && <ProfileRankCard profile={value} compactWeb={compactWeb} />;
  const compactIdentity = compactWeb && value && <View style={styles.compactIdentity}>
    <View style={styles.identityHeading}>
      <Ionicons name={rankingPrivate ? 'eye-off-outline' : 'shield-checkmark-outline'} size={20} color={COLORS.primaryDark} accessible={false} />
      <Text accessibilityRole="header" style={styles.identityTitle}>{rankingPrivate ? 'Em đang ẩn khỏi bảng xếp hạng' : value.leaderboardNameHidden !== false ? 'Em đang dùng bí danh' : 'Em đang hiển thị tên'}</Text>
    </View>
    <Text style={s.body}>{rankingPrivate ? 'Thành tích vẫn được lưu trong tài khoản của em.' : value.leaderboardNameHidden !== false
      ? 'Bạn bè nhìn thấy ' + (value.publicAlias?.trim() || 'bí danh động vật của em') + '.' : 'Bạn bè nhìn thấy ' + value.displayName + '.'}</Text>
    <AppButton title="Đổi quyền riêng tư" variant="ghost" onPress={() => router.push({ pathname: '/account', params: { section: 'privacy' } })} />
  </View>;
  const metrics = desktopWeb && value && <PersonalMetrics metrics={[
    { label: 'Bài đã hoàn thành', amount: value.stats.lessons, icon: 'book-outline', tone: 'blue' },
    { label: 'Quiz giải đúng', amount: value.stats.quizzes, icon: 'checkmark-circle-outline', tone: 'green' },
    { label: 'Lượt chơi đạt yêu cầu', amount: value.stats.games, icon: 'game-controller-outline', tone: 'yellow' },
  ]} />;
  return <SafeAreaView style={[s.screen, desktopWeb && styles.webScreen]} edges={['top']} onLayout={web ? event => setWidth(event.nativeEvent.layout.width) : undefined}>
    <ScrollView showsVerticalScrollIndicator={desktopWeb}
      contentContainerStyle={[s.content, desktopWeb ? styles.webContent : styles.compactContent, wide && styles.wideContent]}>
      {desktopWeb ? <PersonalPageHeader title="Thành tích của em" backLabel="Về trang chủ" onBack={() => router.replace('/(tabs)')} />
        : <StudentPageHeader compact title="Thành tích" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/account')} />}
      <AppButton title="Lộ trình rank" variant="secondary" onPress={() => setGuideOpen(true)} />
      {wide ? <View style={[styles.mainColumns, styles.wideColumns]}>
        <View style={[styles.mainColumn, styles.rankColumn]}>
          {rank}
          {metrics}

          {tasks}
        </View>
        <View style={[styles.mainColumn, styles.boardColumn]}>
          {leaderboard}
          {history}
        </View>
      </View> : desktopWeb ? <>
        {rank}
        {leaderboard}

        {metrics}
        {tasks}
        {history}
      </> : <>
        {compactWeb ? <>{rank}{leaderboard}{compactIdentity}</> : <View style={styles.mainColumns}>
          <View style={styles.mainColumn}>{rank}</View>
          <View style={styles.mainColumn}>{leaderboard}</View>
        </View>}
        {value && <ProfileStats profile={value} />}
        {tasks}

        {history}
      </>}
      {!value && !profile.failed && <ActivityIndicator accessibilityLabel="Đang tải thành tích" />}
      {profile.failed && <RecoveryNotice dialog={!value && !guideOpen} title={value ? 'Chưa cập nhật được thành tích' : 'Chưa tải được thành tích'}
        message={value ? 'Em đang xem thành tích đã tải trước đó.' : 'Em kiểm tra kết nối rồi thử lại nhé.'}
        actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại thành tích', icon: 'refresh-outline', onPress: profile.retry }]} />}
    </ScrollView>
    {guideOpen && <RankGuide profile={value} onClose={() => setGuideOpen(false)} />}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  compactIdentity: { padding: 16, gap: 8, borderRadius: 20, backgroundColor: '#F0E9FF', borderWidth: 1, borderColor: '#DED0FA' },
  identityHeading: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  identityTitle: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  webScreen: { backgroundColor: STUDENT_WEB.background },
  compactContent: { paddingTop: 12 },
  webContent: { maxWidth: '100%', paddingTop: 18, paddingHorizontal: 22, gap: 12 },
  webPanel: { borderColor: STUDENT_WEB.border, borderRadius: STUDENT_WEB.radius, padding: 16, gap: 10 },
  wideContent: { paddingBottom: 38 },
  mainColumns: { gap: 16 }, wideColumns: { flexDirection: 'row', alignItems: 'flex-start', gap: 24 },
  mainColumn: { gap: 16, minWidth: 0 }, rankColumn: { flex: 1.65 }, boardColumn: { flex: 1 },
  boardHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 }, grow: { flex: 1, minWidth: 0, gap: 4 },
  boardIcon: { width: 36, height: 36, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFF1CB' },
  boardScope: { color: STUDENT_WEB.muted, fontFamily: FONTS.bold, fontSize: 12, lineHeight: 17 },
  rankHelp: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surfaceSubdued },
  ownPosition: { minHeight: 48, borderRadius: 14, padding: 12, backgroundColor: COLORS.primaryLight, flexDirection: 'row', alignItems: 'center', gap: 8 },
  webOwnPosition: { backgroundColor: '#F1EAFF', borderColor: '#E5D9FC', borderWidth: 1, minHeight: 42, padding: 9 },
  positionText: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  boardRow: { minHeight: 84, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 16, backgroundColor: COLORS.background, borderWidth: 1, borderColor: 'transparent' },
  webBoardRow: { minHeight: 60, paddingVertical: 6, paddingHorizontal: 7, gap: 7, backgroundColor: '#FBF9FF', borderColor: '#ECE4F8' },
  positionBadge: { minWidth: 28, alignItems: 'center' },
  webPosition: { minWidth: 38, minHeight: 38, paddingHorizontal: 3, borderRadius: 10, justifyContent: 'center', backgroundColor: '#F0EAF9' },
  webPositionText: { textAlign: 'center' },
  selfRow: { borderColor: '#BCA8F6', backgroundColor: '#F2ECFF' }, position: { minWidth: 28, fontFamily: FONTS.extraBold, fontSize: 16, color: COLORS.primaryDark },
  nameRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6 }, alias: { flexShrink: 1, fontFamily: FONTS.bold, fontSize: 15, lineHeight: 22, color: COLORS.textPrimary },
  selfBadge: { fontFamily: FONTS.bold, fontSize: 11, color: COLORS.primaryDark, backgroundColor: '#E2D6FF', paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8 },
  rankRow: { flexDirection: 'row', alignItems: 'center', gap: 5 }, rankName: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary },
  stars: { flexDirection: 'row', alignItems: 'center', gap: 4 }, starCount: { fontFamily: FONTS.extraBold, fontSize: 15, color: '#8C5400' },
  webStars: { backgroundColor: '#FFF3D5', borderRadius: 10, paddingHorizontal: 6, paddingVertical: 4 },
  goldPlace: { backgroundColor: '#FFF0C8' },
  silverPlace: { backgroundColor: '#E9EFFA' },
  bronzePlace: { backgroundColor: '#FBE7DA' },
});

const placeStyles = [styles.goldPlace, styles.silverPlace, styles.bronzePlace];
