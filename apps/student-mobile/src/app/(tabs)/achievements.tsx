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
import { RankGuide } from '../../features/student-profile/RankGuide';
import { COLORS, FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { PersonalMetrics, PersonalPageHeader } from '../../features/student-profile/PersonalWeb';
import { WEEKLY_ACTIVITY_GOAL } from '../../features/home/learningActivity';

const LEADERBOARD_PAGE_SIZE = 10;

export default function AchievementsScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  const grade = Number(auth?.user?.gradeLevel ?? auth?.user?.grade);
  const registeredGrade = Number.isInteger(grade) && grade >= 1 && grade <= 5 ? grade : undefined;
  return <Achievements key={owner ?? 'signed-out'} owner={owner} registeredGrade={registeredGrade} />;
}

function Achievements({ owner, registeredGrade }: { owner?: string; registeredGrade?: number }) {
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
    if (Platform.OS === 'web') setVisibleEntries(LEADERBOARD_PAGE_SIZE);
    setBoard(undefined);
    void profileApi.leaderboard(undefined, call.signal).then(data => {
      if (!call.signal.aborted) setBoard({ data });
    }).catch(() => {
      if (!call.signal.aborted) setBoard({ error: true });
    });
    return () => call.abort();
    // The retry counter intentionally reloads the focused request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, profile.value?.publicAlias, profile.value?.gradeLevel, profile.value?.leaderboardVisible, retry]));
  const current = board;
  const value = profile.value;
  // The profile is the source of truth for the registered grade. A stale board
  // response must not make the heading show a different grade.
  const expectedGrade = value?.gradeLevel ?? registeredGrade;
  const grade = web ? expectedGrade ?? current?.data?.gradeLevel : current?.data?.gradeLevel ?? value?.gradeLevel;
  const rankingPrivate = web && value?.leaderboardVisible === false;
  const listedEntries = current?.data?.entries.filter(item => !rankingPrivate || !item.self) ?? [];
  const boardMatchesGrade = !web || !expectedGrade || !current?.data?.gradeLevel || expectedGrade === current.data.gradeLevel;
  const ownEntryIndex = listedEntries.findIndex(item => item.self);
  const leaderboard = <View style={[s.card, desktopWeb && styles.webPanel]}>
        <View style={styles.boardHeader}>
          <View style={styles.grow}><Text accessibilityRole="header" style={s.heading}>Bảng xếp hạng{grade ? ` khối ${grade}` : ''}</Text>
            <Text style={s.body}>Cùng các bạn chăm học mỗi ngày</Text></View>
          <Pressable accessibilityRole="button" accessibilityLabel="Xem các bậc xếp hạng" onPress={() => setGuideOpen(true)} style={styles.rankHelp}>
            <Ionicons name="help-circle-outline" size={25} color={COLORS.primaryDark} accessible={false} /></Pressable>
        </View>
        {!boardMatchesGrade ? <RecoveryNotice title="Bảng xếp hạng chưa đúng khối lớp" message="Em tải lại để xem các bạn cùng khối nhé."
          actions={[{ label: 'Tải lại', accessibilityLabel: 'Tải lại bảng xếp hạng đúng khối lớp', icon: 'refresh-outline', onPress: () => setRetry(n => n + 1) }]} />
          : current?.error ? <RecoveryNotice title="Chưa mở được bảng xếp hạng" message="Em kiểm tra kết nối rồi thử lại nhé."
          actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại bảng xếp hạng', icon: 'refresh-outline', onPress: () => setRetry(n => n + 1) }]} />
          : current?.data ? <>
            <View style={styles.ownPosition}><Ionicons name="podium-outline" size={19} color={COLORS.primaryDark} accessible={false} />
              <Text accessibilityLiveRegion="polite" style={styles.positionText}>{!rankingPrivate && current.data.ownPosition
                ? `Vị trí của em · #${current.data.ownPosition}` : rankingPrivate
                  ? 'Em chưa tham gia bảng xếp hạng' : 'Hoàn thành hoạt động để nhận sao nhé'}</Text></View>
            {listedEntries.length === 0 && <Text style={s.body}>{grade ? 'Chưa có bạn nào được xếp hạng trong khối này.' : 'Em cập nhật khối lớp trong hồ sơ để mở bảng xếp hạng nhé.'}</Text>}
            {web && ownEntryIndex >= visibleEntries && <AppButton title="Xem vị trí của em" variant="secondary"
              onPress={() => setVisibleEntries(Math.ceil((ownEntryIndex + 1) / LEADERBOARD_PAGE_SIZE) * LEADERBOARD_PAGE_SIZE)} />}
            {listedEntries.slice(0, visibleEntries).map(item => <View key={item.position} testID="leaderboard-entry" style={[styles.boardRow, web && styles.webBoardRow, item.self && styles.selfRow]}>
              <View accessible={web} accessibilityLabel={`Vị trí ${item.position}`} style={[styles.positionBadge, web && item.position <= 3 && styles.topPosition]}>{web && item.position <= 3 && <Ionicons name={item.position === 1 ? 'trophy-outline' : 'medal-outline'} size={17} color={item.position === 1 ? '#A56200' : '#667085'} accessible={false} />}<Text style={styles.position}>{`#${item.position}`}</Text></View><StudentAvatar id={item.avatar} size={40} />
              <View style={styles.grow}>
                <View style={styles.nameRow}><Text style={styles.alias}>{web && item.self
                  ? value?.leaderboardNameHidden === false ? value.displayName : value?.publicAlias?.trim() || 'Bạn chăm học'
                  : item.alias?.trim() || 'Bạn chăm học'}</Text>{item.self && <Text style={styles.selfBadge}>Em</Text>}</View>
                <View style={styles.rankRow}><RankEmblem name={item.rank.name} size={22} /><Text style={styles.rankName}>{item.rank.name}</Text></View>
              </View>
              <View accessibilityLabel={`${item.stars} sao`} style={styles.stars}><Ionicons name="star" size={14} color="#A56200" accessible={false} /><Text style={styles.starCount}>{web ? item.stars.toLocaleString('vi-VN') : item.stars}</Text></View>
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
  const titleItems = value?.titles.map(title => {
    const icon = <Ionicons name={title.unlocked ? 'ribbon' : 'lock-closed-outline'} size={desktopWeb ? 18 : 25} color="#5B339D" accessible={false} aria-hidden />;
    return <View key={title.id} style={[s.row, s.chip, desktopWeb && styles.webTitle, desktopWeb && title.unlocked && styles.webTitleUnlocked]}>
      {desktopWeb ? <View style={styles.titleIcon}>{icon}</View> : icon}
      <View style={desktopWeb ? styles.titleCopy : { flex: 1, minWidth: 150 }}>
        <Text style={desktopWeb ? styles.titleName : s.heading}>{title.name}</Text>
        <Text style={desktopWeb ? styles.titleMeta : s.body}>{title.rarity} · {title.unlocked ? 'Đã mở khóa' : title.progress + '/' + title.goal}</Text>
        <Text style={desktopWeb ? styles.titleDetail : s.body}>{title.description}</Text>
      </View>
    </View>;
  });
  const titles = value && <View style={[s.card, desktopWeb && styles.webPanel]}>
    <Text accessibilityRole="header" style={s.heading}>Bộ sưu tập danh hiệu</Text>
    {desktopWeb ? (titleItems?.length ? <View style={styles.titleGrid} {...{ dataSet: { studentTitleGrid: 'true' } }}>{titleItems}</View>
      : <Text style={s.body}>Danh hiệu sẽ xuất hiện khi em đạt các mốc học tập.</Text>) : titleItems}
    <AppButton title="Chọn danh hiệu trên hồ sơ" variant="secondary" style={desktopWeb ? styles.titleAction : undefined} onPress={() => router.push('/account')} />
  </View>;
  const history = value && <View style={[s.card, desktopWeb && styles.webPanel]}>
          <Text accessibilityRole="header" style={s.heading}>Những lần em nhận sao</Text>
          {value.history.length === 0 && <Text style={s.body}>Sao sẽ xuất hiện khi em hoàn thành hoạt động đủ điều kiện.</Text>}
          {value.history.map((item, index) => <Text key={item.completedAt + item.source + index} style={s.body}>
            +{item.stars} sao · {{ LESSON: 'Hoàn thành bài học', QUIZ: 'Giải đúng Quiz', GAME: 'Thắng lượt chơi' }[item.source]} · {new Date(item.completedAt).toLocaleDateString('vi-VN')}
          </Text>)}
        </View>;
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
      {wide ? <View style={[styles.mainColumns, styles.wideColumns]}>
        <View style={[styles.mainColumn, styles.rankColumn]}>
          {rank}
          {metrics}
          {titles}
          {tasks}
        </View>
        <View style={[styles.mainColumn, styles.boardColumn]}>
          {leaderboard}
          {history}
        </View>
      </View> : desktopWeb ? <>
        {rank}
        {leaderboard}
        {titles}
        {metrics}
        {tasks}
        {history}
      </> : <>
        {compactWeb ? <>{rank}{compactIdentity}{leaderboard}</> : <View style={styles.mainColumns}>
          <View style={styles.mainColumn}>{rank}</View>
          <View style={styles.mainColumn}>{leaderboard}</View>
        </View>}
        {value && <ProfileStats profile={value} />}
        {tasks}
        {titles}
        {history}
      </>}
      {!value && !profile.failed && <ActivityIndicator accessibilityLabel="Đang tải thành tích" />}
      {profile.failed && <RecoveryNotice title={value ? 'Chưa cập nhật được thành tích' : 'Chưa tải được thành tích'}
        message={value ? 'Em đang xem thành tích đã tải trước đó.' : 'Em kiểm tra kết nối rồi thử lại nhé.'}
        actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại thành tích', icon: 'refresh-outline', onPress: profile.retry }]} />}
    </ScrollView>
    {guideOpen && <RankGuide onClose={() => setGuideOpen(false)} />}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  compactIdentity: { padding: 16, gap: 8, borderRadius: 20, backgroundColor: '#F0E9FF', borderWidth: 1, borderColor: '#DED0FA' },
  identityHeading: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  identityTitle: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  webScreen: { backgroundColor: STUDENT_WEB.background },
  compactContent: { paddingTop: 12 },
  webContent: { maxWidth: '100%', paddingTop: 18, paddingHorizontal: 22, gap: 12 },
  webPanel: { borderColor: STUDENT_WEB.border, borderRadius: STUDENT_WEB.radius, padding: 20 },
  wideContent: { paddingBottom: 38 },
  mainColumns: { gap: 16 }, wideColumns: { flexDirection: 'row', alignItems: 'flex-start', gap: 24 },
  mainColumn: { gap: 16, minWidth: 0 }, rankColumn: { flex: 1.65 }, boardColumn: { flex: 1 },
  titleGrid: { gap: 8 },
  webTitle: { flexWrap: 'nowrap', alignItems: 'flex-start', justifyContent: 'flex-start', gap: 7, padding: 8, borderWidth: 0, minWidth: 0, backgroundColor: '#F5F3FA' },
  titleCopy: { flex: 1, minWidth: 0, gap: 2 },
  webTitleUnlocked: { backgroundColor: '#F1E9FF' },
  titleIcon: { borderRadius: 9, backgroundColor: '#E9DCFF', padding: 5 },
  titleName: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 18 },
  titleMeta: { color: STUDENT_WEB.primary, fontFamily: FONTS.bold, fontSize: 12, lineHeight: 16 },
  titleDetail: { color: STUDENT_WEB.muted, fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 17 },
  titleAction: { alignSelf: 'flex-start', maxWidth: '100%' },
  boardHeader: { flexDirection: 'row', alignItems: 'center', gap: 10 }, grow: { flex: 1, minWidth: 0, gap: 4 },
  rankHelp: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surfaceSubdued },
  ownPosition: { minHeight: 48, borderRadius: 14, padding: 12, backgroundColor: COLORS.primaryLight, flexDirection: 'row', alignItems: 'center', gap: 8 },
  positionText: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  boardRow: { minHeight: 84, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 16, backgroundColor: COLORS.background, borderWidth: 1, borderColor: 'transparent' },
  webBoardRow: { minHeight: 57, paddingVertical: 5, paddingHorizontal: 10, gap: 8, backgroundColor: STUDENT_WEB.background, borderColor: STUDENT_WEB.border },
  positionBadge: { minWidth: 28, alignItems: 'center' }, topPosition: { borderRadius: 12, backgroundColor: '#FFF1CC', minHeight: 36, justifyContent: 'center', gap: 3, paddingHorizontal: 6 },
  selfRow: { borderColor: '#BCA8F6', backgroundColor: '#F2ECFF' }, position: { minWidth: 28, fontFamily: FONTS.extraBold, fontSize: 16, color: COLORS.primaryDark },
  nameRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6 }, alias: { flexShrink: 1, fontFamily: FONTS.bold, fontSize: 15, lineHeight: 22, color: COLORS.textPrimary },
  selfBadge: { fontFamily: FONTS.bold, fontSize: 11, color: COLORS.primaryDark, backgroundColor: '#E2D6FF', paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8 },
  rankRow: { flexDirection: 'row', alignItems: 'center', gap: 5 }, rankName: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary },
  stars: { flexDirection: 'row', alignItems: 'center', gap: 4 }, starCount: { fontFamily: FONTS.extraBold, fontSize: 15, color: '#8C5400' },
});
