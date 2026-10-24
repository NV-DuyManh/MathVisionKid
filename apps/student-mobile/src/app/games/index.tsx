import React, { useCallback, useContext, useEffect, useState, useSyncExternalStore } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Redirect, useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { TRAINING_CATALOG } from '../../features/training-games/catalog';
import { trainingAccess } from '../../features/training-games/identity';
import { trainingTrace } from '../../features/training-games/diagnostics';
import { trainingResults } from '../../features/training-games/resultStore';
import type { TrainingSessionResult } from '@mathvisionkid/training-games';

export default function GamesScreen() {
  const auth = useContext(AuthContext);
  const router = useRouter();
  const { width } = useWindowDimensions();
  const access = trainingAccess(auth?.user, !!auth?.isAuthenticated);
  const studentId = access.kind === 'student' ? access.studentId : null;
  useEffect(() => {
    trainingTrace('catalog-access', { mode: access.kind, loading: !!auth?.isLoading, authenticated: !!auth?.isAuthenticated });
  }, [access.kind, auth?.isLoading, auth?.isAuthenticated]);
  const [recent, setRecent] = useState<{ owner: string; rows: Record<string, TrainingSessionResult | undefined>; failed: boolean }>({ owner: '', rows: {}, failed: false });
  const saveError = useSyncExternalStore(trainingResults.subscribe, () => studentId ? trainingResults.error(studentId) : null, () => null);
  useFocusEffect(useCallback(() => {
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

  return <SafeAreaView style={styles.screen} edges={['top', 'left', 'right', 'bottom']}>
    <ScrollView contentContainerStyle={styles.content}>
    <View style={styles.header}>
      <Pressable accessibilityRole="button" accessibilityLabel="Quay lại tab Của em"
        onPress={() => router.dismissTo('/(tabs)/profile')}
        style={({ pressed }) => [styles.back, pressed && styles.pressed]}>
        <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} accessible={false} />
      </Pressable>
      <Text accessibilityRole="header" style={styles.title}>Trò chơi rèn luyện cho em</Text>
      <View style={styles.placeholder} />
    </View>
    <View style={styles.intro}><Text style={styles.eyebrow}>MỖI LƯỢT CHƠI, THÊM MỘT ĐIỀU HAY</Text><Text style={styles.heading}>Chọn chuyến phiêu lưu của em</Text><Text style={styles.copy}>Vừa chơi, vừa luyện toán theo cách em thích.</Text><Text style={styles.local}>{access.kind === 'trial' ? 'Lượt chơi thử không ghi vào thành tích.' : 'Kết quả được lưu riêng trên thiết bị này.'}</Text></View>
    {access.kind === 'blocked' && <Text accessibilityRole="alert" style={styles.notice}>{access.message}</Text>}
    {access.kind === 'trial' && <Text accessibilityRole="alert" style={styles.notice}>Chơi thử không lưu thành tích. Tài khoản dùng thử chưa có hồ sơ học sinh thật; dữ liệu lượt thử chỉ giữ tạm và được bỏ khi thoát trò chơi.</Text>}
    {saveError && <View accessibilityRole="alert" style={styles.noticeBox}><Text style={styles.notice}>{saveError}</Text><Pressable accessibilityRole="button" accessibilityLabel="Thử lưu kết quả" onPress={() => { if (studentId) void trainingResults.retry(studentId).catch(() => {}); }} style={styles.retry}><Text style={styles.playText}>Thử lưu lại</Text></Pressable></View>}
    {recent.owner === studentId && recent.failed && <Text accessibilityRole="alert" style={styles.notice}>Chưa đọc được kết quả gần đây. Dữ liệu cũ vẫn được giữ nguyên.</Text>}
    <View style={styles.grid}>{TRAINING_CATALOG.map(game => {
      const result = recent.owner === studentId ? recent.rows[game.id] : undefined;
      const playable = game.ready && access.kind !== 'blocked';
      return <View key={game.id} testID={`training-card-${game.id}`} style={[styles.card, width >= 720 && styles.wideCard]}>
        <View accessible={false} style={[styles.art, { backgroundColor: game.tint }]}><View style={styles.orbit} /><View style={styles.spark} /><Ionicons name={game.icon} size={68} color={game.color} /><Text style={[styles.artCaption, { color: game.color }]}>CÙNG EM CHINH PHỤC</Text></View>
        <View style={styles.cardBody}><Text style={styles.gameTitle}>{game.title}</Text><Text style={styles.copy}>{game.description}</Text><Text style={styles.math}>{game.math}</Text>
          {game.note && <Text style={styles.note}>{game.note}</Text>}
          {result && <Text testID={`training-recent-${game.id}`} style={styles.recent}>Gần đây: {({ won: 'Hoàn thành', lost: 'Đã thử sức', abandoned: 'Dừng giữa chừng', restarted: 'Chơi lại' } as const)[result.status]}{result.score !== undefined ? ` · ${result.score}${result.maxScore !== undefined ? '/' + result.maxScore : ''} điểm` : ''}</Text>}
          <Pressable accessibilityRole="button" accessibilityLabel={`${access.kind === 'trial' ? 'Chơi thử' : 'Chơi'} ${game.title}`} accessibilityState={{ disabled: !playable }} disabled={!playable} testID={`training-play-${game.id}`} onPress={() => {
            if (!playable) return;
            trainingTrace('play-press', { gameId: game.id, mode: access.kind });
            router.push({ pathname: '/games/[gameId]', params: access.kind === 'trial' ? { gameId: game.id, playMode: 'trial' } : { gameId: game.id } });
          }} style={({ pressed }) => [styles.play, !playable && styles.disabled, pressed && styles.pressed]}><Text style={styles.playText}>{!game.ready ? 'Chưa sẵn sàng' : access.kind === 'blocked' ? 'Đăng nhập để chơi' : access.kind === 'trial' ? 'Chơi thử' : 'Chơi ngay'}</Text><Ionicons name="arrow-forward" size={20} color="#FFFFFF" accessible={false} /></Pressable>
        </View>
      </View>;
    })}</View>
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { flexGrow: 1, width: '100%', maxWidth: 1060, alignSelf: 'center', paddingHorizontal: 16, paddingBottom: 32 },
  intro: { paddingVertical: 22, gap: 10 }, eyebrow: { fontFamily: FONTS.extraBold, color: COLORS.primaryDark, fontSize: 10, letterSpacing: 1.3 },
  heading: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 26, lineHeight: 34 },
  copy: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 14, lineHeight: 22 },
  local: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textMuted }, grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 },
  card: { width: '100%', overflow: 'hidden', borderRadius: 24, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: '#E8E3F4' }, wideCard: { width: '48%' },
  art: { height: 152, alignItems: 'center', justifyContent: 'center', overflow: 'hidden', gap: 9 }, orbit: { position: 'absolute', width: 190, height: 190, borderRadius: 95, borderWidth: 1, borderColor: '#FFFFFF90', transform: [{ rotate: '-20deg' }, { scaleY: .55 }] }, spark: { position: 'absolute', right: 35, top: 25, width: 12, height: 12, backgroundColor: '#FFFFFF', borderRadius: 4, transform: [{ rotate: '20deg' }] }, artCaption: { fontFamily: FONTS.extraBold, fontSize: 9, letterSpacing: 1.7 },
  cardBody: { padding: 20, gap: 10 }, gameTitle: { fontFamily: FONTS.extraBold, fontSize: 21, lineHeight: 28, color: COLORS.textPrimary },
  math: { fontFamily: FONTS.bold, fontSize: 12, lineHeight: 19, color: COLORS.primaryDark }, note: { fontFamily: FONTS.semiBold, fontSize: 11, color: COLORS.textMuted },
  play: { minHeight: 48, marginTop: 8, borderRadius: 16, backgroundColor: COLORS.primary, paddingHorizontal: 18, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }, playText: { fontFamily: FONTS.extraBold, color: '#FFFFFF', fontSize: 15 }, disabled: { opacity: .45 },
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
