import React, { useCallback, useContext, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { isCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
import { Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Redirect, useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { AppButton } from '../../components/ui/AppButton';
import { AuthContext } from '../../context/AuthContext';
import { COLORS, FONTS, IS_STUDENT_WEB, SIZES } from '../../constants/theme';
import { STAR_QUEST, TRAINING_CATALOG } from '../../features/training-games/catalog';
import { GAME_COVERS, GameCover } from '../../features/training-games/GameCover';
import { trainingAccess } from '../../features/training-games/identity';
import { trainingTrace } from '../../features/training-games/diagnostics';
import { trainingResults } from '../../features/training-games/resultStore';
import { enterGameDisplay } from '../../features/training-games/GameDisplay';
import type { TrainingSessionResult } from '@mathvisionkid/training-games';
import { useStudentProfile } from '../../features/student-profile/useStudentProfile';
import { PersonalPanel } from '../../features/student-profile/PersonalWeb';
import { STUDENT_WEB } from '../../constants/studentWebDesign';

const gameFilters = [
  { label: 'Tất cả', ids: [] },
  { label: 'Quãng đường', ids: ['terrain-racing'] },
  { label: 'Phân số', ids: ['energy-defense', 'planet-rescue'] },
  { label: 'Hình học', ids: ['block-island'] },
  { label: 'Tư duy', ids: ['race-to-finish'] },
] as const;

export default function GamesScreen() {
  const auth = useContext(AuthContext);
  const router = useRouter();
  const opening = useRef(false);
  const { width } = useWindowDimensions();
  const desktopWeb = IS_STUDENT_WEB && !isCompactStudentWeb(width);
  const access = trainingAccess(auth?.user, !!auth?.isAuthenticated);
  const studentId = access.kind === 'student' ? access.studentId : null;
  const webProfile = useStudentProfile(desktopWeb ? studentId ?? undefined : undefined);
  const [filter, setFilter] = useState<number>(0);
  const [pageWidth, setPageWidth] = useState(0);
  const desktop = desktopWeb && pageWidth >= 950;
  const pageGames = TRAINING_CATALOG.filter(game => !desktopWeb || !filter || gameFilters[filter].ids.some(id => id === game.id));
  const Layout = desktopWeb ? View : React.Fragment;
  useEffect(() => {
    trainingTrace('catalog-access', { mode: access.kind, loading: !!auth?.isLoading, authenticated: !!auth?.isAuthenticated });
  }, [access.kind, auth?.isLoading, auth?.isAuthenticated]);
  const [recent, setRecent] = useState<{ owner: string; rows: Record<string, TrainingSessionResult | undefined>; failed: boolean }>({ owner: '', rows: {}, failed: false });
  const saveError = useSyncExternalStore(trainingResults.subscribe, () => studentId ? trainingResults.error(studentId) : null, () => null);
  useFocusEffect(useCallback(() => {
    opening.current = false;
    if (!studentId) return;
    let active = true;
    const read = async () => {
      try {
        const rows = await Promise.all(TRAINING_CATALOG.map(async game => [game.id, (await trainingResults.history(studentId, game.id))[0]] as const));
        if (active) setRecent({ owner: studentId, rows: Object.fromEntries(rows), failed: false });
      } catch { if (active) setRecent({ owner: studentId, rows: {}, failed: true }); }
    };
    void read(); const unsubscribe = trainingResults.subscribe(() => { void read(); });
    return () => { active = false; unsubscribe(); };
  }, [studentId]));

  if (auth?.isLoading) return null;
  if (!auth?.isAuthenticated) return <Redirect href="/login" />;

  return <SafeAreaView style={styles.screen} edges={['top', 'left', 'right', 'bottom']}
    onLayout={desktopWeb ? event => setPageWidth(event.nativeEvent.layout.width) : undefined}>
    <ScrollView contentContainerStyle={[styles.content, desktopWeb && styles.webContent]}>
    <View style={[styles.header, desktopWeb && styles.webHeader]}>
      {!desktopWeb && <Pressable accessibilityRole="button" accessibilityLabel="Quay lại tab Của em"
        onPress={() => router.dismissTo('/(tabs)/profile')}
        style={({ pressed }) => [styles.back, pressed && styles.pressed]}>
        <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} accessible={false} />
      </Pressable>}
      {desktopWeb ? <View style={styles.webHeadingCopy}>
        <Text accessibilityRole="header" style={[styles.title, styles.webTitle]}>Khu trò chơi toán học</Text>
        <Text style={styles.copy}>Chọn một trò để luyện tính nhẩm, phân số và tư duy toán học.</Text>
      </View> : <><Text accessibilityRole="header" style={styles.title}>Khu trò chơi</Text><View style={styles.placeholder} /></>}
    </View>
    {access.kind === 'blocked' && <Text accessibilityRole="alert" style={styles.notice}>{access.message}</Text>}
    {access.kind === 'trial' && <Text accessibilityRole="alert" style={styles.notice}>Chơi thử không lưu thành tích. Tài khoản dùng thử chưa có hồ sơ học sinh thật; dữ liệu lượt thử chỉ giữ tạm và được bỏ khi thoát trò chơi.</Text>}
    {saveError && <View accessibilityRole="alert" style={styles.noticeBox}><Text style={styles.notice}>{saveError}</Text><Pressable accessibilityRole="button" accessibilityLabel="Thử lưu kết quả" onPress={() => { if (studentId) void trainingResults.retry(studentId).catch(() => {}); }} style={styles.retry}><Text style={styles.playText}>Thử lưu lại</Text></Pressable></View>}
    {recent.owner === studentId && recent.failed && <Text accessibilityRole="alert" style={styles.notice}>Chưa đọc được kết quả gần đây. Dữ liệu cũ vẫn được giữ nguyên.</Text>}
    <Layout {...(desktopWeb ? { style: [styles.webLayout, desktop && styles.webColumns] } : {})}>
    <Layout {...(desktopWeb ? { style: styles.webMain } : {})}>
    {access.kind === 'student' && <Pressable testID="game-star-quest" accessibilityRole="button"
      accessibilityLabel={STAR_QUEST.title} accessibilityHint={STAR_QUEST.description}
      onPress={() => { if (opening.current) return; opening.current = true; router.push('/games/arithmetic-quest'); }}
      style={({ pressed }) => [styles.card, desktopWeb && styles.featured, pressed && styles.pressed]}>
      {desktopWeb ? <>
        <Image source={GAME_COVERS['star-quest']} style={StyleSheet.absoluteFill} contentFit="cover" contentPosition={{ left: '50%', top: '30%' }} accessible={false} />
        <LinearGradient colors={['#251365F5', '#35156DBB', '#28145609']} locations={[0, .41, .9]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} />
        <View style={styles.featuredCopy}>
          <Text style={styles.featuredLabel}>★ Trò chơi nổi bật</Text>
          <Text accessibilityRole="header" style={styles.featuredTitle}>{STAR_QUEST.title}</Text>
          <Text style={styles.featuredDescription}>{STAR_QUEST.description}</Text>
          <View style={styles.featuredCta}><Ionicons name="play" size={16} color="#24104C" accessible={false} /><Text style={styles.featuredAction}>Chơi ngay</Text></View>
        </View>
      </> : <>
        <GameCover id="star-quest" title={STAR_QUEST.title} />
        <View style={styles.cardBody}><Text style={styles.copy}>{STAR_QUEST.description}</Text></View>
      </>}
    </Pressable>}
    {desktopWeb && <View style={styles.skillSection}>
      <Text accessibilityRole="header" style={styles.heading}>Chọn trò chơi theo kỹ năng</Text>
      <View style={styles.filters}>{gameFilters.map((item, index) => <Pressable key={item.label} accessibilityRole="button"
        aria-pressed={index === filter} onPress={() => setFilter(index)}
        style={[styles.filter, index === filter && styles.selectedFilter]}>
        <Text style={[styles.filterLabel, index === filter && styles.selectedFilterLabel]}>{item.label}</Text>
      </Pressable>)}</View>
    </View>}
    <View style={styles.section}>
      <Text accessibilityRole="header" style={styles.heading}>Chọn trò luyện toán</Text>
      {access.kind === 'student' && <Text style={styles.copy}>Kết quả chơi thông thường lưu trên thiết bị. Các thử thách tính sao ghi kết quả vào hồ sơ.</Text>}
    </View>
    <View style={styles.grid} {...(desktopWeb ? { dataSet: { studentGameGrid: 'true' } } : {})}>{pageGames.map(game => {
      const result = recent.owner === studentId ? recent.rows[game.id] : undefined;
      const playable = game.ready && access.kind !== 'blocked';
      return <View key={game.id} testID={`training-card-${game.id}`} style={[styles.card, !desktopWeb && width >= 720 && styles.wideCard]}>
        <Pressable accessibilityRole="button" accessibilityLabel={`${access.kind === 'trial' ? 'Chơi thử' : 'Chơi'} ${game.title}`}
          accessibilityState={{ disabled: !playable }} disabled={!playable} testID={`training-play-${game.id}`} onPress={() => {
            if (!playable || opening.current) return;
            opening.current = true;
            trainingTrace('play-press', { gameId: game.id, mode: access.kind });
            enterGameDisplay(game.id);
            router.push({ pathname: '/games/[gameId]', params: access.kind === 'trial' ? { gameId: game.id, playMode: 'trial' } : { gameId: game.id } });
          }} style={({ pressed }) => [styles.playTarget, !playable && styles.disabled, pressed && styles.pressed]}>
          <GameCover id={game.id} title={game.title} />
        <View style={[styles.cardBody, desktopWeb && styles.webGameBody]}>
          <Text style={styles.copy}>{game.description}</Text><Text style={styles.math}>{game.math}</Text>
          {game.note && <Text style={styles.note}>{game.note}</Text>}
          {result && <Text testID={`training-recent-${game.id}`} style={styles.recent}>Gần đây: {({ won: 'Hoàn thành', lost: 'Đã thử sức', abandoned: 'Dừng giữa chừng', restarted: 'Chơi lại' } as const)[result.status]}{result.score !== undefined ? ` · ${result.score}${result.maxScore !== undefined ? '/' + result.maxScore : ''} điểm` : ''}</Text>}
          {!playable && <Text style={styles.note}>{!game.ready ? 'Chưa sẵn sàng' : 'Đăng nhập để chơi'}</Text>}
        </View>
        </Pressable>
          {playable && access.kind === 'student' && <>
            <View style={[styles.challenge, desktopWeb && styles.webChallenge]}>
            <AppButton title="Mở thử thách tính sao" accessibilityLabel={`Mở thử thách tính sao · ${game.title}`} variant="secondary"
              onPress={() => { if (opening.current) return; opening.current = true; router.push({ pathname: '/games/arithmetic-quest', params: { mode: game.id } }); }} />
            <Text style={styles.note}>Giải 5 câu để có cơ hội nhận sao vào hồ sơ.</Text>
            </View>
          </>}
      </View>;
    })}</View>
    </Layout>
    {desktopWeb && access.kind === 'student' && <View style={[styles.webAside, desktop && styles.widthAside]}>
      <PersonalPanel title="Phần thưởng đã nhận">
        {webProfile.value ? <>
          <Text style={styles.rewardCount}>{webProfile.value.stats.games} lượt chơi đạt yêu cầu</Text>
          <Text style={styles.copy}>{webProfile.value.stars} sao tích lũy từ các hoạt động học và chơi.</Text>
        </> : <Text style={styles.copy}>{webProfile.failed ? 'Chưa tải được phần thưởng.' : 'Đang tải thành tích…'}</Text>}
      </PersonalPanel>
      <PersonalPanel title="Lượt chơi gần đây">
        {recent.owner === studentId && TRAINING_CATALOG.some(game => recent.rows[game.id])
          ? TRAINING_CATALOG.flatMap(game => {
            const result = recent.rows[game.id];
            return result?.score === undefined ? [] : <Text key={game.id} style={styles.copy}>{game.title} · {result.score} điểm</Text>;
          })
          : <Text style={styles.copy}>Điểm trên thiết bị này sẽ xuất hiện sau khi em chơi.</Text>}
      </PersonalPanel>
    </View>}
    </Layout>
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { flexGrow: 1, width: '100%', maxWidth: 1060, alignSelf: 'center', paddingHorizontal: 16, paddingBottom: 32 },
  webContent: { maxWidth: '100%', paddingHorizontal: 22, paddingTop: 12, paddingBottom: 40 },
  webHeadingCopy: { flex: 1, minWidth: 0, gap: 3 },
  webHeader: { alignSelf: 'stretch', maxWidth: '100%', minHeight: 0, paddingHorizontal: 0, paddingVertical: 7, gap: 12 },
  webTitle: { flex: 0, paddingHorizontal: 0, textAlign: 'left', fontFamily: FONTS.black, fontSize: 29, lineHeight: 35 },
  featured: { overflow: 'hidden', minHeight: 227, padding: 21, justifyContent: 'center' },
  featuredCopy: { maxWidth: 380, gap: 8 },
  featuredLabel: { color: '#291552', backgroundColor: STUDENT_WEB.gold, alignSelf: 'flex-start', paddingVertical: 4, paddingHorizontal: 9, borderRadius: 18, fontFamily: FONTS.extraBold, fontSize: 12 },
  featuredTitle: { color: '#FFFFFF', fontFamily: FONTS.black, fontSize: 35, lineHeight: 44 },
  featuredDescription: { color: '#F5EEFF', fontFamily: FONTS.semiBold, fontSize: 15, lineHeight: 23 },
  featuredCta: { minHeight: 45, paddingHorizontal: 20, marginTop: 7, borderRadius: 14, backgroundColor: '#FFDF57', alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 8 },
  featuredAction: { color: '#24104C', fontFamily: FONTS.extraBold, fontSize: 15 },
  section: { paddingVertical: 16, gap: 4 },
  heading: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 20, lineHeight: 28 },
  copy: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 14, lineHeight: 22 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 },
  card: { width: '100%', borderRadius: 24, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: '#E8E3F4' },
  wideCard: { flexBasis: '48%', flexGrow: 1, maxWidth: '50%' },
  webLayout: { gap: 18 },
  webColumns: { flexDirection: 'row', alignItems: 'flex-start' },
  webMain: { flex: 1, minWidth: 0 },
  webAside: { gap: 13, minWidth: 0 },
  widthAside: { width: 292, flexShrink: 0 },
  skillSection: { gap: 7, paddingTop: 15 },
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  filter: { minHeight: 44, justifyContent: 'center', borderRadius: 13, paddingHorizontal: 13, backgroundColor: STUDENT_WEB.soft },
  selectedFilter: { backgroundColor: STUDENT_WEB.primary },
  filterLabel: { color: STUDENT_WEB.primary, fontFamily: FONTS.bold, fontSize: 13 },
  selectedFilterLabel: { color: '#FFFFFF' },
  rewardCount: { color: STUDENT_WEB.primary, fontFamily: FONTS.extraBold, fontSize: 19 },
  playTarget: { minHeight: 48 },
  cardBody: { padding: 16, gap: 8 }, challenge: { paddingHorizontal: 16, paddingBottom: 16, gap: 8 },
  webGameBody: { padding: 13, gap: 6 }, webChallenge: { paddingHorizontal: 13, paddingBottom: 12, gap: 6 },
  math: { fontFamily: FONTS.bold, fontSize: 12, lineHeight: 19, color: COLORS.primaryDark }, note: { fontFamily: FONTS.semiBold, fontSize: 11, color: COLORS.textMuted },
  playText: { fontFamily: FONTS.extraBold, color: '#FFFFFF', fontSize: 15 }, disabled: { opacity: .45 },
  recent: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textSecondary }, notice: { fontFamily: FONTS.semiBold, color: '#7C4315', fontSize: 13, lineHeight: 21, paddingVertical: 8 }, noticeBox: { backgroundColor: COLORS.warningLight, padding: 12, borderRadius: 14, marginBottom: 16 }, retry: { minHeight: 48, alignItems: 'center', justifyContent: 'center', padding: 12, borderRadius: 14, backgroundColor: COLORS.primary },
  header: {
    minHeight: 64, flexDirection: 'row', alignItems: 'center', paddingHorizontal: SIZES.medium,
    paddingVertical: SIZES.base, width: '100%', maxWidth: 620, alignSelf: 'center',
  },
  back: {
    width: SIZES.minTouchTarget, height: SIZES.minTouchTarget, borderRadius: SIZES.minTouchTarget / 2,
    justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.primaryLight,
  },
  title: {
    flex: 1, minWidth: 0, paddingHorizontal: SIZES.small, fontFamily: FONTS.extraBold,
    fontSize: 20, lineHeight: 28, textAlign: 'center', color: COLORS.textPrimary,
  },
  placeholder: { width: SIZES.minTouchTarget },
  pressed: { opacity: .7 },
});
